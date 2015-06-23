from random import *
from itertools import izip

class Token:
    __slots__ = ['sent', 'tid', 'pid', 'lemma', 'pos', 'hid', 'label', 'domain', 'deps']

    # # for conll06
    # def __init__(self, line):
    #     entries = line.split()
    #     self.tid = int(entries[0]) # gold data, don't touch!
    #     self.pid = -1
    #     self.lemma = entries[2]
    #     self.pos = entries[3]
    #     self.hid = int(entries[6])
    #     self.label = entries[7]
    #     self.domain = Domain(self)
    #     self.deps = []

    # for conll09
    def __init__(self, line):
        entries = line.split()
        self.tid = int(entries[0].split('_')[1]) # gold data, don't touch!
        self.pid = -1
        self.lemma = entries[2]
        self.pos = entries[4]
        self.hid = int(entries[8])
        self.label = entries[10]
        self.domain = Domain(self)
        self.deps = []
        # for output
        self.line = line

    def __repr__(self):
        return str(self.tid)



    # def __eq__(self, ):
    #     return 

    def __lt__(self, other):
        return self.tid < other.tid

    def single(self):
        return len(self.domain) == 1

    # add more cached features
    def lemma_label_pos(self):
        return self.lemma, self.label, self.pos

class Root(Token):
    __slots__ = ['sent', 'tid', 'pid', 'lemma', 'pos', 'hid', 'label', 'domain', 'deps']
    def __init__(self):
        self.tid = 0
        self.pid = 0
        self.hid = None
        self.head = None
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
            d.head = h
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
        # self.global_score = 0
        Sequence.count += 1
        # head of the domain could be useful in some features

    # def __repr__(self):
        # return '(%s): %d' % (', '.join(str(i) for i in self), self.score)
        # return '(%s): %d' % ', '.join(str(i) for i in self)

    # be careful here, very dangerous
    def __lt__(self, other):
        return self.score > other.score

    def mark_head(self, head):
        self.head = head
        return self

    # @profile
    def append(self, model, tk):
        sq = Sequence(self + (tk,))
        sq.head = self.head
        sq.prev = self
        sq.score = sq.get_local_score(model)
        return sq

    def copy(self):
        sq = Sequence(self)
        sq.head = self.head
        sq.prev = self.prev
        sq.score = self.score
        return sq


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
  
    # cache more atom features to save time
    def local_map(self, func):
        l = len(self)
        if l > 1:
            t1, t2 = self[-1], self[-2]
            lm1, lb1, p1 = t1.lemma_label_pos()
            lm2, lb2, p2 = t2.lemma_label_pos()
            h = self.head_code(t1, t2)
            d = l - 2
            nc1, nc2 = len(t1.deps), len(t2.deps)
            yield func('f1~LB1_LB2:%s_%s' % (lb1, lb2))
            yield func('f2~LM1_LM2:%s_%s' % (lm1, lm2))
            yield func('f3~LB1_LM1:%s_%s' % (lb1, lm1))
            yield func('f4~LB1_LM2:%s_%s' % (lb1, lm2))
            yield func('f5~LB2_LM1:%s_%s' % (lb2, lm1))
            yield func('f6~LB2_LM2:%s_%s' % (lb2, lm2))
            yield func('f7~P1_P2:%s_%s' % (p1, p2))
            yield func('f8~P1_P2_H:%s_%s_%s' % (p1, p2, h))
            yield func('f9~LB1_LB2_P1_H:%s_%s_%s_%s' % (lb1, lb2, p1, h))
            yield func('f10~LB1_LB2_P2_H:%s_%s_%s_%s' % (lb1, lb2, p2, h))
            yield func('f11~LB1_LB2_P1_P2_H:%s_%s_%s_%s_%s' % (lb1, lb2, p1, p2, h))
            yield func('f12~LB1_LB2_P1_NC2_H:%s_%s_%s_%s_%s' % (lb1, lb2, p1, nc2, h))
            yield func('f13~LB1_LB2_P2_NC1_H:%s_%s_%s_%s_%s' % (lb1, lb2, p2, nc1, h))

            if l > 2:
                t3 = self[-2]
                lm3, lb3, p3 = self[-3].lemma_label_pos()
                h = self.head_code(t1, t2, t3)
                d = l - 3
                yield func('f14~LM1_LM2_LM3:%s_%s_%s' % (lm1, lm2, lm3))
                yield func('f15~LM1_LM2_LM3_D:%s_%s_%s_%s' % (lm1, lm2, lm3, d))
                yield func('f16~P1_P2_P3:%s_%s_%s' % (p1, p2, p3))
                yield func('f17~P1_P2_P3_D:%s_%s_%s_%s' % (p1, p2, p3, d))
                yield func('f18~LM1_LM3_H:%s_%s_%s' % (lm1, lm3, h))
                yield func('f19~LM1_LM3_H_D:%s_%s_%s_%s' % (lm1, lm3, h, d))
                yield func('f20~LB1_LB2_LB3_H:%s_%s_%s_%s' % (lb1, lb2, lb3, h))
                yield func('f21~LB1_LB2_LB3_H_D:%s_%s_%s_%s_%s' % (lb1, lb2, lb3, h, d))
                yield func('f22~LB1_LB2_LB3_LM1_P2_H:%s_%s_%s_%s_%s_%s' % (lb1, lb2, lb3, lm1, p2, h))
                yield func('f23~LB1_LB2_LB3_LM1_P2_H_D:%s_%s_%s_%s_%s_%s_%s' % (lb1, lb2, lb3, lm1, p2, h, d))
                yield func('f24~LB1_LB2_LB3_LM2_P1_H:%s_%s_%s_%s_%s_%s' % (lb1, lb2, lb3, lm2, p1, h))
                yield func('f25~LB1_LB2_LB3_LM2_P1_H_D:%s_%s_%s_%s_%s_%s_%s' % (lb1, lb2, lb3, lm2, p1, h, d))

    def add_extra_score(self, model):
        self.score += sum(self.extra_map(model.get_score))

    def get_extra_feats(self):
        return list(self.extra_map(lambda x: x))

    def extra_map(self, func):
        l = len(self)
        que = self.question()
        lmh, lbh, ph = self.head.lemma_label_pos()
        posh = self.pos_head()

        if l > 1:
            yield func('f26~LBl1_LBr1_LBr2_Pl1_Pr1_POSh_L>3:%s_%s_%s_%s_%s_%s_%s' \
                % (self[0].label, self[-1].label, self[-2].label, self[0].pos, self[-1].pos, posh, l > 3))
        if l > 2:
            yield func('f27~LBl1_LBl2_LBl3_Pr1_Pr2_POSh_?_L>4:%s_%s_%s_%s_%s_%s_%s_%s'\
                % (self[0].label, self[1].label, self[2].label, self[-1].pos, self[-2].label, posh, que, l > 4))
            yield func('f28~LBl1_LBl2_LBl3_Pr1_Pr2_LMh_?_L>4:%s_%s_%s_%s_%s_%s_%s_%s'\
                % (self[0].label, self[1].label, self[2].label, self[-1].pos, self[-2].label, lmh, que, l > 4))
        if l > 3:
            yield func('f29~Pl1_Pl2_Pl3_Pl4_Pr1_LBh_POSh_?_L>6:%s_%s_%s_%s_%s_%s_%s_%s_%s'\
                % (self[0].pos, self[1].pos, self[2].pos, self[3].pos, self[-1].pos, lbh, posh, que, l > 6))
            yield func('f30~Pr1_Pr2_Pr3_Pr4_Pl1_LBh_POSh_?_L>6:%s_%s_%s_%s_%s_%s_%s_%s_%s'\
                % (self[-1].pos, self[-2].pos, self[-3].pos, self[-4].pos, self[0].pos, lbh, posh, que, l > 6))
        yield func('f31~Pl1_Pr1_LMl1_LMr1_LMh_POSh_?:%s_%s_%s_%s_%s_%s_%s'\
            % (self[0].pos, self[-1].pos, self[0].lemma, self[-1].lemma, lmh, posh, que))


    def head_code(self, t1, t2, t3 = None):
        if t1 is self.head:
            return 1
        elif t2 is self.head:
            return 2
        elif t3 is self.head:
            return 3
        else:
            return 0

    def question(self):
        return any(t.lemma == '?' for t in self)

    def pos_head(self):
        return self.index(self.head)


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


