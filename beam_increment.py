from __future__ import division
from sentence import *
from model import *
from itertools import *
from collections import defaultdict
from time import time
from bisect import insort_left
import sys

# TODO
# implement the evaluate metrics, BLEU, NIST, Edit, Exact
# mira update! not working
# give output to evaluate, it should be plain text, 
# exchange of same words in the same domain should be tolerented!!!
# start real evaluations!
# use bisect for small beam, sort for large beam

FEAT = False
ITER = 10

#################################
# training

def train(train_file, model_file, domain_beam_size, sent_beam_size):
    model = Model()
    sents = [sent for sent in read_sentence(train_file)]
    # sents = list(read_sentence(train_file))

    print '# of sentences', len(sents)
    for it in xrange(ITER):
        oracle_score = 0
        # global_oracle_score = 0
        for (it, sent) in enumerate(sents):
            if it % 100 == 0:
                print it
            candidates = {}
            for h in sent:
                if len(h.domain) >1:
                    sqs = train_domain(model, h.domain, domain_beam_size, it)
                    oracle_score += sqs[0].get_oracle_score()
                    candidates[h] = sqs
                    model.qadd()
            # sent_candidates = train_sent(model, sent, candidates, sent_beam_size)
            # global_oracle_score += sent_candidates[0].get_oracle_score()
        print 'oracle score:', oracle_score
        # print 'global score:', global_oracle_score
        print '# of features:', len(model.feat_map)
        print '# of non-zero features:', len(filter(lambda x: x != 0, model.feat_map.values()))
    print 'sequences:', Sequence.count

    if FEAT:
        f = open('features.txt', 'w')
        for k in sorted(model.feat_map):
            f.write('%s%s%d\n' % (k, ' ' * (80 - len(k)),model.feat_map[k]))
        f.close()

    model.average()
    model.save(model_file)
    return model

#################################
# train domain

def train_domain(model, domain, size, it):
    gold = domain.gold_sequence()
    (gold_part, pred_part), gold_seq, agenda = find_violation(model, domain, gold, size, True)
    if gold_part != pred_part:
        gf, pf = gold_part.get_local_feats(), pred_part.get_local_feats()
        if gold_part is gold_seq:
            gf += gold_part.get_extra_feats()
            pf += pred_part.get_extra_feats()
        model.update(gf, pf)

        # if it < 3:
        #     model.update(gf, pf, gold_part.score, pred_part.score)
        # else:
        #     model.update_pa(gf, pf, gold_part.score, pred_part.score)


        # use only if train sentence
        # agenda[-1] = gold_seq
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
        if i == l - 1:
            gold_part.add_extra_score(model)
        if gold_part.score < agenda[-1].score:
            violations.append((gold_part, agenda[0]))

    # add extra score for the final sequence
    # gold_part = gold_part.copy()
    # gold_part.add_extra_score(model)
    # for sq in agenda:
    #     sq.add_extra_score(model)
    # agenda.sort()
    # if gold_part.score < agenda[-1].score:
    #     violations.append((gold_part, agenda[0]))

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
# def train_sent(model, sent, candidates, size):
#     (gold_part, pred_part), agenda = find_violation_for_sent(model, candidates, sent, size, True)
#     if gold_part != pred_part:
#         model.update_global(gold_part, pred_part)
#     return agenda


# def gold_extension(model, candidates, gold_part, h):
#     for dsq in candidates[h]:
#         if dsq.is_gold():
#             gold_dsq = dsq
#             break
#     if not gold_part:
#         hsq_prefix, hsq_suffix = (), ()
#     else:
#         i  = gold_part.index(h)
#         hsq_prefix, hsq_suffix = gold_part[:i], gold_part[i + 1:]
#     nsq = Sequence(hsq_prefix + dsq + hsq_suffix)
#     # nsq.global_score = gold_part.score + dsq.score + nsq.get_global_score(model)
#     return nsq


