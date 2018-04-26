#!/usr/bin/env python
# -*- coding: utf-8 -*-c

import codecs
from collections import defaultdict
from glob import glob
import math
import operator
import os
import pickle
import re
import sys

import ipdb
import numpy as np
from sklearn import feature_extraction
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from tqdm import tqdm

from util import readInvIndex, readCleanInvIndex, readDocLength, readDocModel
from util import docNameToIndex


def run_transcript2docmodel(query_utf8_file, transcript_dir, lex_file,
                            lm_dir, docmodels_cache, save_docmodel_dir, background_file, doclength_file, index_file):
    """
      1. Build lex file
      2. Create language models
    """
    if not os.path.exists(lm_dir):
        print("Creating dir at {}".format(lm_dir))
        os.makedirs(lm_dir)
    #######################
    #    Build Lex Dict   #
    #######################
    if not os.path.exists(lex_file):
        print("Building lex dictionary...")
        lex_dict = {}
        lex_idx = 1
        print("Reading query {}".format(query_utf8_file))
        with open(query_utf8_file) as f:
            for line in tqdm(f.readlines()):
                query_string = line.strip()
                query_phrases = query_string.split()

                for ph in query_phrases:
                    lex_key = utf8_to_brackethex(ph)
                    if lex_key not in lex_dict:
                        lex_dict[lex_key] = lex_idx
                        lex_idx += 1

        print("Reading documents from {}".format(transcript_dir))
        for docname in tqdm(sorted(os.listdir(transcript_dir))):
            # Language model dictionary, store for inverted index and doclength
            doc_path = os.path.join(transcript_dir, docname)
            # Read transcription
            with open(doc_path, 'r') as f:
                text = f.read()
                uni_text = text
                cut_uni_text = uni_text.split()

                for ph in cut_uni_text:
                    lex_key = utf8_to_brackethex(ph)
                    if lex_key not in lex_dict:
                        lex_dict[lex_key] = lex_idx
                        lex_idx += 1

        with open(lex_file, 'w') as f:
            for lex_key in lex_dict.keys():
                f.write("{}\n".format(lex_key))

        print("lex built")
    else:
        print("lex file already exists at {}".format(lex_file))
        lex_dict = {}
        with open(lex_file, 'r') as fin:
            for idx, line in enumerate(fin.readlines(), 1):
                lex = line.strip()
                lex_dict[lex] = idx

    #######################
    #        TFIDF        #
    #######################
    with open("data/{}/words.pkl".format(sys.argv[1]), 'rb') as f:
        words = pickle.load(f)
    with open("data/{}/tfidf.pkl".format(sys.argv[1]), 'rb') as f:
        tfidf = pickle.load(f)

    inv_words = {}
    for idx, word in enumerate(words):
        inv_words[word] = idx

    #######################
    #   Language Models   #
    #######################
    # All doc lengths in one file
    if not os.path.exists(docmodels_cache):
        print("Reading docmodels from {} and saving cache to {}".format(transcript_dir, docmodels_cache))
        docmodels = {}
        doclength_dict = {}

        for docname in tqdm(sorted(os.listdir(transcript_dir))):
            # Language model dictionary, store for inverted index and doclength
            doc_index = docNameToIndex(docname)
            docmodels[docname] = defaultdict(float)
            doc_path = os.path.join(transcript_dir, docname)

            # Read transcription
            with open(doc_path, 'r') as f:
                text = f.read()
                uni_text = text
                cut_uni_text = uni_text.split()

                doclength_dict[docname] = len(cut_uni_text)

                # Unicode to bracket big5 hex
                for word in cut_uni_text:
                    # To big5 hex
                    bracketed_chars = utf8_to_brackethex(word)

                    if bracketed_chars in lex_dict:
                        lex_index = lex_dict[bracketed_chars]
                        # docmodels[docname][lex_index] += 1.
                        docmodels[docname][lex_index] = tfidf[doc_index][inv_words[word]]

                # Normalize docmodel
                # factor = 1. / sum(docmodels[docname].values())
                # for k in docmodels[docname].keys():
                #     docmodels[docname][k] *= factor

        with open(docmodels_cache, 'wb') as f:
            obj = (docmodels, doclength_dict)
            pickle.dump(obj, f, protocol=2)

    else:
        print("Loading docmodel cache from {}".format(docmodels_cache))
        with open(docmodels_cache, 'rb') as f:
            docmodels, doclength_dict = pickle.load(f)

    # Read from transcript dir, save to docmodel dir
    if not os.path.exists(save_docmodel_dir):
        print("Creating dir at {}".format(save_docmodel_dir))
        os.makedirs(save_docmodel_dir)

        # Write document models
        print("Writing document models to {}".format(save_docmodel_dir))
        for docname in tqdm(os.listdir(transcript_dir)):
            if docname in docmodels.keys():
                save_docname = os.path.join(save_docmodel_dir, docname)
                with open("{}".format(save_docname), 'w') as fout:
                    for k, v in docmodels[docname].items():
                        fout.write('{} {}\n'.format(k, v))
    else:
        print("Document models have already been written to {}".format(save_docmodel_dir))

    sorted_docmodel_keys = sorted(docmodels.keys())
    ipdb.set_trace()

    # Write background file
    if not os.path.exists(background_file):
        print("Writing background file to {}".format(background_file))
        with open(background_file, 'w') as f:
            ndocuments = len(docmodels)
            for lex_key, lex_idx in tqdm(lex_dict.items()):
                prob = 0.
                for docname, model in docmodels.items():
                    prob += model.get(lex_idx, 0.)
                prob /= ndocuments
                f.write('{} {}\n'.format(lex_key, prob))
    else:
        print("Background file already exists at {}".format(background_file))

    # Write doclength file
    if not os.path.exists(doclength_file):
        print("Writing doclength file to {}".format(doclength_file))
        with open(doclength_file, 'w') as fout:
            for k in tqdm(sorted(doclength_dict.keys())):
                fout.write("{} {}\n".format(k, doclength_dict[k]))
    else:
        print("Doclength file already exists at {}".format(doclength_file))

    # Write inverted index
    if not os.path.exists(index_file):
        print("Writing inverted index to {}".format(index_file))
        with open(index_file, 'w') as fout:
            for word_index in tqdm(range(1, len(lex_dict) + 1, 1)):
                inv_index_string = ""
                # Loop through all the documents
                sorted_docmodel_keys = sorted(docmodels.keys())
                for doc_index, key in enumerate(sorted_docmodel_keys, 0):
                    docmodel = docmodels[key]
                    if word_index in docmodel:
                        word_prob = docmodel[word_index]
                        inv_index_string += '{}:{} '.format(doc_index, word_prob)

                inv_index_string = inv_index_string.rstrip()
                fout.write("{}\t{}\n".format(word_index, inv_index_string))
    else:
        print("Inverted index file already exists at {}".format(index_file))


