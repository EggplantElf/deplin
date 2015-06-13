from __future__ import division
from sentence import *
from model import *
import cProfile


# TODO
# implement the evaluate metrics, BLEU, NIST, Edit, Exact
# try the incremental way

#################################
# training

def train(train_file, model_file, domain_size, sent_size):
    model = Model()
    sents = [sent for sent in read_sentence(train_file)]
    print '# of sentences', len(sents)
    for it in range(10):
        oracle_score = 0
        for (i, sent) in enumerate(sents):
            if i % 100 == 0:
                print i
            for hd in sent:
                pred = domain_search(model, hd.domain, domain_size)[0]
                oracle_score += pred.get_oracle_score()
                # training the domain linearizer
                train_domain(model, hd.domain, domain_size)
        print 'oracle score:', oracle_score
        print '# of features:', len(model.feat_map)
        print '# of non-zero features:', len(filter(lambda x: x != 0, model.weights))
    print 'sequences:', Sequence.count
    print '# of mapping:', Sequence.mapped
    print '# of scoring:', Sequence.scored

    model.save(model_file)

def train_domain(model, domain, size):
    gold = domain.gold_sequence()
    # gold_sub, pred_sub = find_early_violation(model, domain, gold, size)
    gold_sub, pred_sub = find_max_violation(model, domain, gold, size)
    if gold_sub != pred_sub:
        model.update(gold_sub, pred_sub)



def find_early_violation(model, domain, gold, size):
    gold_sub = Sequence().calc(model)
    beam = [gold_sub]
    for tk in domain:
        gold_sub = get_gold_sub(gold, gold_sub, tk)
        beam = sum([insert(model, sq, tk) for sq in beam], [])
        beam.sort(key = lambda x: x.score, reverse = True)
        beam = beam[:size]
        if gold_sub not in beam:
            return gold_sub.calc(model), beam[0]
    return gold.calc(model), beam[0]

def find_max_violation(model, domain, gold, size):
    violations = []
    gold_sub = Sequence().calc(model)
    beam = [gold_sub]
    for tk in domain:
        gold_sub = get_gold_sub(gold, gold_sub, tk)
        beam = sum([insert(model, sq, tk) for sq in beam], [])
        beam.sort(key = lambda x: x.score, reverse = True)
        beam = beam[:size]
        if gold_sub not in beam:
            violations.append((gold_sub.calc(model), beam[0]))
            beam.append(gold_sub)
    if violations:
        return max(violations, key = lambda (g, p): p.score - g.score)
    else:
        return gold.calc(model), beam[0]

def get_gold_sub(gold, gold_sub, tk):
    for i in range(len(gold_sub) + 1):
        sub = Sequence(gold_sub[:i] + (tk,) + gold_sub[i:])
        if valid(gold, sub):
            return sub 

def valid(gold, sq):
    i = -1
    try:
        for t in sq:
            i = gold.index(t, i + 1)
    except ValueError:
        return False
    else:
        return True

#################################
# test
def test(filename, model_file, domain_size):
    model = Model(model_file)
    
    oracle_score = 0
    correct = 0
    total = 0
    stats = {}

    for sent in read_sentence(filename):
        for hd in sent: 
            sq = domain_search(model, hd.domain, domain_size)[0]
            l = len(sq)
            if l not in stats:
                stats[l] = [0, 0]
            if sq == hd.domain.gold_sequence():
                correct += 1
                stats[l][0] += 1
            total += 1
            stats[l][1] += 1
            oracle_score += sq.get_oracle_score()

    print 'sequences:', Sequence.count
    print 'oracle score:', oracle_score
    print 'accuracy: %d / %d = %.4f' % (correct, total, correct / total)
    for l in sorted(stats):
        print 'length = %d, accuracy: %d / %d = %.4f' % (l, stats[l][0], stats[l][1], stats[l][0] / stats[l][1])



#################################
# linearization

def linearize(filename, model_file, domain_size, sent_size):
    model = Model(model_file)
    oracle_score = 0
    correct = 0
    total = 0
    for sent in read_sentence(filename):
        candis = {}
        for hd in sent: 
            candis[hd] = domain_search(model, hd.domain, domain_size)
        sq = sent_search(model, sent, candis, sent_size)
        score = sq.get_oracle_score()
        oracle_score += score
        if score == 0:
            correct += 1
        total += 1

    print 'oracle score:', oracle_score
    print 'accuracy: %d / %d = %.4f' % (correct, total, correct / total)




#################################
# domain search

def domain_search(model, domain, size):
    beam = [Sequence().calc(model)]
    for tk in domain:
        beam = sum([insert(model, sq, tk) for sq in beam], [])
        beam.sort(key = lambda x: x.score, reverse = True)
        beam = beam[:size]
    return beam

# given (1,2), 3
# return [(3,1,2), (1,3,2), (1,2,3)]
def insert(model, sq, tk):
    combis = []
    for i in range(len(sq) + 1):
        nsq = Sequence(sq[:i] + (tk,) + sq[i:]).calc(model)
        combis.append(nsq)
    return combis

#################################
# sent search

def sent_search(model, sent, candis, size):
    beam = [Sequence().calc(model)]
    for hd in traverse(sent[0]):
        beam = [replace(model, hsq, dsq) for dsq in candis[hd] for hsq in beam]
        beam.sort(key = lambda x: x.score, reverse = True)
        beam = beam[:size]
    return beam[0]


def traverse(h):
    return [h] + sum([traverse(d) for d in h.deps], [])

def replace(model, hsq, dsq):
    if not hsq:
        return dsq
    for i, h in enumerate(hsq):
        if h in dsq:
            return Sequence(hsq[:i] + dsq + hsq[i + 1:]).calc(model)

#################################



if __name__ == '__main__':
    # train('wsj_train.f1k.conll06', 'test.model',10, 3)
    # cProfile.run("test('wsj_dev.conll06', 'test.model', 10)")
    # linearize('wsj_dev.conll06', 'test.model', 10, 1)
    cProfile.run("train('wsj_train.f1k.conll06', 'test.model',10, 3)")
