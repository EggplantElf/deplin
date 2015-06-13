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
        return Sequence(sorted(self, key = lambda x: x.tid))

    # def __repr__(self):
    #     return 'd(%s)' % self.head

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
            shuffle(d.domain)
            # d.domain.reverse()
            shuffle(d.deps)


class Sequence(tuple):
    count = 0
    mapped = 0
    scored = 0
    appended = 0

    def __init__(self, *args):
        super(Sequence, self).__init__(self, *args)
        Sequence.count += 1
    def __repr__(self):
        return '(%s): %d' % (', '.join(str(i) for i in self), self.score)

    def calc(self, model):
        self.get_feats(model)
        self.get_score(model)
        return self

    def get_feats(self, model):
        self.feats = []
        for i in self:
            self.add_feat(model, 'LB:%s' % i.label)
            self.add_feat(model, 'LM:%s' % i.lemma)
            self.add_feat(model, 'P:%s' % i.pos)
        for (i, j) in izip(self, self[1:]):
            self.add_feat(model, 'LB1_LB2:%s_%s' % (i.label, j.label))
            self.add_feat(model, 'LM1_LM2:%s_%s' % (i.lemma, j.lemma))
            self.add_feat(model, 'LB1_LM2:%s_%s' % (i.label, j.lemma))
            self.add_feat(model, 'P1_P2:%s_%s' % (i.pos, j.pos))
        for (i, j, k) in izip(self, self[1:], self[2:]):
            self.add_feat(model, 'LM1_LM2_LM3:%s_%s_%s' % (i.lemma, j.lemma, k.lemma))
            self.add_feat(model, 'P1_P2_P3:%s_%s_%s' % (i.pos, j.pos, k.pos))
        Sequence.mapped += 1

    def add_feat(self, model, feat_str):
        feat = model.map_feat(feat_str)
        if feat != None:
            self.feats.append(feat)

    def get_score(self, model):
        self.score = model.get_score(self.feats)
        Sequence.scored += 1

    def get_oracle_score(self):
        score = 0
        for (i, j) in izip(self, self[1:]):
            if i.tid > j.tid:
                score += (j.tid - i.tid)
        return score

    def append(self, model, tk):
        sq = Sequence(self + (tk,))
        inc_feats = []
        func = lambda x: inc_feats.append(model.map_feat(x))

        func('LB:%s' % tk.label)
        func('LM:%s' % tk.lemma)
        func('P:%s' % tk.pos)

        if len(self) >= 1:
            func('LB1_LB2:%s_%s' % (self[-1].label, tk.label))
            func('LM1_LM2:%s_%s' % (self[-1].lemma, tk.lemma))
            func('LB1_LM2:%s_%s' % (self[-1].label, tk.lemma))
            func('P1_P2:%s_%s' % (self[-1].pos, tk.pos))
        if len(self) >= 2:
            func('LM1_LM2_LM3:%s_%s_%s' % (self[-2].lemma, self[-1].lemma, tk.lemma))
            func('P1_P2_P3:%s_%s_%s' % (self[-2].pos, self[-1].pos, tk.pos))
        inc_feats = filter(lambda x: x, inc_feats)
        inc_score = model.get_score(inc_feats)
        sq.feats = self.feats + inc_feats
        sq.score = self.score + inc_score
        Sequence.appended += 1
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


def not_none(x):
    return x != None

