import pandas as pd
import string
import pickle

X_train = pd.read_csv("/home/sabar/Desktop/nlp_project/data/nlp_proj/data/clean/train_df.csv").values
X_test = pd.read_csv("/home/sabar/Desktop/nlp_project/data/nlp_proj/data/clean/test_df.csv").values

def strip_punctuation(sentence):
    letters = []
    for letter in sentence:
            if letter not in string.punctuation and not letter == '\n':
                letters.append(letter)
    return "".join(letters)

def filter_data(X, lextype, word):
    X = filter(lambda x: x[1] == lextype, X)

    for index in range(len(X)):
        paragraph = X[index][5]
        word = X[index][3]
            
        sentences = []
        for sentence in paragraph.split("."):
            sentence = strip_punctuation(sentence.strip()).lower()
            if len(sentence) and word in sentence:
                sentences.append(sentence)
        if not len(sentences):
            sentences.append("EMPTY_SENTENCE")
        print sentences
        
filter_data(X_test, "promise-v", "promise")
