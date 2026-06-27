from onnxruntime import InferenceSession
import numpy as np
from collections import defaultdict
import numpy as np
import torch
import gensim.downloader
import yaml

profile_path = "Profiles/default.yml"
with open(profile_path) as infile:
    profile = yaml.safe_load(infile)

GLOBALS = {
    'glove_vectors': None,
}

models_folder = "genie/models"
with open(f"{models_folder}/model.onnx", "rb") as f:
    onx = f.read()

labels_path = "genie/models/labels.txt"
with open(labels_path) as infile:
    labels  = []
    for line in infile.read().strip().split('\n'):
        labels.append((line.split(',')[0], eval(line.split(',')[1])))

INTERNAL_INDICES = defaultdict(lambda: -1)

def reset_internal_indices():
    global INTERNAL_INDICES
    INTERNAL_INDICES = defaultdict(lambda: -1)

def get_text_embedding(stack, layers=4, word_limit=20):
    stack = [x.split(' ')[:word_limit] for x in stack.split('\n')][:layers]
    lengths = torch.Tensor([x.index('*') if '*' in x else len(x) for x in stack])
    embedding = torch.Tensor(np.array([[GLOBALS['glove_vectors'].get_vector(x) for x in embedding_i] for embedding_i in stack]))
        
    # https://stackoverflow.com/questions/53403306/how-to-batch-convert-sentence-lengths-to-masks-in-pytorch
    mask = torch.arange(word_limit).expand(len(lengths), word_limit) < lengths.unsqueeze(1)
    return embedding, mask

def predict(input_data, initial_value):
    INTERNAL_INDICES[input_data[-1]] += 1
    src, mask = get_text_embedding(input_data[-1])
    X = src.reshape((1, -1)).numpy()

    sess = InferenceSession(onx, providers=["CPUExecutionProvider"])
    prediction = sess.run(None, {"X": X.astype(np.float32)})[0][0]

    label, max_index = labels[prediction]
    INTERNAL_INDICES[input_data[-1]] %= max_index
    if max_index == 1:
        prediction = profile
        for val in label.split('.'):
            prediction = prediction[val]
    else:
        a, b = label.split('.')
        label = f"{a}[{INTERNAL_INDICES[input_data[-1]]}][{b}]"
        prediction = profile[a][INTERNAL_INDICES[input_data[-1]]][b]

    if prediction == initial_value:
        return ('IGNORE', 'ignore')
    elif input_data[1] in ['checkbox', 'radio'] and prediction != 'ignore':
        return (label, 'click')
    return (label, prediction)

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

    return predict(input_data, None)