def run_create_query_pickle(lex_file, query_utf8_file, answer_file, query_pickle):
    if os.path.exists(query_pickle):
        print("Query pickle file already exists at {}".format(query_pickle))
        return
    else:
        print("Create query pickle file at {}".format(query_pickle))

    # Load lex dict
    lex_dict = {}
    with open(lex_file, 'r') as fin:
        for idx, line in enumerate(fin.readlines(), 1):
            lex = line.strip()
            lex_dict[lex] = idx

    # Read query file
    query_dict_list = []
    with open(query_utf8_file, 'r') as f:
        for line in tqdm(f.readlines()):
            query_string = line.strip()
            query_phrases = query_string.split()

            query_dict = {}

            nphrases = len(query_phrases)
            for ph in query_phrases:
                lex_key = utf8_to_brackethex(ph)
                lex_idx = lex_dict[lex_key]
                query_dict[lex_idx] = 1. / nphrases

            query_dict_list.append(query_dict)

    # Read Answer File
    answer_dict_list = []
    for _ in range(len(query_dict_list)):
        answer_dict_list.append({})

    with open(answer_file, 'r') as f:
        for line in f.readlines():
            tokens = line.split()
            query_idx = int(tokens[0])
            doc_idx = int(tokens[1])

            answer_dict_list[query_idx][doc_idx] = 1.

    answer_index_list = range(len(answer_dict_list))

    with open(query_pickle, 'wb') as f:
        obj = list(zip(query_dict_list, answer_dict_list, answer_index_list))
        pickle.dump(obj, f, protocol=2)


