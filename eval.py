from __future__ import division
from itertools import izip


def dist(sq):
    pass

def ngram(sq, n):
    return zip(*[sq[i:] for i in range(n)])

def precision(g, p):
    if p:
        return sum(1 for x in p if x in g) / len(p)
    else:
        return 1
# use set!
def bleu(gold, pred):
    return (precision(ngram(gold, 2), ngram(pred, 2))\
                * precision(ngram(gold, 3), ngram(pred, 3))\
                * precision(ngram(gold, 4), ngram(pred, 4))) ** 0.25 

def edit(s1,s2):
    if len(s1) > len(s2):
        s1,s2 = s2,s1
    distances = range(len(s1) + 1)
    for index2,char2 in enumerate(s2):
        newDistances = [index2+1]
        for index1,char1 in enumerate(s1):
            if char1 == char2:
                newDistances.append(distances[index1])
            else:
                newDistances.append(1 + min((distances[index1],
                                             distances[index1+1],
                                             newDistances[-1])))
        distances = newDistances
    return distances[-1] / 2
 

def read_lemmas(file_name, i):
    sent = []
    for line in open(file_name):
        line = line.strip()
        if line:
            sent.append(line.split()[i])
        elif sent:
            yield sent
            sent = []


def evaluate(gold_file, pred_file):
    bleu_acc = 0
    edit_acc = 0
    edit_all = 0
    total = 0
    for (gold, pred) in izip(read_lemmas(gold_file, 2), read_lemmas(pred_file, 0)):
        # print ' '.join(gold)
        # print ' '.join(pred)
        bleu_acc += bleu(gold, pred)
        edit_acc += edit(gold, pred)
        total += 1
        edit_all += len(gold)

    print 'bleu: %.4f' % (bleu_acc / total)
    print 'edit: %.4f' % (edit_acc / edit_all)




if __name__ == '__main__':
    evaluate('wsj_dev.conll06', 'wsj_dev.col')
