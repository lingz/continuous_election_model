from voter import Voter, Candidate
from multiprocessing import Process, Queue
import json
import sys
import os
import cProfile

verbose = False
step = False
detailed = False
profile = False
path = "./"
repeats = 1
cycle_count = 0
numThreads = 1

def main():
  global verbose, step, profile, detailed, repeats, path, numThreads
  nextArg = None
  numVoters = 0
  numCandidates = 0
  numRounds = 0
  for arg in sys.argv:
    if arg == "-v" or arg == "--verbose":
      verbose = True
    elif arg == "-s" or arg == "--step": 
      step = True
    elif arg == "-p" or arg == "--profile":
      profile = True
    elif arg == "-d" or arg == "--detailed":
      detailed = True
    elif arg in ["-n", "-c", "-r", "--repeats", "--path", "-t"]:
      nextArg = arg
    elif nextArg:
      if nextArg == "-n":
        numVoters = int(arg)
      elif nextArg == "-c":
        numCandidates = int(arg)
      elif nextArg == "-r":
        numRounds = int(arg)
      elif nextArg == "--repeats":
        repeats = int(arg)
      elif nextArg == "--path":
        path = arg
      elif nextArg == "-t":
        numThreads = int(arg)
      nextArg = None


  if not numVoters:
    numVoters = input("Please input the number of voters you would like: ")
  if not numCandidates:
    numCandidates = input("Please input the number of candidates: ")
  if not numRounds:
    numRounds = input("Please enter the number of rounds you would like: ")

  if verbose:
    print(numVoters, numCandidates, numRounds, verbose, step)

  if profile:
    cProfile.runctx('run_context(numVoters, numCandidates, numRounds)',\
        { "step": step,
          "verbose": verbose,
          "run_context": run_context,
          "vote_round": vote_round,
          "vote_sub_round": vote_sub_round,
          "cycle_count": cycle_count,
          "detailed": detailed},
        { "numVoters": numVoters,
          "numCandidates": numCandidates,
          "numRounds": numRounds,
          "run_context": run_context})
  else:
    run_experiment(numVoters, numCandidates, numRounds)

def start_process(numVoters, numCandidates, numRounds, i, repeats, result_queue):
  context = Run_Context(numVoters, numCandidates, numRounds, i, repeats, result_queue)
  context.run()

def run_experiment(numVoters, numCandidates, numRounds):
  global numThreads, repeats

  data = []
  # if numRounds is not a multiple of threads, make it so
  if repeats % numThreads:
    repeats = ((repeats / numThreads) + 1) * numThreads

  # build a queue to collect results
  result_queue = Queue(repeats)

  summary = {"parameters": 
      {
        "Voters": numVoters,
        "Candidates": numCandidates,
        "Rounds": numRounds,
        "Repeats": repeats
      }}
  if detailed:
    summary["data"] = data

  threads = []
  for i in xrange(numThreads):
    threads.append(Process(target=start_process, args=(numVoters, numCandidates, numRounds, i, repeats / numThreads, result_queue)))
  for thread in threads:
    thread.start()
  for thread in threads:
    thread.join()
  for i in xrange(repeats):
    data.append(result_queue.get(False))

  equilibrium_average = average(data, "average_to_equilibrium")
  equilibrium_variance = variance(data, equilibrium_average, "average_to_equilibrium")
  summary["average_to_equilibrium"] = {
        "value": equilibrium_average,
        "variance": equilibrium_variance
      }
  staying_power_average = [0] * numCandidates
  staying_power_variance = [0] * numCandidates
  for i in xrange(numCandidates):
    staying_power_average[i] = average(data, "staying_power", i)
    staying_power_variance[i] = variance(data, staying_power_average[i], "staying_power", i)
  summary["staying_power"] = {
        "value": staying_power_average,
        "variance": staying_power_variance
      }
  turnover_average = average(data, "turnover_average")
  turnover_variance = variance(data, turnover_average, "turnover_average")
  summary["turnover_average"] = {
        "value": turnover_average,
        "variance": turnover_variance
      }
  dump_path = os.path.join(path, "results_n%d_c%d_r%d.txt" % (numVoters, numCandidates, numRounds))
  with open(dump_path, "w") as f:
    json.dump(summary, f)
  print("Khalas")