def run_create_requests(docmodel_dir, inv_index_file, doclength_file, request_dir):
    if not os.path.exists(request_dir):
        os.makedirs(request_dir)
        print("Creating requests at {}".format(request_dir))

        inv_index = readInvIndex(inv_index_file)
        lengs = readDocLength(doclength_file)

        for doc_fname in tqdm(glob(os.path.join(docmodel_dir, '*'))):
            docmodel = readDocModel(doc_fname)
            for key, _ in docmodel.items():
                docmodel[key] *= math.log(1 + len(inv_index[key]))

            sorted_model = sorted(docmodel.items(), key=operator.itemgetter(1), reverse=True)

            filename = doc_fname.split('/')[-1]
            outfile = os.path.join(request_dir, str(docNameToIndex(filename)))
            with open(outfile, 'w') as fout:
                for key, val in sorted_model:
                    fout.write("{}\t{}\n".format(key, val))
    else:
        print("Request already exists at {}".format(request_dir))


def run_create_keyterms(inv_index_file, keyterm_dir):
    if not os.path.exists(keyterm_dir):
        os.makedirs(keyterm_dir)
        print("Creating keyterms at {}".format(keyterm_dir))

        inv_index = readCleanInvIndex(inv_index_file)

        for term1 in tqdm(inv_index.keys()):

            set1 = set(inv_index[term1])

            jaccard = {}

            for term2, _ in inv_index.items():
                if term1 == term2:
                    continue

                set2 = set(inv_index[term2])

                jaccard[term2] = float(len(set1 & set2)) / len(set1 | set2)

            listToPrint = sorted(jaccard.items(), key=operator.itemgetter(1), reverse=True)

            outfile = os.path.join(keyterm_dir, str(term1))
            with open(outfile, 'w') as fout:
                for term, val in listToPrint[1:100]:
                    if val != 0:
                        fout.write("{}\t{}\n".format(term, val))
    else:
        print("Keyterm already exists at {}".format(keyterm_dir))


