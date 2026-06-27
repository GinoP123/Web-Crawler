#!/Users/ginoprasad/miniconda3/envs/torch-gpu/bin/python3
from collections import defaultdict
import glob
dataset_paths = [
    "/Users/ginoprasad/Job_Applications/web_crawler/dataset/v1.5_Broadcom/dataset_revision.txt",
    "/Users/ginoprasad/Job_Applications/web_crawler/dataset/v1.2_ASML/dataset_revision.txt",
    "/Users/ginoprasad/Job_Applications/web_crawler/dataset/v1.3_Stryker/dataset_revision.txt",
    "/Users/ginoprasad/Job_Applications/web_crawler/dataset/v1.5_KLA/dataset.txt"
]
dataset_paths += glob.glob("/Users/ginoprasad/Job_Applications/web_crawler/dataset/*/keystrokes/page_*")

dataset = ''
for dataset_path in dataset_paths:
    with open(dataset_path) as infile:
        dataset += infile.read()

class AhoCorasick():
    def set_failure_links(self, query):
        failure_links = [0,0]
        for char in query[1:]:
            i = len(failure_links) - 1
            failure_link = 0
            while i != 0:
                if query[failure_links[i]] == char:
                    failure_link = failure_links[i]+1
                    break
                else:
                    i = failure_links[i]
            failure_links.append(failure_link)
        self.failure_links = failure_links
    
    def __call__(self, datastream, query):
        aut.set_failure_links(query)
        node_index = 0
        indices = []
        for i, char in enumerate(datastream):
            while node_index and (node_index == len(query) or query[node_index] != char):
                node_index = aut.failure_links[node_index]
            if query[node_index] == char:
                node_index += 1
            if node_index == len(query):
                indices.append(i - len(query) + 1)
        return indices
aut = AhoCorasick()

INTERNAL_INDICES = defaultdict(int)

def predict(input_data, initial_value):
    global INTERNAL_INDICES
    query = '\n'.join(input_data[-1].split('\n')[:3])
    if query in dataset:
        valid_queries = aut(dataset, query)

        INTERNAL_INDICES[query] %= len(valid_queries)
        start_index = valid_queries[INTERNAL_INDICES[query]]
        INTERNAL_INDICES[query] += 1
        
        prediction = dataset[start_index:].split('\n')[12].strip('"')
        if prediction == initial_value:
            return 'ignore'
        elif initial_value is not None and any([x in input_data[1].lower() for x in ['radio', 'check']]) and 'true' in prediction.lower():
            return 'click'
        else:
            return prediction
    return 'ignore'


def test():
	input_data = [None, None, """
^ role description * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
^ work experience job title company location i currently work here from current value is m m y y y y m m y y y yus e right and left arrows to navigate spin buttons to current value is m m y y y y m m y y
^ work experience delete work experience job title company location i currently work here from current value is m m y y y y m m y y y yus e right and left arrows to navigate spin buttons to current value is m m y y y y m
^ work experience work experience delete work experience job title company location i currently work here from current value is m m y y y y m m y y y yus e right and left arrows to navigate spin buttons to current value is m m y y y
^ work experience work experience delete work experience job title company location i currently work here from current value is m m y y y y m m y y y yus e right and left arrows to navigate spin buttons to current value is m m y y y
^ my experience indicates a required field work experience work experience delete work experience job title company location i currently work here from current value is m m y y y y m m y y y yus e right and left arrows to navigate spin buttons to current value
^ video conference services technology ? step of my information current step of my experience application questions voluntary disclosures self identify review my experience indicates a required field work experience work experience delete work experience job title company location i currently work here from current value is m m y
^ skip to main content english sign in home introduce yourself video conference services technology ? step of my information current step of my experience application questions voluntary disclosures self identify review my experience indicates a required field work experience work experience delete work experience job title company location i
^ video conference services technology administrator my experience skip to main content english sign in home introduce yourself video conference services technology ? step of my information current step of my experience application questions voluntary disclosures self identify review my experience indicates a required field work experience work experience delete
^ video conference services technology administrator my experience skip to main content english sign in home introduce yourself video conference services technology ? step of my information current step of my experience application questions voluntary disclosures self identify review my experience indicates a required field work experience work experience delete
""".strip()]

	query = '\n'.join(input_data[2].split('\n')[:3])
	return predict(input_data, None)

