from sentence import *
from linearizer import *
from random import random
from itertools import permutations

def main(filename):
    lin = Linearizer()
    for sent in read_sentence(filename):
        beam = beam_search(sent, 10)


def beam_search(sent, size):
    gscores = {}
    agenda = [Sequence()]
    candis = {}
    for h in sent:
        dm = h.domain
        candis[h] = domain_candis(dm, 10)

    for h in traverse(sent[0]):
        print h, candis[h]
        beam = []
        for dseq in candis[h]:
            for hseq in agenda:
                nseq = replace(hseq, dseq)
                beam.append(nseq)
        beam.sort(key = lambda x: x.get_score(), reverse = True)
        if len(beam) > size:
            agenda = beam[:size]
        else:
            agenda = beam
    for seq in agenda:
        print seq


# beam search for candidate sequences of a domain
def domain_candis(dm, size):
    agenda = [Sequence()]
    for t in dm:
        beam = sum([insert(seq, t) for seq in agenda], [])
        beam.sort(key = lambda x: x.get_score(), reverse = True)
        if len(beam) > size:
            agenda = beam[:size]
        else:
            agenda = beam
    return agenda


# given (1,2), 3
# return [(3,1,2), (1,3,2), (1,2,3)]
def insert(seq, t):
    combis = []
    for i in range(len(l) + 1):
        nseq = Sequence(seq[:i] + (t,) + seq[i:])
        combis.append(nseq)
    return combis

def replace(hseq, dseq):
    if not hseq:
        return dseq
    for i, h in enumerate(hseq):
        if h in dseq:
            return Sequence(hseq[:i] + dseq + hseq[i + 1:])


def traverse(h):
    return [h] + sum([traverse(d) for d in h.deps], [])


def global_score(l):
    return 1



def stats(filename):
    stat = {}
    for sent in read_sentence(filename):
        for h in traverse(sent[0]):
            l = len(h.domain)
            if l not in stat:
                stat[l] = 0
            stat[l] += 1
    for k in sorted(stat):
        print k, stat[k]

if __name__ == '__main__':
    # stats('wsj_train.conll06')
    main('test.conll')