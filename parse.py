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
low_ap_idx = [6, 7, 8, 11, 20, 23, 27, 37, 43, 43, 44, 45, 48, 49, 49, 52, 134, 141, 142, 144, 158, 160, 164, 166, 170, 170, 183, 187, 189, 192, 195, 197, 206, 210, 220, 225, 229, 236, 245, 258, 258, 270, 276, 276, 279, 280]

for idx, doc in enumerate(data):
    paragraphs = doc['paragraphs']
    if len(paragraphs) > upper_limit or len(paragraphs) < lower_limit:
        continue
    if idx in ignored_queries_idx:
        continue
    if len(queries) in low_ap_idx:
        low_ap_idx.pop(0)
        continue
    title = doc['title']
    title = regex.sub(' ', title)
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
