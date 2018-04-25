def readInvIndex(fname):
    fin = open(fname)
    inv_index = {}
    for line in fin.readlines():
        pair = line.replace('\n', '').split('\t')
        wordID = int(pair[0])
        if pair[1] == '':
            inv_index[wordID] = {}
            continue
        docset = {}
        for valpair in pair[1].split():
            key, val = valpair.split(':')
            docset[int(key)] = float(val)
        inv_index[wordID] = docset
    fin.close()
    return inv_index


def readCleanInvIndex(fname):
    fin = open(fname)
    inv_index = {}
    for line in fin.readlines():
        pair = line.replace('\n', '').split('\t')
        wordID = int(pair[0])
        if pair[1] == '':
            continue
        docset = {}
        for valpair in pair[1].split():
            key, val = valpair.split(':')
            docset[int(key)] = float(val)
        inv_index[wordID] = docset
    fin.close()
    return inv_index


def readDocLength(fname):
    fin = open(fname)
    docLengs = {}
    for line in fin.readlines():
        pair = line.replace('\n', '').split()
        docID = docNameToIndex(pair[0])
        docleng = float(pair[1])
        docLengs[docID] = docleng
    fin.close()
    return docLengs


def readDocModel(fname):
    fout = open(fname)
    model = {}
    for line in fout.readlines():
        tokens = line.split()
        word = int(tokens[0])
        val = float(tokens[1])
        model[word] = val
    return model


def docNameToIndex(fname):
    return int(fname[1:])