def run_create_lda(mallet_binary, docmodel_dir, lda_dir, lex_file):
    # Make directory for mallet
    train_dir = os.path.join(lda_dir, 'mallet_train')
    if not os.path.exists(train_dir):
        os.makedirs(train_dir)

    # Make mallet file from documents
    mallet_file = os.path.join(train_dir, 'documents.mallet')
    print("Mallet: import-dir {} to {}".format(docmodel_dir, mallet_file))
    make_mallet_file_cmd = "{} import-dir --input {} --output {} --keep-sequence".format(
        mallet_binary, docmodel_dir, mallet_file)
    if os.path.exists(mallet_file):
        print("Mallet file already exists {}. Skipping...".format(mallet_file))
    else:
        os.system(make_mallet_file_cmd)

    # Train with lda
    print("Train lda topic model with mallet")

    train_topics_cmd = "{mallet_bin} train-topics --input {input} \
                                        --inferencer-filename {inferencer_filename} \
                                        --output-model {output_model} \
                                        --output-state {output_state} \
                                        --output-topic-keys {output_topic_keys} \
                                        --topic-word-weights-file {topic_words_weight_file} \
                                        --word-topic-counts-file {words_topic_counts_file} \
                                        --output-doc-topics {output_doc_topics} \
                                        --num-topics {num_topics} \
                                        --num-threads {num_threads} \
                                        --optimize-interval {optimize_interval} \
                                        --alpha {alpha} \
                                        --beta {beta}"

    # Define here to use later
    topic_words_weight_file = os.path.join(train_dir, 'topic_words_weight_file')

    train_topics_param = {'mallet_bin': mallet_binary,
                          'input': mallet_file,
                          'inferencer_filename': os.path.join(train_dir, 'inferencer.model'),
                          'output_model': os.path.join(train_dir, 'output_model.binary'),
                          'output_state': os.path.join(train_dir, 'output_state.gz'),
                          'output_topic_keys': os.path.join(train_dir, 'output_topic_keys.txt'),
                          'topic_words_weight_file': topic_words_weight_file,
                          'words_topic_counts_file': os.path.join(train_dir, 'words_topic_counts_file.txt'),
                          'output_doc_topics': os.path.join(train_dir, 'output_doc_topics.txt'),
                          'num_topics': 256,  # FROM ISDR-CMDP
                          'num_threads': 4,
                          'optimize_interval': 20,  # From Mallet Tutorial
                          'alpha': 1,  # From ISDR-CMDP
                          'beta': 0.05  # From ISDR-CMDP
                          }

    if os.path.exists(topic_words_weight_file):
        print("Topic words weight file already exists {}. Skipping...".format(topic_words_weight_file))
    else:
        os.system(train_topics_cmd.format(**train_topics_param))

    # Create topic models with normalized lda weights
    print("Create topic model word distributions with normalized lda weights {}".format(
        topic_words_weight_file))

    # Read lex
    print("Loading lex file")
    lex_dict = {}
    with open(lex_file, 'r') as fin:
        for idx, line in enumerate(fin.readlines(), 1):
            lex = line.strip()
            lex_dict[lex] = idx

    topic_models = defaultdict(dict)
    print("Reading topic weights")
    with codecs.open(topic_words_weight_file, 'r', 'utf-8') as f:
        for line in tqdm(f.readlines()):
            tokens = line.split()

            line_filename = tokens[0]

            phrase = tokens[1]
            if utf8_to_brackethex(phrase) not in lex_dict:
                lex_index = 43846
            else:
                lex_index = lex_dict[utf8_to_brackethex(phrase)]

            prob = float(tokens[2])

            topic_models[line_filename][lex_index] = prob

    print("Writing topic models")
    for fname in tqdm(topic_models.keys()):

        factor = 1. / sum(topic_models[fname].values())
        for k in topic_models[fname].keys():
            topic_models[fname][k] *= factor

        topic_path = os.path.join(lda_dir, fname)
        with open(topic_path, 'w') as fout:
            for lex_index, prob in topic_models[fname].items():
                fout.write('{}\t{}\n'.format(lex_index, prob))


def run_create_topic_rankings(mallet_binary, query_utf8_nltk_file, lda_dir, topic_ranking_dir):
    # Query file to mallet
    print("Transorming queries to mallet")
    query_mallet_file = os.path.join(lda_dir, 'mallet_train', 'queries.mallet')
    document_mallet_file = os.path.join(lda_dir, 'mallet_train', 'documents.mallet')
    import_file_cmd = "{} import-file --input {} --output {} --use-pipe-from {}"
    if os.path.exists(query_mallet_file):
        print("Query mallet file already exists {}".format(query_mallet_file))
    else:
        os.system(import_file_cmd.format(mallet_binary, query_utf8_nltk_file,
                                         query_mallet_file, document_mallet_file))

    # Infer Model
    print("Inferencing quries")
    inferencer_model = os.path.join(lda_dir, 'mallet_train', 'inferencer.model')
    query_doc_topics = os.path.join(lda_dir, 'mallet_train', 'query_doc_topics.txt')

    inference_cmd = "{} infer-topics --input {} --inferencer {} --output-doc-topics {}"
    if os.path.exists(query_doc_topics):
        print("Query doc topics already exists {}".format(query_doc_topics))
    else:
        os.system(inference_cmd.format(mallet_binary, query_mallet_file,
                                       inferencer_model, query_doc_topics))

    # Write Topic Rankings
    print("Creating Topic Rankings Get Top 20")
    if not os.path.exists(topic_ranking_dir):
        os.makedirs(topic_ranking_dir)

    with open(query_doc_topics, 'r') as f:
        next(f)
        for line in tqdm(f):
            tokens = line.split()
            fname = int(tokens[0])
            topic_probs = list(map(float, tokens[2:]))

            assert len(topic_probs) == 256

            topic_prob_tuples = zip(range(256), topic_probs)
            topic_prob_tuples = sorted(topic_prob_tuples, key=lambda x: x[1], reverse=True)

            filepath = os.path.join(topic_ranking_dir, str(fname))
            with open(filepath, 'w') as fout:
                for topic_idx, score in list(topic_prob_tuples)[:20]:
                    fout.write("{}\t{}\n".format(topic_idx, score))

