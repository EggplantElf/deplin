from __future__ import division
from sentence import *
from new_model import *
from itertools import *
from collections import defaultdict
from time import time
from bisect import *

# TODO
# implement the evaluate metrics, BLEU, NIST, Edit, Exact
# finish the features!
# start real evaluatinos!

#################################
# training

def train(train_file, model_file, domain_beam_size, sent_beam_size):
    model = Model()
    sents = [sent for sent in read_sentence(train_file)]
    # sents = list(read_sentence(train_file))

    print '# of sentences', len(sents)
    for it in xrange(20):
        oracle_score = 0
        global_oracle_score = 0
        for (i, sent) in enumerate(sents):
            if i % 100 == 0:
                print i
            candidates = {}
            for h in sent:
                if len(h.domain) >1:
                    sqs = train_domain(model, h.domain, domain_beam_size)
                    oracle_score += sqs[0].get_oracle_score()
                    candidates[h] = sqs
            sent_candidates = train_sent(model, sent, candidates, sent_beam_size)
            global_oracle_score += sent_candidates[0].get_oracle_score()
        print 'oracle score:', oracle_score
        print 'global score:', global_oracle_score
        print '# of features:', len(model.feat_map)
        print '# of non-zero features:', len(filter(lambda x: x != 0, model.feat_map.values()))
    print 'sequences:', Sequence.count

    # model.save(model_file)


#################################
# train domain

def train_domain(model, domain, size):
    gold = domain.gold_sequence()
    (gold_part, pred_part), gold_seq, agenda = find_violation(model, domain, gold, size, True)
    if gold_part != pred_part:
        agenda[-1] = gold_seq
        model.update_local(gold_part, pred_part)
    return agenda


def appendable(domain, sq):
    s = domain.copy()
    for tk in sq:
        s.remove(tk)
    return s

 
def find_violation(model, domain, gold, size, find_max):
    violations = []
    gold_part = Sequence()
    agenda = [gold_part]
    for i in xrange(len(domain)):
        beam = []
        for sq in agenda:
            for tk in appendable(domain, sq):
                nsq = sq.append(model, tk)
                insort_left(beam, nsq)
        agenda = beam[:size]
        gold_part = gold_part.append(model, gold[i])
        if gold_part.score < agenda[-1].score:
            violations.append((gold_part, agenda[0]))
    if violations:
        if find_max:
            return max(violations, key = lambda (g, p): (p.score - g.score, len(p))), gold_part, agenda
        else:
            return violations[0], gold_part, agenda
    else:
        return (gold_part, agenda[0]), gold_part, agenda


#################################
# train sentence

# assume sent is the correct order for now,
def train_sent(model, sent, candidates, size):
    (gold_part, pred_part), agenda = find_violation_for_sent(model, candidates, sent, size, True)
    if gold_part != pred_part:
        model.update_global(gold_part, pred_part)
    return agenda

def traverse(h):
    # return [h] + sum([traverse(d) for d in h.deps], [])
    yield h
    for d in h.deps:
        for dd in traverse(d):
            yield dd

def gold_extension(model, candidates, gold_part, h):
    for dsq in candidates[h]:
        if dsq.is_gold():
            gold_dsq = dsq
            break
    if not gold_part:
        hsq_prefix, hsq_suffix = (), ()
    else:
        i  = gold_part.index(h)
        hsq_prefix, hsq_suffix = gold_part[:i], gold_part[i + 1:]
    nsq = Sequence(hsq_prefix + dsq + hsq_suffix)
    nsq.global_score = gold_part.score + dsq.score + nsq.get_global_score(model)
    return nsq

def get_extensions(model, candidates, agenda, h):
    for hsq in agenda:
        if not hsq:
            hsq_prefix, hsq_suffix = (), ()
        else:
            i = hsq.index(h)
            hsq_prefix, hsq_suffix = hsq[:i], hsq[i + 1:]
        for dsq in candidates[h]:
            nsq = Sequence(hsq_prefix + dsq + hsq_suffix)
            nsq.global_score = hsq.score + dsq.score + nsq.get_global_score(model)
            yield nsq

# merge with find domain violation later
# use *args to generalize
def find_violation_for_sent(model, candidates, sent, size, find_max):
    global count
    violations = []
    gold_part = Sequence()
    agenda = [gold_part]
    for h in traverse(sent.root):
        # print 'traverse', h
        # print 'gold', gold_part
        if len(h.domain) > 1:
            beam = []
            for nsq in get_extensions(model, candidates, agenda, h):
                count += 1
                insort_left(beam, nsq)
            agenda = beam[:size]
            gold_part = gold_extension(model, candidates, gold_part, h)
            if gold_part.score < agenda[-1].score:
                violations.append((gold_part, agenda[0]))
    if violations:
        if find_max:
            return max(violations, key = lambda (g, p): p.score - g.score), agenda
        else:
            return violations[0], agenda
    else:
        return (gold_part, agenda[0]), agenda



#################################
# test
# all needs change
def test(filename, model_file, domain_beam_size):
    model = Model(model_file)
    
    oracle_score = 0
    correct = 0
    total = 0
    stats = {}

    for sent in read_sentence(filename):
        for h in sent: 
            sq = domain_search(model, h.domain, domain_beam_size)[0]
            l = len(sq)
            if l not in stats:
                stats[l] = [0, 0]
            if sq == h.domain.gold_sequence():
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

def domain_search(model, domain, size):
    agenda = [Sequence()]
    for i in range(len(domain)):
        beam = []
        for sq in agenda:
            for tk in cands(domain, sq):
                nsq = sq.append(model, tk)
                insort_left(beam, nsq)
        agenda = beam[:size]
    return agenda

def sent_search(model, sent, candis, size):
    beam = [Sequence()]
    for h in traverse(sent[0]):
        beam = [replace(model, hsq, dsq) for dsq in candis[h] for hsq in beam]
        beam.sort(reverse = True)
        beam = beam[:size]
    return beam[0]


#################################



if __name__ == '__main__':
    t0 = time()
    train('wsj_train.f1k.conll06', 'test.model',10, 3)
    # train('test.conll', 'test.model',10, 3)

    # linearize('wsj_dev.conll06', 'test.model', 10, 1)
    print 'time used:', time() - t0

