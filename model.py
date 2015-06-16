from __future__ import division
import itertools as it
import cPickle
import gzip


class Model:
    def __init__(self, modelfile = None):
        if modelfile:
            self.load(modelfile)
            self.frozen = True
        else:
            self.feat_map = {'#': 0}
            self.feat_rev = {0: '#'}
            self.weights = [0]
            self.frozen = False

    def save(self, modelfile):
        stream = gzip.open(modelfile,'wb')
        cPickle.dump(self.weights,stream,-1)
        cPickle.dump(self.feat_map, stream, -1)
        cPickle.dump(self.feat_rev, stream, -1)
        stream.close()

    def load(self, modelfile):
        print 'loading model ...'
        stream = gzip.open(modelfile,'rb')
        self.weights = cPickle.load(stream)
        self.feat_map = cPickle.load(stream)
        self.feat_rev = cPickle.load(stream)
        stream.close()


    def map_feat(self, feat):
        if self.frozen:
            return self.feat_map.get(feat, None)
        else:
            if feat not in self.feat_map:
                l = len(self.feat_map)
                self.feat_map[feat] = l
                self.feat_rev[l] = feat
            return self.feat_map[feat]

    def rev_feat(self, i):
        return self.feat_map.get(feat, None)


    def create_weights(self):
        self.weights = [0.0] * len(self.feat_map)

    def grow_weights(self, l):
        s = max(l, (len(self.weights) + 1) // 2)
        self.weights += [0.0] * s

    def get_score(self, feats):
        if not self.frozen and feats:
            d = max(feats) - len(self.weights) + 1
            if d > 0:
                self.grow_weights(d)
        return sum(self.weights[i] for i in feats)

    def update(self, gold, pred):
        # t = min((pred.score - gold.score + 1) / (2 * min(len(pred.feats), len(gold.feats))), 0.1)
        t = 1
        for i in gold.feats:
            self.weights[i] += t
        for i in pred.feats:
            self.weights[i] -= t

    def remove_zeros(self):
        new_feat_map = {}
        new_feat_rec = {}
        





