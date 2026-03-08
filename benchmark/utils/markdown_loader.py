import os

def load_corpus(path):
    docs = []
    for f in os.listdir(path):
        if f.endswith(".md"):
            with open(os.path.join(path, f), encoding="utf-8") as file:
                docs.append(file.read())
    return docs
