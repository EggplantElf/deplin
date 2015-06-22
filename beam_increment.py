from __future__ import division
from sentence import *
from model import *
from itertools import *
from collections import defaultdict
from time import time
from bisect import insort_left

# TODO
# implement the evaluate metrics, BLEU, NIST, Edit, Exact
# finish the features!
# mira update
# local additional global
# start real evaluatinos!

#################################
# training

def train(train_file, model_file, domain_beam_size, sent_beam_size):
    model = Model()
    sents = [sent for sent in read_sentence(train_file)]
    # sents = list(read_sentence(train_file))

    print '# of sentences', len(sents)
    for it in xrange(10):
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
            # sent_candidates = train_sent(model, sent, candidates, sent_beam_size)
            # global_oracle_score += sent_candidates[0].get_oracle_score()
        print 'oracle score:', oracle_score
        print 'global score:', global_oracle_score
        print '# of features:', len(model.feat_map)
        print '# of non-zero features:', len(filter(lambda x: x != 0, model.feat_map.values()))
    print 'sequences:', Sequence.count

    model.save(model_file)
    return model

#################################
# train domain

def train_domain(model, domain, size):
    gold = domain.gold_sequence()
    (gold_part, pred_part), gold_seq, agenda = find_violation(model, domain, gold, size, True)
    if gold_part != pred_part:
        agenda[-1] = gold_seq
        model.update_local(gold_part, pred_part)
        if gold_part is gold_seq:
            model.update_extra(gold_part, pred_part)
    return agenda


def appendable(domain, sq):
    s = domain.copy()
    for tk in sq:
        s.remove(tk)
    return s

 
def find_violation(model, domain, gold, size, find_max):
    violations = []
    gold_part = Sequence().mark_head(domain.head)
    agenda = [gold_part]
    l = len(domain)
    for i in xrange(l):
        beam = []
        for sq in agenda:
            for tk in appendable(domain, sq):
                nsq = sq.append(model, tk)
                # in the last sequence, add additional features
                if i == l - 1:
                    nsq.add_extra_score(model)
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
    violations = []
    gold_part = Sequence()
    agenda = [gold_part]
    for h in traverse(sent.root):
        # print 'traverse', h
        # print 'gold', gold_part
        if len(h.domain) > 1:
            beam = []
            for nsq in get_extensions(model, candidates, agenda, h):
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
def test(filename, model, domain_beam_size, sent_beam_size):
    oracle_score = 0
    global_score = 0
    correct = 0
    total = 0
    stats = {}

    o = open('result.txt', 'w')

    for sent in read_sentence(filename):
        candidates = {}
        for h in sent: 
            candidates[h] = domain_search(model, h.domain, domain_beam_size)
            sq = candidates[h][0]
            l = len(sq)
            if l not in stats:
                stats[l] = [0, 0]
            if sq.is_gold():
                stats[l][0] += 1
            stats[l][1] += 1
            oracle_score += sq.get_oracle_score()
        sent_sq = sent_search(model, sent, candidates, sent_beam_size)
        # sent_sq = flatten(sent, candidates)
        if sent_sq.is_gold():
            correct += 1
        total += 1
        o.write('g: %s\n' % ', '.join(str(t) for t in sorted(sent_sq)))
        o.write('p: %s\n' % ', '.join(str(t) for t in sent_sq))
    o.close()

    f = open('features.txt', 'w')
    for k in sorted(model.feat_map):
        f.write('%s%s%d\n' % (k, ' ' * (40 - len(k)),model.feat_map[k]))
    f.close()

    print 'oracle score:', oracle_score
    print 'accuracy: %d / %d = %.4f' % (correct, total, correct / total)
    for l in sorted(stats):
        print 'length = %d, accuracy: %d / %d = %.4f' % (l, stats[l][0], stats[l][1], stats[l][0] / stats[l][1])

def domain_search(model, domain, size):
    agenda = [Sequence().mark_head(domain.head)]
    l = len(domain)
    for i in xrange(l):
        beam = []
        for sq in agenda:
            for tk in appendable(domain, sq):
                nsq = sq.append(model, tk)
                if i == l - 1:
                    nsq.add_extra_score(model)
                insort_left(beam, nsq)
        agenda = beam[:size]
    return agenda


def sent_search(model, sent, candidates, size):
    agenda = [Sequence()]
    for h in traverse(sent.root):
        if len(h.domain) > 1:
            beam = []
            for nsq in get_extensions(model, candidates, agenda, h):
                insort_left(beam, nsq)
            agenda = beam[:size]
    return agenda[0]

def flatten(sent, candidates):
    pass

#################################



if __name__ == '__main__':
    t0 = time()
    model = train('wsj_train.f1k.conll06', 'test.model',10, 1)
    # model = Model('test.model')
    test('wsj_dev.conll06', model, 10, 1)
    print 'time used:', time() - t0

