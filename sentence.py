from random import *

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
        self.domain = [self]
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
        self.domain = [self]
        self.deps = []

# class Domain(list):
#     def __init__(self, head):
#         self.append(head)
#         self.tid = head.tid
#         self.head = head

    # def __repr__(self):
        # return 'd(%s)' % self.head

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
            shuffle(d.deps)


class Sequence(tuple):
    def __init__(self, *args):
        super(Sequence, self).__init__(self, *args)
        self.has_score = False


    def __repr__(self):
        return '(%s): %d' % (', '.join(str(i) for i in self), self.get_score())


    def get_score(self):
        if not self.has_score:
            self.has_score = True

            # oracle scoring function
            self.score = 0
            for (i, j) in zip(self, self[1:]):
                if i.tid > j.tid:
                    self.score += (j.tid - i.tid)
            # print 'score', self
            
        return self.score

    # def get_feat(self):



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




