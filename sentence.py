from random import *
from itertools import izip

class Token:
    __slots__ = ['sent', 'tid', 'pid', 'lemma', 'pos', 'hid', 'label', 'domain', 'deps']

    def __init__(self, line):
        entries = line.split()
        self.sent = None
        self.tid = int(entries[0]) # gold data, don't touch!
        self.pid = -1
        self.lemma = entries[2]
        self.pos = entries[3]
        self.hid = int(entries[6])
        self.label = entries[7]
        self.domain = Domain(self)
        self.deps = []

    def __repr__(self):
        return str(self.tid)

    def single(self):
        return len(self.domain) == 1



class Root(Token):
    __slots__ = ['sent', 'tid', 'pid', 'lemma', 'pos', 'hid', 'label', 'domain', 'deps']
    def __init__(self):
        self.tid = 0
        self.pid = 0
        self.hid = None
        self.sent = None
        self.lemma = 'ROOT'
        self.pos = 'ROOT'
        self.label = 'ROOT'
        self.domain = Domain(self)
        self.deps = []

class Domain(list):
    def __init__(self, head):
        self.append(head)
        self.head = head

    def gold_sequence(self):
        return sorted(self, key = lambda x: x.tid)

class Sentence(list):
    def __init__(self):
        self.append(Root())
        self.arcs = []

    def add_token(self, token):
        self.append(token)
        token.sent = self

    def get_domains(self):
        for d in self[1:]:
            h = self[d.hid]
            h.domain.append(d)
            h.deps.append(d)

    def randomize(self):
        for d in self:
            # shuffle(d.domain)
            d.domain.reverse()
            # shuffle(d.deps)
            d.deps.reverse()


class Sequence(tuple):
    count = 0

    def __init__(self, *args):
        super(Sequence, self).__init__(self, *args)
        self.prev = None
        self.score = 0
        Sequence.count += 1

    def __repr__(self):
        return '(%s): %d' % (', '.join(str(i) for i in self), self.score)

    def get_local_feats(self):
        l = len(self)
        feats = []
        if l >= 2:
            feats.append('LB1_LB2:%s_%s' % (self[-2].label, self[-1].label))
            feats.append('LM1_LM2:%s_%s' % (self[-2].lemma, self[-1].lemma))
            feats.append('LB1_LM2:%s_%s' % (self[-2].label, self[-1].lemma))
            feats.append('P1_P2:%s_%s' % (self[-2].pos, self[-1].pos))
            if l >= 3:
                feats.append('LM1_LM2_LM3:%s_%s_%s' % (self[-3].lemma, self[-2].lemma, self[-1].lemma))
                feats.append('P1_P2_P3:%s_%s_%s' % (self[-3].pos, self[-2].pos, self[-1].pos))
        return feats

    # maybe even not list, but direct update here, try later
    # doesn't matter much, too few updates anyway
    def get_full_feats(self):
        if self.prev:
            return self.prev.get_full_feats() + self.get_local_feats()
        else:
            return []

    def get_local_score(self, model):
        l = len(self)
        s = 0
        if l >= 2:
            s += model.get_score('LB1_LB2:%s_%s' % (self[-2].label, self[-1].label))
            s += model.get_score('LM1_LM2:%s_%s' % (self[-2].lemma, self[-1].lemma))
            s += model.get_score('LB1_LM2:%s_%s' % (self[-2].label, self[-1].lemma))
            s += model.get_score('P1_P2:%s_%s' % (self[-2].pos, self[-1].pos))
            if l >= 3:
                s += model.get_score('LM1_LM2_LM3:%s_%s_%s' % (self[-3].lemma, self[-2].lemma, self[-1].lemma))
                s += model.get_score('P1_P2_P3:%s_%s_%s' % (self[-3].pos, self[-2].pos, self[-1].pos))
        return s

    def get_full_score(self, model):
        self.score = self.prev.score + self.get_local_score(model)

    def get_oracle_score(self):
        score = 0
        for (i, j) in izip(self, self[1:]):
            if i.tid > j.tid:
                score += (j.tid - i.tid)
        return score

    def append(self, model, tk):
        sq = Sequence(self + (tk,))
        sq.prev = self
        sq.get_full_score(model)
        return sq


def read_sentence(filename):
    print 'reading sentences ...'
    sentence = Sentence()
    for line in open(filename):
        line = line.rstrip()
        if line:
            sentence.add_token(Token(line))
        elif len(sentence) != 1:
            sentence.get_domains()
            sentence.randomize()
            yield sentence
            sentence = Sentence()