class Run_Context():
  def __init__(self, numVoters, numCandidates, numRounds, threadNum, repeats, result_queue):
    print("Thread %d Initiliazed" % threadNum)
    self.numVoters = numVoters
    self.numCandidates = numCandidates
    self.numRounds = numRounds
    self.threadNum = threadNum
    self.repeats = repeats
    self.result_queue = result_queue

  def run(self):
    print("Thread %d Started" % self.threadNum)
    for i in xrange(self.repeats):
      self.experimentNum = i
      print("Thread %d - Experiment %d" % (self.threadNum, self.experimentNum))
      self.voters = [Candidate(i) if i < self.numCandidates else Voter() for i in xrange(self.numVoters)]
      if verbose:
        print("Candidate Data:")
        for i in xrange(self.numCandidates):
          print(self.voters[i])
      single_repeat_data = []
      single_summary = {}
      if detailed:
        single_summary["round_data"] = single_repeat_data
      for roundNum in xrange(self.numRounds):
        self.roundNum = roundNum
        print("Thread %d - Experiment %d - Round %d" % (self.threadNum, self.experimentNum, self.roundNum))
        single_repeat_data.append(self.vote_round())

      average_to_equilibrium = 0
      staying_power = [0] * self.numCandidates
      last_leader = None
      turnover_average = 0
      for datum in single_repeat_data:
        average_to_equilibrium = average_to_equilibrium + datum["sub_cycles"]
        leader = datum["leader"]
        staying_power[leader] += 1
        if leader != last_leader:
          last_leader = leader
          turnover_average += 1
      single_summary["average_to_equilibrium"] = 1.0 * average_to_equilibrium / self.numRounds
      staying_power.sort()
      single_summary["staying_power"] = map(lambda x: 1.0 * x / self.numRounds, staying_power[::-1])
      single_summary["turnover_average"] = 1.0 * turnover_average / self.numRounds
      self.result_queue.put(single_summary)

  def vote_sub_round(self):
    scores = [0 for x in xrange(self.numCandidates)]
    satisfactions = [0 for x in xrange(self.numCandidates)]
    last_leader = None
    for voter in self.voters:
      # get the scores and leader
      local_leader, local_scores = voter.cast_vote(self.voters, self.numCandidates)
      last_leader = local_leader
      scores[local_leader] += 1
      # sum the satisfactions
      satisfactions = [x + y for x, y in zip(local_scores, satisfactions)]


    leader = scores.index(max(scores))

    for index, score in enumerate(scores):
      candidate = self.voters[index]
      candidate.set_votes(score)

    if detailed:
      # normalize all satisfactions to between 0 and 1
      satisfactions = map(lambda x: x / self.numCandidates, satisfactions)

    # normalize all scores to be percentages
    scores = map(lambda x: 1.0 * x / self.numVoters, scores)

    satisfaction_population = satisfactions[leader]
    if verbose:
      print ("""
      Winner: %d
      Scores: %s
      Satisfactions: %s
      """ % (leader, scores, satisfactions))

    if step:
      raw_input("Continue?")

    # satisfaction_ultimate_leader is not complete yet, and we need
    if detailed:
      return {
            "leader": leader,
            "scores": scores,
            "satisfaction_population": satisfaction_population,
            "satisfactions": satisfactions
          }
    else:
      return {"leader": leader, "scores": scores}

  def vote_round(self):
    global cycle_count
    cycle_count += 1
    if verbose:
      print("Thread %d - Experiment %d - Round %d - Cycle %d" % (self.threadNum, self.experimentNum, self.roundNum, cycle_count))

    complete = False
    previous_scores = [0] * self.numCandidates
    sub_cycles_count = 0
    if detailed:
      datum = {
          "progress": []
          }
    else:
      datum = {}
    ultimate_leader = None
    sub_cycles_to_equilbrium = 0
    while (not complete):
      sub_cycles_count += 1
      if verbose:
        print "Thread %d - Experiment %d - Round %d - Cycle %d - Sub-Cycle %d:" % (self.threadNum, self.experimentNum, self.roundNum, cycle_count, sub_cycles_count)

      result = self.vote_sub_round()

      if detailed:
        datum["progress"].append(result)

      complete = all(result["scores"][i] == previous_scores[i] for i in xrange(self.numCandidates))
      previous_scores = result["scores"]

      if result["leader"] != ultimate_leader:
        ultimate_leader = result["leader"]
        sub_cycles_to_equilbrium = sub_cycles_count

      if complete:
        datum["leader"] = ultimate_leader
        datum["sub_cycles"] = sub_cycles_to_equilbrium
        if detailed:
          datum["satisfaction_population"] = result["satisfaction_population"]
          # we need to now generate the ultimate leader satisfactions
          for result_data in datum["progress"]:
            result_data["satisfaction_ultimate_leader"] = result_data["satisfactions"][ultimate_leader]
            del result_data["satisfactions"]


    # Shift for the next round
    map(lambda voter: voter.shift_preference(), self.voters)

    if step:
      raw_input("Start New Round?")
    return datum

def average(data, key1, key2 = None):
  average = 0
  for datum in data:
    if key2 != None:
      value = datum[key1][key2]
    else:
      value = datum[key1]
    average += value
  return 1.0 * average / len(data)

def variance(data, average, key1, key2 = None):
  variance = 0
  for datum in data:
    if key2 != None:
      value = datum[key1][key2]
    else:
      value = datum[key1]
    variance += (value - average) ** 2
  return 1.0 * variance / len(data)


if __name__ == "__main__":
  main()
