import os
import sys
import optparse
import copy
from subprocess import call

steps = {}

initPara = {
	'-a': 1.0,
	'-b': 1.0,
	'-s': 100,
	'-k': 20,
	'-d': 10
}

decoder = 'baseline.py'
scorer = 'score-decoder.py'


def getNeighbors(state):
	neis = []
	for item in steps:
		state[item] += steps[item];
		neis.append(copy.deepcopy(state))
		state[item] -= steps[item];
		
		state[item] -= steps[item];
		neis.append(copy.deepcopy(state))
		state[item] += steps[item];

		state[item] += steps[item] * 2;
		neis.append(copy.deepcopy(state))
		state[item] -= steps[item] * 2;

		state[item] -= steps[item] * 2;
		neis.append(copy.deepcopy(state))
		state[item] += steps[item] * 2;

		state[item] += steps[item] * 4;
		neis.append(copy.deepcopy(state))
		state[item] -= steps[item] * 4;

		state[item] -= steps[item] * 4;
		neis.append(copy.deepcopy(state))
		state[item] += steps[item] * 4;

	return neis


stateScore = {}
def getScore(state):
	print '#############################################################################'
	print '############################## inside getScore() ############################'
	stateTuple = tuple(state.keys() + state.values())
	if stateTuple in stateScore:
		print str(stateTuple) + ' already exist: ' + str(stateScore[stateTuple])
		return stateScore[stateTuple]
	

	command = 'python ' + decoder + ' -i data/input --mute 1 '
	for key in state:
		command += key + ' ' + str(state[key]) + ' '
	command += '| python ' + scorer + ' -i data/input > tempLog.ignore'
	print command
	os.system(command)

	score = 0
	symbolSentence = 'Total corpus log probability (LM+TM):'
	with file('tempLog.ignore') as f:
		for line in f.readlines():
			if line[0:len(symbolSentence)] == symbolSentence:
				score = float(line.split()[5])
				stateScore[stateTuple] = score
				break

	os.system('rm tempLog.ignore')
	return score


def writeToLog(logFileName, s):
	with open(logFileName, 'a+') as f:
		f.write(s + '\n')

def fillInPair(dic, item):
	kv = item.split(':')
	try:
		dic[kv[0]] = int(kv[1])
	except ValueError:
		dic[kv[0]] = float(kv[1])


def main():
	optparser = optparse.OptionParser()
	optparser.add_option("-l", "--log", dest="log", default="localSearch_log.ignore", help="log to store the output")
	optparser.add_option("-p", "--init_parameters", dest="init_parameters", default="-a:1.0,-b:1.0,-s:100,-k:20,-d:10", help="initial prarameters")
	optparser.add_option("-t", "--steps", dest="steps", default="-a:0.1,-b:0.1", help="steps for dimensions of local search")
	opts = optparser.parse_args()[0]

	logFileName = opts.log

	# if os.path.isfile('stateScore.json'):
	# 	with open('stateScore.json', 'r') as f:
	# 		sc = json.loads(f)
	# 		for key in sc:
	# 			stateScore[key] = sc[key]

	for item in opts.init_parameters.split(','):
		fillInPair(initPara, item)

	for item in opts.steps.split(','):
		fillInPair(steps, item)
	
	print "logFileName: " + logFileName
	print "initPara: " + str(initPara)
	print "steps: " + str(steps)
	print "stateScore: " + str(stateScore)
	# exit()

	curState = copy.deepcopy(initPara)
	curScore = getScore(curState)
	writeToLog(logFileName, "### Init CurState - Score:" + str(curScore) + ", State:" + str(curState))
	while True:
		bestState = copy.deepcopy(curState)
		bestScore = curScore

		for neiState in getNeighbors(curState):
			neiScore = getScore(neiState)
			writeToLog(logFileName, "### Neighbor - Score:" + str(neiScore) + ", State:" + str(neiState))
			if neiScore >= bestScore:
				bestState = copy.deepcopy(neiState)
				bestScore = neiScore

		if bestScore == curScore:
			break
		else:
			curState = copy.deepcopy(bestState)
			curScore = bestScore
			writeToLog(logFileName, "### Update CurState - Score:" + str(curScore) + ", State:" + str(curState))

	writeToLog(logFileName, "### Last CurState - Score:" + str(curScore) + ", State:" + str(curState))
	writeToLog(logFileName, "$ stateScore: " + str(stateScore))

	# with open('stateScore.json', 'w') as f:
	# 	f.write(json.dumps(stateScore))

if __name__ == "__main__":
    main()












