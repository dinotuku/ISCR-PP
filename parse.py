#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parse SQuAD Dataset (New Method)
"""

import json
import os
import pickle
import re
import string
import sys

# import ipdb
import numpy as np
from sklearn import feature_extraction
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer

name = sys.argv[1]
lower_limit = int(name.split('_')[0])
upper_limit = int(name.split('_')[1])

os.system("rm -rf data/{}".format(name))
os.system("mkdir -p data/{}".format(name))
os.system("mkdir data/{}/doc".format(name))
os.system("mkdir data/{}/query".format(name))

data = json.load(open('data/spoken_train-v1.1.json'))['data']
regex = re.compile("[%s]" % re.escape(string.punctuation))
split_regex = re.compile("[%s]" % re.escape(string.punctuation.replace('.', '')))
split_docs = []
tmp_docs = []

for doc in data:
    paragraphs = doc['paragraphs']
    for paragraph in paragraphs:
        context = paragraph['context'].lower()
        split_context = split_regex.sub('', context)
        split_context = context.replace('. ', '\n')
        context = regex.sub('', context)
        tmp_docs.append(context)
        split_docs.append(split_context)

print(len(tmp_docs), 'docs')

def tokenizer(text):
    return text.split()

vectorizer = CountVectorizer(tokenizer=tokenizer)
transformer = TfidfTransformer()
tfidf = transformer.fit_transform(vectorizer.fit_transform(tmp_docs))
words = vectorizer.get_feature_names()
weights = tfidf.toarray()

# ipdb.set_trace()

tmp_queries = []

for i in range(len(weights)):
    doc_weights = weights[i]
    sort_idx = np.argsort(doc_weights)[::-1]
    tmp_queries.append([])
    for j in range(5):
        tmp_queries[-1].append(words[sort_idx[j]])

tmp_queries_dict = {}

for idx, queries in enumerate(tmp_queries):
    for query in queries:
        if query not in tmp_queries_dict:
            tmp_queries_dict[query] = [[idx], 0]
        else:
            tmp_queries_dict[query][0].append(idx)
            tmp_queries_dict[query][1] += 1

docs = []
queries = []
queries_ans = []
tfidf_array = []

for query, lst in tmp_queries_dict.items():
    idx_list = lst[0]
    count = lst[1]
    if count >= lower_limit and count <= upper_limit:
        queries.append(query)
        for idx in idx_list:
            if split_docs[idx] not in docs:
                docs.append(split_docs[idx])
                tfidf_array.append(weights[idx])
            queries_ans.append((len(queries) - 1, docs.index(split_docs[idx])))

print(len(docs), 'docs')
print(len(queries), 'queries')
print(len(queries_ans), 'pairs')

for idx, doc in enumerate(docs):
    with open("data/{}/doc/T{:05d}".format(name, idx), 'w') as f:
        f.write(doc)

with open("data/{}/query/SQuAD.query".format(name), 'w') as f:
    for query in queries:
        f.write("{}\n".format(query))

with open("data/{}/query/SQuAD.ans".format(name), 'w') as f:
    for query_id, doc_id in queries_ans:
        f.write("{} {}\n".format(query_id, doc_id))

with open("data/{}/words.pkl".format(name), 'wb') as f:
    pickle.dump(words, f, protocol=2)

with open("data/{}/tfidf.pkl".format(name), 'wb') as f:
    pickle.dump(tfidf_array, f, protocol=2)
