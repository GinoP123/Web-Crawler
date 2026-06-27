import numpy as np
import glob

included_file_paths = ['/Users/ginoprasad/Job_Applications/web_crawler/aladdin/dataset/included_f1_revision.txt']
included_file_paths += glob.glob("/Users/ginoprasad/Job_Applications/web_crawler/dataset/*/keystrokes/page_*")
included = ''
for dataset_path in included_file_paths:
    with open(dataset_path) as infile:
        if 'keystrokes' in dataset_path:
            included += ''.join(infile.readlines()[2::20])
        else:
            included += infile.read()

excluded_file_path = '/Users/ginoprasad/Job_Applications/web_crawler/aladdin/dataset/excluded_f1_revision.txt'
with open(excluded_file_path) as infile:
    excluded = infile.read()
with open("/Users/ginoprasad/Job_Applications/web_crawler/aladdin/dataset/error_list.txt") as infile:
    lines = infile.readlines()
    excluded += ''.join([y for x, y in zip(lines[2::5], lines[3::5]) if x == "<class 'selenium.common.exceptions.ElementNotInteractableException'>\n"])


def get_alignment_local_score(s_list, t, indel_penalty=-1, sub_penalty=-1):
    best_score = float('-inf')
    for s in s_list:
        prev_scores = np.arange(len(s)+1) * indel_penalty
        for j, char_2 in enumerate(t, start=1):
            scores = np.ones(len(s)+1) * (j*indel_penalty)
            for i, char_1 in enumerate(s, start=1):
                score = 1 if (char_1 == char_2) else sub_penalty
                scores[i] = max(score+prev_scores[i-1], 
                                  indel_penalty+prev_scores[i], 
                                  indel_penalty+scores[i-1],
                               0)
            prev_scores = scores
            best_score = max(max(scores), best_score)
    return best_score

class Node():
    def __init__(self, parent=None):
        self.failure_link = None
        self.dictionary_link = None
        self.parent = parent
        self.children = {}
        self.is_word = False
    
    def create_child(self, char):
        assert char not in self.children
        self.children[char] = Node(self)
        return self.children[char]
    
    def set_failure_link(self, ch=''):
        if self.parent is None:
            self.failure_link = self
        elif self.parent.parent is None:
            self.failure_link = self.parent
        else:
            ancestor = self.parent.failure_link
            while ch not in ancestor.children and ancestor.parent is not None:
                ancestor = ancestor.failure_link
            self.failure_link = ancestor(ch) if ch in ancestor.children else ancestor
    
    def set_dictionary_link(self):
        ancestor = self.failure_link
        while not ancestor.is_word and ancestor.parent is not None:
            ancestor = ancestor.failure_link
        self.dictionary_link = ancestor if ancestor.parent is not None else None
    
    def get_word(self):
        if self.parent is None:
            return ''
        return self.parent.get_word() + [x for x, y in self.parent.children.items() if y == self][0]

    def __call__(self, x):
        if x in self.children:
            return self.children[x]
        elif self.parent is None:
            return self
        return self.failure_link(x)

class AhoCorasick():
    def create_trie(self, queries):
        self.root = Node()
        for query in queries:
            curr = self.root
            for char in query:
                curr = curr(char) if char in curr.children else curr.create_child(char)
            curr.is_word = True
            
    def set_failure_links(self, queries):
        self.root.set_failure_link()
        iters = {query: [self.root, iter(query)] for query in queries}
        while iters:
            for key, (curr, it) in list(iters.items()):
                ch = next(it) if it.__length_hint__() else None
                if ch is None:
                    del iters[key]
                    continue
                iters[key][0] = curr(ch)
                iters[key][0].set_failure_link(ch)

    def set_dictionary_links(self, queries):
        for query in queries:
            curr = self.root
            for ch in query:
                curr = curr(ch)
                curr.set_dictionary_link()
    
    def __init__(self, queries):
        self.create_trie(queries)
        self.set_failure_links(queries)
        self.set_dictionary_links(queries)
    
    def __call__(self, database):
        ret = []
        curr = self.root
        for i, ch in enumerate(database):
            curr = curr(ch)
            ancestor = curr
            while ancestor is not None and ancestor.parent is not None:
                if ancestor.is_word:
                    ret.append((i, ancestor.get_word()))
                ancestor = ancestor.dictionary_link
        return ret
    
def get_features(elem):
    features = [f'<{elem.name}'] # tag
    for attribute, value in elem.attrs.items():
        features.append(f'{attribute}="{value}"')
    features.append(elem.text)
    return features

def get_nearest_neighbor(elem, database, certificate_needed=False):
    features = get_features(elem)
    aut = AhoCorasick(features + ['\n'])
    hits = aut(database)
    
    line_num = 0
    matches = set()
    max_hit = (len(matches), line_num)
    for hit in hits:
        if hit[1] == '\n':
            line_num += 1
            matches = set()
        else:
            matches.add(hit[1])
            max_hit = max(max_hit, (len(matches), -line_num))
    if certificate_needed:
        return max_hit[0], database.split('\n')[-max_hit[1]]
    return max_hit[0]

def get_nearest_neighbor_batch(elems, database, certificate_needed=False):
    individual_features = [set([x for x in get_features(elem)]) for elem in elems]
    combined_features = set([x for elem in elems for x in get_features(elem)] + ['\n'])
    
    aut = AhoCorasick(combined_features)
    hits = aut(database)
    
    line_num = curr = 0
    matches = [set() for _ in individual_features]
    max_hits = [(len(matches_), line_num) for matches_ in matches]
    for hit in hits:
        if hit[1] == '\n':
            line_num += 1
            matches = [set() for _ in individual_features]
        else:
            for i, (features, matches_) in enumerate(zip(individual_features, matches)):
                if hit[1] in features:
                    matches_.add(hit[1])
                max_hits[i] = max(max_hits[i], (len(matches_), -line_num))

    max_scores = np.array([max_hit[0] for max_hit in max_hits])
    if certificate_needed:
        split_database = database.split('\n')
        certificates = np.array([split_database[-max_hit[1]] for max_hit in max_hits])
        return max_scores, certificates
    return max_scores

def predict(elem):
    included_score = get_nearest_neighbor(elem, included)
    excluded_score = get_nearest_neighbor(elem, excluded)
    return included_score > excluded_score

def predict_batch(elems):
    included_scores = get_nearest_neighbor_batch(elems, included)
    excluded_scores = get_nearest_neighbor_batch(elems, excluded)
    return included_scores > excluded_scores


