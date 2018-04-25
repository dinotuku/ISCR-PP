#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parse SQuAD Dataset
"""

import json
import os
import re
import string

os.system('mkdir data/train')
os.system('rm -rf data/train/doc')
os.system('rm -rf data/train/query')
os.system('mkdir data/train/doc')
os.system('mkdir data/train/query')

data = json.load(open('data/spoken_train-v1.1.json'))['data']

docs = []
queries = []
queries_ans = []

doc_count = 0
query_count = 0
id_not_want = [1, 5, 23, 24, 187, 260, 309, 359, 409, 428, 432]

for i, doc in enumerate(data):
    if i in id_not_want:
        continue
    else:
        title = doc['title'].lower().replace('_', ' ')
        paragraphs = doc['paragraphs']
        docs.append([])
        queries.append(title)
        queries_ans.append([])
        for paragraph in paragraphs:
            context = paragraph['context'].lower().replace('. ', '\n')
            if title in context:
                queries_ans[query_count].append(doc_count)
                docs[query_count].append(context)
                doc_count += 1

        if (len(queries_ans[query_count]) < 5):
            doc_count -= len(queries_ans[query_count])
            queries.pop()
            queries_ans.pop()
            docs.pop()
        else:
            query_count += 1

for query_id, doc_id_list in enumerate(queries_ans):
    for idx, doc in enumerate(docs[query_id]):
        with open("data/train/doc/T{}".format(doc_id_list[idx]), 'w') as f:
            f.write(doc)

with open('data/train/query/SQuAD.query', 'w') as f:
    for query in queries:
        f.write("{}\n".format(query))

with open('data/train/query/SQuAD.ans', 'w') as f:
    for query_id, doc_id_list in enumerate(queries_ans):
        for doc_id in doc_id_list:
            f.write("{} {}\n".format(query_id, doc_id))
