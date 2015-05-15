class Token:
    __slots__ = ['tid', 'pid', 'lemma', 'pos', 'head', 'label']

    def __init__(self, line):
        entries = line.split()
        self.tid = int(entries[0])
        self.pid = -1
        self.lemma = entries[2]
        self.pos = entries[3]
        self.head = int(entries[6])
        self.label = entries[7]


class Root(Token):
    def __init__(self):
        self.tid = 0
        self.pid = 0
        self.lemma = 'ROOT'
        self.pos = 'ROOT'
        self.label = 'ROOT'

class Sentence(list):
    def __init__(self):
        self.append(Root())

    def add_token(self, token):
        self.append(token)

    def add_heads(self, arcs):
        for (h, d) in arcs:
            self[d].head = h


def read_sentence(filename):
    print 'reading sentences ...'
    sentence = Sentence()
    for line in open(filename):
        line = line.rstrip()
        if line:
            sentence.add_token(Token(line, train))
        elif len(sentence) != 1:
            yield sentence
            sentence = Sentence()




