from __future__ import division
from collections import defaultdict, Counter
import cPickle
import gzip



class Model:
    def __init__(self, modelfile = None):
        if modelfile:
            self.load(modelfile)
        else:
            self.feat_map = defaultdict(int)
            self.delta = defaultdict(int)
            self.q = 0

    def save(self, modelfile):
        stream = gzip.open(modelfile,'wb')
        cPickle.dump(self.feat_map, stream, -1)
        stream.close()

    def load(self, modelfile):
        print 'loading model ...'
        stream = gzip.open(modelfile,'rb')
        self.feat_map = cPickle.load(stream)
        stream.close()

    def get_score(self, feats):
        return self.feat_map.get(feats, 0)

    def update(self, gf, pf):
        for i in gf:
            self.feat_map[i] += 1
            self.delta[i] += self.q
        for i in pf:
            self.feat_map[i] -= 1
            self.delta[i] -= self.q

    def qadd(self):
        self.q += 1

    def average(self):
        for f in self.feat_map:
            self.feat_map[f] -= self.delta[f] / self.q

    def update_pa(self, gf, pf, gs, ps):
        diff = Counter(gf)
        diff.subtract(Counter(pf))
        abs_diff = sum(abs(v) for v in diff.values())
        loss = max(ps - gs, 1)
        if abs_diff == 0:
            return
        t = loss / abs_diff
        # t = loss / abs_diff
        for i in gf:
            self.feat_map[i] += t
        for i in pf:
            self.feat_map[i] -= t