####################
#       Util       #
####################


def cut_queries(query_utf8_file, query_utf8_nltk_file):
    if os.path.exists(query_utf8_nltk_file):
        print("Jieba query file has already been cut {}".format(query_utf8_nltk_file))
        return
    print("Cutting queries with jieba to {}".format(query_utf8_nltk_file))
    with codecs.open(query_utf8_file, 'r', 'utf-8') as f:
        with codecs.open(query_utf8_nltk_file, 'w', 'utf-8') as fout:
            for line in f.readlines():
                line = line.strip()
                cut_line = ' '.join(line.split())
                fout.write(cut_line + '\n')


def cut_transcript(transcript_dir, nltk_dir):
    if not os.path.exists(nltk_dir):
        os.makedirs(nltk_dir)
        print("Run cutting transcript from {} to {}".format(transcript_dir, nltk_dir))
        for filepath in tqdm(glob(os.path.join(transcript_dir, '*'))):
            if os.path.isfile(filepath):
                with open(filepath, 'r') as f:
                    text = f.read()
                    jieba_text = ' '.join(text.split())

                filename = filepath.split('/')[-1]

                with codecs.open(os.path.join(nltk_dir, filename), 'w', 'utf-8') as f:
                    f.write(jieba_text)
    else:
        print("Transcript {} has already been cut to {}".format(transcript_dir, nltk_dir))


def utf8_to_brackethex(uni_word):

    bracketed_chars = '[' + uni_word + ']'

    return bracketed_chars


if __name__ == "__main__":
    ############################
    #         Specify          #
    ############################

    transcript_name = "spoken_squad_{}".format(sys.argv[1])

    mallet_binary = 'mallet/bin/mallet'
    ###############################
    #       Reconstruct Query     #
    ###############################
    data_dir = 'data'
    transcript_dir = data_dir + "/{}/doc".format(sys.argv[1])
    query_dir = data_dir + "/{}/query".format(sys.argv[1])
    nltk_dir = data_dir + "/{}/doc/nltk".format(sys.argv[1])

    query_utf8_file = os.path.join(query_dir, 'SQuAD.query')
    query_utf8_nltk_file = os.path.join(query_dir, 'SQuAD_nltk.query')

    cut_queries(query_utf8_file, query_utf8_nltk_file)

    ###############################
    #    Create Language Models   #
    ###############################

    lm_dir = os.path.join(data_dir, transcript_name)
    docmodels_cache = os.path.join(lm_dir, 'docmodels.cache')

    save_docmodel_dir = os.path.join(lm_dir, 'docmodel')
    lex_file = os.path.join(lm_dir, transcript_name + '.lex')
    background_file = os.path.join(lm_dir, transcript_name + '.background')
    doclength_file = os.path.join(lm_dir, transcript_name + '.doclength')
    index_file = os.path.join(lm_dir, transcript_name + '.index')

    run_transcript2docmodel(query_utf8_file, transcript_dir, lex_file,
                            lm_dir, docmodels_cache, save_docmodel_dir, background_file, doclength_file, index_file)

    ###############################
    #     Create Query Pickle     #
    ###############################

    answer_file = os.path.join(query_dir, 'SQuAD.ans')
    query_pickle = os.path.join(lm_dir, 'query.pickle')

    run_create_query_pickle(lex_file, query_utf8_file, answer_file, query_pickle)

    ###############################
    #     Create Action Models    #
    ###############################

    request_dir = os.path.join(lm_dir, 'request')

    run_create_requests(save_docmodel_dir, index_file, doclength_file, request_dir)

    keyterm_dir = os.path.join(lm_dir, 'keyterm')

    run_create_keyterms(index_file, keyterm_dir)

    lda_dir = os.path.join(lm_dir, 'lda')

    # cut_transcript(transcript_dir, nltk_dir)

    run_create_lda(mallet_binary, transcript_dir, lda_dir, lex_file)

    topic_ranking_dir = os.path.join(lm_dir, 'topicRanking')

    run_create_topic_rankings(mallet_binary, query_utf8_nltk_file, lda_dir, topic_ranking_dir)
