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

    # def __eq__(self, ):
    #     return 

    def __lt__(self, other):
        return self.tid < other.tid

    def single(self):
        return len(self.domain) == 1

    def lemma_label_pos(self):
        return self.lemma, self.label, self.pos

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

class Domain(set):
    def __init__(self, head):
        self.add(head)
        self.head = head

    def gold_sequence(self):
        # return sorted(self, key = lambda x: x.tid)
        return sorted(self)

class Sentence(list):
    def __init__(self):
        self.root = Root()
        self.append(self.root)

    def add_token(self, token):
        self.append(token)
        token.sent = self

    def get_domains(self):
        for d in self[1:]:
            h = self[d.hid]
            h.domain.add(d)
            h.deps.append(d)

    def randomize(self):
        for d in self:
            # shuffle(d.domain)
            # d.domain.reverse()
            # shuffle(d.deps)
            d.deps.reverse()


class Sequence(tuple):
    count = 0

    def __init__(self, *args):
        super(Sequence, self).__init__(self, *args)
        self.prev = None
        self.score = 0
        self.global_score = 0
        Sequence.count += 1
        # head of the domain could be useful in some features

    # def __repr__(self):
        # return '(%s): %d' % (', '.join(str(i) for i in self), self.global_score)

    # be careful here, very dangerous
    def __lt__(self, other):
        return self.global_score > other.global_score

    # @profile
    def append(self, model, tk):
        sq = Sequence(self + (tk,))
        sq.prev = self
        sq.score = sq.get_local_score(model)
        sq.global_score = sq.score
        return sq

    # could be slow, really slow! try head_index
    # only sequences generated in the sent search have real global score
    # def extend(self, model, dsq):
    #     nsq = Sequence(self[:i] + dsq + self[i + 1:])
    #     nsq.global_score = self.score + dsq.score + nsq.get_global_score(model)
    #     return nsq

    def is_gold(self):
        return all(i < j for (i, j) in izip(self, self[1:]))

    def get_oracle_score(self):
        score = 0
        for (i, j) in izip(self, self[1:]):
            if i.tid > j.tid:
                score += (j.tid - i.tid)
        return score

    def get_local_score(self, model):
        return self.prev.score + sum(self.local_map(model.get_score))


    def get_local_feats(self):
        if self.prev:
            return self.prev.get_local_feats() + list(self.local_map(lambda x: x))
        else:
            return []
  
    def local_map(self, func):
        if len(self) > 1:
            lm1, lb1, p1 = self[-1].lemma_label_pos()
            lm2, lb2, p2 = self[-2].lemma_label_pos()
            yield func('LB1_LB2:%s_%s' % (lb1, lb2))
            yield func('LM1_LM2:%s_%s' % (lm1, lm2))
            yield func('LB1_LM2:%s_%s' % (lb1, lm2))
            yield func('P1_P2:%s_%s' % (p1, p2))
            if len(self) > 2:
                lm3, lb3, p3 = self[-3].lemma_label_pos()
                yield func('LM1_LM2_LM3:%s_%s_%s' % (lm1, lm2, lm3))
                yield func('P1_P2_P3:%s_%s_%s' % (p1, p2, p3))


    def get_global_score(self, model):
        return sum(self.global_map(model.get_score))

    def get_global_feats(self):
        return list(self.global_map(lambda x: x))


    def global_map(self, func):
        if len(self) > 6:
            yield func('P_F3_L3:%s_%s_%s_%s_%s_%s' % \
                (self[1].pos, self[2].pos, self[3].pos, self[4].pos, self[5].pos, self[6].pos))


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


