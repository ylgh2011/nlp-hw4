import os
import sys
import optparse
import copy
from subprocess import call

steps = {
	'-a': 0.1,
	'-b': 0.1,
}

decoder = 'baseline.py'
scorer = 'score-decoder.py'
logFileName = 'localSearch_log.log.ignore'


def getNeighbors(state):
	neis = []
	for item in steps:
		state[item] += steps[item];
		neis.append(copy.deepcopy(state))
		state[item] -= steps[item];
		state[item] -= steps[item];
		neis.append(copy.deepcopy(state))
		state[item] += steps[item];
	return neis


def getScore(state):
	command = 'python ' + decoder + ' -i data/input2 '
	for key in state:
		command += key + ' ' + str(state[key]) + ' '
	command += '| python ' + scorer + ' -i data/input2 > tempLog.ignore'
	print '#############################################################################'
	print '############################## getScore #####################################'
	print command
	os.system(command)

	symbolSentence = 'Total corpus log probability (LM+TM):'
	with file('tempLog.ignore') as f:
		for line in f.readlines():
			if line[0:len(symbolSentence)] == symbolSentence:
				return float(line.split()[5])

	os.system('rm tempLog.ignore')
	return 0


def writeToLog(s):
	with open(logFileName, 'a+') as f:
		f.write(s + '\n')


def main():
	optparser = optparse.OptionParser()
	optparser.add_option("-d", "--decoder", dest="decoder", default="baseline.py", help="Python script to decode")
	optparser.add_option("-s", "--scorer", dest="scorer", default="score-decoder.py", help="Python script to evaluate the output")
	opts = optparser.parse_args()[0]

	decoder = opts.decoder
	scorer = opts.scorer

	initPara = {
		'-a': 1.1,
		'-b': 1,
		'-s': 100,
		'-k': 30,
		'-w': 10
	}

	curState = copy.deepcopy(initPara)
	curScore = getScore(curState)
	writeToLog("### Init CurState - Score:" + str(curScore) + ", State:" + str(curState))
	while True:
		bestState = copy.deepcopy(curState)
		bestScore = curScore

		for neiState in getNeighbors(curState):
			neiScore = getScore(neiState)
			writeToLog("### Neighbor - Score:" + str(neiScore) + ", State:" + str(neiState))
			if neiScore > bestScore:
				bestState = copy.deepcopy(neiState)
				bestScore = neiScore

		if bestScore == curScore:
			break
		else:
			curState = copy.deepcopy(bestState)
			curScore = bestScore
			writeToLog("### Update CurState - Score:" + str(curScore) + ", State:" + str(curState))

	writeToLog("### Last CurState - Score:" + str(curScore) + ", State:" + str(curState))

if __name__ == "__main__":
    main()












