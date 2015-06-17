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
        self.feats = []
        Sequence.count += 1
        # experiment
        # self.set = set(self)

    def __repr__(self):
        return '(%s): %d' % (', '.join(str(i) for i in self), self.score)

    def get_feats(self, model):
        l = len(self)
        if l >= 2:
            self.feats.append(model.get_feat('LB1_LB2:%s_%s' % (self[-2].label, self[-1].label)))
            self.feats.append(model.get_feat('LM1_LM2:%s_%s' % (self[-2].lemma, self[-1].lemma)))
            self.feats.append(model.get_feat('LB1_LM2:%s_%s' % (self[-2].label, self[-1].lemma)))
            self.feats.append(model.get_feat('P1_P2:%s_%s' % (self[-2].pos, self[-1].pos)))
        if l >= 3:
            self.feats.append(model.get_feat('LM1_LM2_LM3:%s_%s_%s' % (self[-3].lemma, self[-2].lemma, self[-1].lemma)))
            self.feats.append(model.get_feat('P1_P2_P3:%s_%s_%s' % (self[-3].pos, self[-2].pos, self[-1].pos)))

    def get_full_feats(self):
        if self.prev:
            return self.prev.get_full_feats() + self.feats
        else:
            return []

    def get_score(self, model):
        self.score = self.prev.score + model.get_score(self.feats)


    def get_oracle_score(self):
        score = 0
        for (i, j) in izip(self, self[1:]):
            if i.tid > j.tid:
                score += (j.tid - i.tid)
        return score

    def append(self, model, tk):
        sq = Sequence(self + (tk,))
        sq.prev = self
        sq.get_feats(model)
        sq.get_score(model)
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



