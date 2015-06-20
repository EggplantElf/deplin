from __future__ import division
from collections import defaultdict
import itertools as it
import cPickle
import gzip



class Model:
    def __init__(self, modelfile = None):
        if modelfile:
            self.load(modelfile)
        else:
            self.feat_map = defaultdict(int)
            # self.feat_map = {}

    def save(self, modelfile):
        stream = gzip.open(modelfile,'wb')
        cPickle.dump(self.feat_map, stream, -1)
        stream.close()

    def load(self, modelfile):
        print 'loading model ...'
        stream = gzip.open(modelfile,'rb')
        self.feat_map = cPickle.load(stream)
        stream.close()

    # defaultdict is better than get, weird
    def get_score(self, feats):
        return self.feat_map.get(feats, 0)
        # return self.feat_map[feats]
        

    def update_local(self, gold, pred):
        for i in gold.get_local_feats():
            self.feat_map[i] += 1
        for i in pred.get_local_feats():
            self.feat_map[i] -= 1

    def update_global(self, gold, pred):
        for i in gold.get_global_feats():
            self.feat_map[i] += 1
        for i in pred.get_global_feats():
            self.feat_map[i] -= 1





