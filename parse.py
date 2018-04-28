#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parse SQuAD Dataset
"""

import json
import os
import re
import string
import sys

import numpy as np

name = sys.argv[1]
lower_limit = int(name.split('_')[0])
upper_limit = int(name.split('_')[1])

os.system("rm -rf data/{}".format(name))
os.system("mkdir -p data/{}".format(name))
os.system("mkdir data/{}/doc".format(name))
os.system("mkdir data/{}/query".format(name))

data = json.load(open('data/spoken_train-v1.1.json'))['data']
regex = re.compile("[%s]" % re.escape(string.punctuation.replace('.', '')))
docs = []
queries = []
queries_ans = []
ignored_queries_idx = [1, 5, 23, 135, 187, 192, 260, 309, 433]

for idx, doc in enumerate(data):
    paragraphs = doc['paragraphs']
    if len(paragraphs) > upper_limit or len(paragraphs) < lower_limit:
        continue
    title = doc['title']
    title = regex.sub(' ', title)
    if idx in ignored_queries_idx:
        continue
    queries.append(title)
    for paragraph in paragraphs:
        context = paragraph['context'].lower()
        context = regex.sub('', context)
        context = context.replace('. ', '\n')
        docs.append(context)
        queries_ans.append((len(queries) - 1, len(docs) - 1))

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
