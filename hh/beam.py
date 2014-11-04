#!/usr/bin/env python
import optparse
import sys
import models
from collections import namedtuple

optparser = optparse.OptionParser()
optparser.add_option("-i", "--input", dest="input", default="data/input", help="File containing sentences to translate (default=data/input)")
optparser.add_option("-t", "--translation-model", dest="tm", default="data/tm", help="File containing translation model (default=data/tm)")
optparser.add_option("-l", "--language-model", dest="lm", default="data/lm", help="File containing ARPA-format language model (default=data/lm)")
optparser.add_option("-n", "--num_sentences", dest="num_sents", default=sys.maxint, type="int", help="Number of sentences to decode (default=no limit)")
optparser.add_option("-k", "--translations-per-phrase", dest="k", default=20, type="int", help="Limit on number of translations to consider per phrase (default=1)")
optparser.add_option("-s", "--heap-size", dest="s", default=1000, type="int", help="Maximum heap size (default=1)")
optparser.add_option("-d", "--disorder", dest="disord", default=3, type="int", help="Disorder limit (default=6)")
optparser.add_option("-w", "--beam width", dest="bwidth", default=10,  help="beamwidth")
optparser.add_option("-e", "--eta", dest="eta", default=0.0, type="float",  help="distortion penalty parameter variable")
optparser.add_option("-a", "--alpha", dest="alpha", default=1.0, type="float", help="weight for language model")
optparser.add_option("-b", "--beta", dest="beta", default=1.0, type="float", help="weight for translation model")
opts = optparser.parse_args()[0]

tm = models.TM(opts.tm, opts.k)
lm = models.LM(opts.lm)
french = [tuple(line.strip().split()) for line in open(opts.input).readlines()[:opts.num_sents]]
hypothesis = namedtuple("hypothesis", "lm_state, logprob, coverage, end, predecessor, phrase")

def bitmap(sequence):
    """ Generate a coverage bitmap for a sequence of indexes """
    return reduce(lambda x,y: x|y, map(lambda i: long('1'+'0'*i,2), sequence), 0)

def onbits(b):
    """ Count number of on bits in a bitmap """
    return 0 if b==0 else (1 if b&1==1 else 0) + onbits(b>>1)

def prefix1bits(b):
    """ Count number of bits encountered before first 0 """
    return 0 if b&1==0 else 1+prefix1bits(b>>1)

def last1bit(b):
    """ Return index of highest order bit that is on """
    return 0 if b==0 else 1+last1bit(b>>1)

# def stateeq(state1, state2):
#     return (state1.lm_state == state2.lm_state) and (state1.end == state2.end) and (state1.coverage == state2.coverage)

def main():
    # tm should translate unknown words as-is with probability 1
    for word in set(sum(french,())):
        if (word,) not in tm:
            tm[(word,)] = [models.phrase(word, 0.0)]

    total_prob = 0
    sys.stderr.write("Decoding %s...\n" % (opts.input,))
    for idx,f in enumerate(french):
        initial_hypothesis = hypothesis(lm.begin(), 0.0, 0, 0, None, None)
        heaps = [{} for _ in f] + [{}]
        heaps[0][lm.begin(), 0, 0] = initial_hypothesis
        for i, heap in enumerate(heaps[:-1]):
            # maintain beam heap
            front_item = sorted(heap.itervalues(), key=lambda h: -h.logprob)[0]
            for k in heap.keys():
                 if heap[k].logprob < front_item.logprob - opts.bwidth:
                    del heap[k]

            for h in sorted(heap.itervalues(),key=lambda h: -h.logprob): #[:opts.s]: # prune
                fopen = prefix1bits(h.coverage)
                for j in xrange(fopen,min(fopen+1+opts.disord, len(f)+1)):
                    for k in xrange(j+1, len(f)+1):
                        if f[j:k] in tm:
                            if (h.coverage & bitmap(range(j, k))) == 0:
                                for phrase in tm[f[j:k]]:
                                    lm_prob = 0
                                    lm_state = h.lm_state
                                    for word in phrase.english.split():
                                        (lm_state, prob) = lm.score(lm_state, word)
                                        lm_prob += prob
                                    lm_prob += lm.end(lm_state) if k == len(f) else 0.0
                                    coverage = h.coverage | bitmap(range(j, k))
                                    logprob = h.logprob + opts.alpha*lm_prob + opts.beta*phrase.logprob + opts.eta*abs(h.end + 1 - j)
                                    
                                    new_hypothesis = hypothesis(lm_state, logprob, coverage, k, h, phrase)

                                    # add to heap
                                    num = onbits(coverage)
                                    if (lm_state, coverage, k) not in heaps[num] or new_hypothesis.logprob > heaps[num][lm_state, coverage, k].logprob:
                                            heaps[num][lm_state, coverage, k] = new_hypothesis


        winner = max(heaps[-1].itervalues(), key=lambda h: h.logprob)
        def extract_english(h): 
            return "" if h.predecessor is None else "%s%s " % (extract_english(h.predecessor), h.phrase.english)
        out = extract_english(winner)
        print out
        sys.stderr.write("#{0}:{2} - {1}\n".format(idx, out , winner.logprob))
        total_prob += winner.logprob

        # if opts.verbose:
        #     def extract_tm_logprob(h):
        #         return 0.0 if h.predecessor is None else h.phrase.logprob + extract_tm_logprob(h.predecessor)
        #     tm_logprob = extract_tm_logprob(winner)
        #     sys.stderr.write("LM = %f, TM = %f, Total = %f\n" % 
        #         (winner.logprob - tm_logprob, tm_logprob, winner.logprob))
    sys.stderr.write("Total score: {0}\n".format(total_prob))


if __name__ == "__main__":
    main()

