from __future__ import division
from sentence import *
import cProfile
from multiprocessing import Process, Manager, Pool
from itertools import izip, repeat

# TODO
# even multi-thread/processing
# implement the evaluate metrics, BLEU, NIST, Edit, Exact
# improve speed for tk in sq

#################################
# parallel batch learning

def grouper(iterable, n):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip(*args)

def update(model, gold, pred):
    for i in gold.get_full_feats():
        try:
            model[i] += 1
        except:
            model[i] = 1
    for i in pred.get_full_feats():
        try:
            model.feat_map[i] -= 1
        except:
            model[i] = -1

def train_parallel(train_file, model_file, batch_size, domain_size):
    model = Manager().dict()
    sents = list(read_sentence(train_file))
    batches = grouper(sents, batch_size)
    jobs = []
    for it in xrange(10):
        for batch in batches:
            p = Process(target=train_batch ,args=(model, batch, domain_size))
            jobs.append(p)
            p.start()
        for p in jobs:
            p.join()
        print '# of features:', len(model)
        print '# of non-zero features:', len(filter(lambda x: x != 0, model.values()))


def train_batch(model, batch, domain_size):
    print 10
    for sent in batch:
        for hd in sent:
            train_domain(model, hd.domain, domain_size)
    


def train_domain(model, domain, size):
    gold = domain.gold_sequence()
    gold_sub, pred_sub = find_early_violation(model, domain, gold, size)
    # gold_sub, pred_sub = find_max_violation(model, domain, gold, size)
    if gold_sub != pred_sub:
        update(model, gold_sub, pred_sub)


def find_early_violation(model, domain, gold, size):
    gold_sub = Sequence()
    agenda = [gold_sub]
    for i in xrange(len(domain)):
        beam = []
        for sq in agenda:
            for tk in domain - set(sq):
                nsq = sq.append(model, tk) # 44 sec
                beam.append(nsq)
        beam.sort(key = lambda x: x.score, reverse = True)
        agenda = beam[:size]
        gold_sub = gold_sub.append(model, gold[i])
        if gold_sub not in agenda:
            return gold_sub, agenda[0]
    return gold_sub, agenda[0]


def find_max_violation(model, domain, gold, size):
    violations = []
    gold_sub = Sequence()
    agenda = [gold_sub]
    for i in xrange(len(domain)):
        beam = []
        for sq in agenda:
            for tk in domain:
                if tk not in sq:
                    nsq = sq.append(model, tk)
                    beam.append(nsq)
        beam.sort(key = lambda x: x.score, reverse = True)
        agenda = beam[:size]
        gold_sub = gold_sub.append(model, gold[i])
        if gold_sub not in agenda:
            violations.append((gold_sub, agenda[0]))
            agenda.append(gold_sub)
    if violations:
        return max(violations, key = lambda (g, p): p.score - g.score)
    else:
        return gold_sub, agenda[0]



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
    print 'mapped:', Sequence.mapped
    print 'scored:', Sequence.scored
    print 'appended:', Sequence.appended

    print 'oracle score:', oracle_score
    print 'accuracy: %d / %d = %.4f' % (correct, total, correct / total)
    for l in sorted(stats):
        print 'length = %d, accuracy: %d / %d = %.4f' % (l, stats[l][0], stats[l][1], stats[l][0] / stats[l][1])


#################################
# domain search

def domain_search(model, domain, size):
    agenda = [Sequence()]
    for i in range(len(domain)):
        beam = []
        for sq in agenda:
            for tk in domain:
                if tk not in sq:
                    nsq = sq.append(model, tk)
                    beam.append(nsq)
        beam.sort(key = lambda x: x.score, reverse = True)
        agenda = beam[:size]
    return agenda



#################################
# sent search

def sent_search(model, sent, candis, size):
    beam = [Sequence()]
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
    # cProfile.run("train_parallel('wsj_train.f1k.conll06', 'test.model', 10, 10)")
    train_parallel('wsj_train.f1k.conll06', 'test.model', 10, 10)
