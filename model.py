from __future__ import division
import itertools as it
from collections import defaultdict
import cPickle
import gzip



class Model:
    def __init__(self, modelfile = None):
        if modelfile:
            self.load(modelfile)
        else:
            self.feat_map = defaultdict(int)

    def save(self, modelfile):
        stream = gzip.open(modelfile,'wb')
        cPickle.dump(self.feat_map, stream, -1)
        stream.close()

    def load(self, modelfile):
        print 'loading model ...'
        stream = gzip.open(modelfile,'rb')
        self.feat_map = cPickle.load(stream)
        stream.close()


    def get_score(self, feat):
        return self.feat_map.get(feat, 0)

    def update(self, gold, pred):
        for i in gold.get_full_feats():
            self.feat_map[i] += 1
        for i in pred.get_full_feats():
            self.feat_map[i] -= 1