# # merge with find domain violation later
# # use *args to generalize
# def find_violation_for_sent(model, candidates, sent, size, find_max):
#     violations = []
#     gold_part = Sequence()
#     agenda = [gold_part]
#     for h in traverse(sent.root):
#         # print 'traverse', h
#         # print 'gold', gold_part
#         if len(h.domain) > 1:
#             beam = []
#             for nsq in get_extensions(model, candidates, agenda, h):
#                 insort_left(beam, nsq)
#             agenda = beam[:size]
#             gold_part = gold_extension(model, candidates, gold_part, h)
#             if gold_part.score < agenda[-1].score:
#                 violations.append((gold_part, agenda[0]))
#     if violations:
#         if find_max:
#             return max(violations, key = lambda (g, p): p.score - g.score), agenda
#         else:
#             return violations[0], agenda
#     else:
#         return (gold_part, agenda[0]), agenda



#################################
# test
# all needs change
def test(input_file, output_file, model, domain_beam_size, sent_beam_size):
    oracle_score = 0
    # global_score = 0
    correct = 0
    total = 0
    correct_domain = 0
    total_domain = 0
    stats = {}
    bleu_acc = 0

    o = open(output_file, 'w')

    for sent in read_sentence(input_file):
        candidates = {}
        for h in sent: 
            candidates[h] = domain_search(model, h.domain, domain_beam_size)
            sq = candidates[h][0]
            l = len(sq)
            if l > 0:
                if l not in stats:
                    stats[l] = [0, 0]
                if sq.is_gold():
                    stats[l][0] += 1
                    correct_domain += 1
                stats[l][1] += 1
                total_domain += 1
            oracle_score += sq.get_oracle_score()
        sent_sq = sent_search(model, sent, candidates, sent_beam_size)
        # sent_sq = flatten(sent, candidates)
        if sent_sq.is_gold():
            correct += 1
        bleu_acc += bleu(sent_sq)
        total += 1
        for tk in sent_sq:
            if tk.lemma != 'ROOT':
                o.write('%s\n' % tk.line)
        o.write('\n')
    o.close()

    print 'oracle score:', oracle_score
    print 'exact match: %d / %d = %.4f' % (correct, total, correct / total)
    print 'domain accuracy: %d / %d = %.4f' % (correct_domain, total_domain, correct_domain / total_domain)
    print 'bleu:', bleu_acc / total
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
    # for sq in agenda:
    #     sq.add_extra_score(model)
    # agenda.sort()
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

def traverse(h):
    # return [h] + sum([traverse(d) for d in h.deps], [])
    yield h
    for d in h.deps:
        for dd in traverse(d):
            yield dd

def get_extensions(model, candidates, agenda, h):
    for hsq in agenda:
        if not hsq:
            hsq_prefix, hsq_suffix = (), ()
        else:
            i = hsq.index(h)
            hsq_prefix, hsq_suffix = hsq[:i], hsq[i + 1:]
        for dsq in candidates[h]:
            nsq = Sequence(hsq_prefix + dsq + hsq_suffix)
            nsq.score = hsq.score + dsq.score
            # nsq.global_score = hsq.score + dsq.score + nsq.get_global_score(model)
            yield nsq
#################################

# evaluations

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
def bleu(sq):
    gold = sorted(sq)
    pred = list(sq)
    return (precision(ngram(gold, 2), ngram(pred, 2))\
                * precision(ngram(gold, 3), ngram(pred, 3))\
                * precision(ngram(gold, 4), ngram(pred, 4))) ** 0.25 


if __name__ == '__main__':
    if sys.argv[1] == '-train':
        train_file = sys.argv[2]
        model_file = sys.argv[3]
        t0 = time()
        model = train(train_file, model_file, 10, 1)
        print 'time used:', time() - t0
    elif sys.argv[1] == '-test':
        test_file = sys.argv[2]
        model_file = sys.argv[3]
        output_file = sys.argv[4]
        model = Model(model_file)
        t0 = time()
        test(test_file, output_file, model, 10, 1)
        print 'time used:', time() - t0

