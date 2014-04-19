from voter import Voter, Candidate
import yaml

verbose = False
step = False
cycle_count = 0

def main():
  #numVoters = input("Please input the number of voters you would like: ")
  #numCandidates = input("Please input the number of candidates: ")
  #numRounds = input("Please enter the number of rounds you would like: ")
  numVoters = 1000000
  numCandidates = 5
  numRounds = 100
  data = []
  voters = [Candidate(i) if i < numCandidates else Voter() for i in xrange(numVoters)]
  print("Candidate Data")
  for i in xrange(numCandidates):
    if verbose:
      print(voters[i])
  for round in xrange(numRounds):
    data.append(vote_round(voters, numCandidates))
  with open("results.txt", "w") as f:
    yaml.dump(data, f)
  print("finished")

def vote_sub_round(voters, numCandidates):
  scores = [0 for x in xrange(numCandidates)]
  satisfactions = [0 for x in xrange(numCandidates)]
  for voter in voters:
    # get the scores and winner
    local_winner, local_scores = voter.cast_vote(voters, numCandidates)
    scores[local_winner] += 1
    # sum the satisfactions
    satisfactions = [x + y for x, y in zip(local_scores, satisfactions)]
  winner = scores.index(max(scores))

  # normalize all scores to be percentages
  scores = map(lambda x: x / len(voters), scores)

  # normalize all satisfactions to between 0 and 1
  satisfactions = map(lambda x: x / numCandidates, satisfactions)

  satisfaction_population = satisfactions[winner]
  if verbose:
    print ("""
    Winner: %d
    Scores: %s
    Satisfactions: %s
    """ % (winner, scores, satisfactions))

  for index, score in enumerate(scores):
    candidate = voters[index]
    candidate.set_votes(score)

  if step:
    raw_input("Continue?")

  # satisfaction_ultimate_leader is not complete yet, and we need
  return {
        "winner": winner,
        "scores": scores,
        "satisfaction_population": satisfaction_population,
        "satisfactions": satisfactions
      }

def vote_round(voters, numCandidates):
  global cycle_count
  cycle_count += 1
  print("New Cycle %d" % cycle_count)

  complete = False
  previous_scores = [0] * numCandidates
  sub_rounds_count = 0
  datum = {
      "progress": []
      }
  while (not complete):
    sub_rounds_count += 1
    if verbose:
      print "Sub-Cycle %d:" % sub_rounds_count
    result = vote_sub_round(voters, numCandidates)
    datum["progress"].append(result)
    complete = all(result["scores"][i] == previous_scores[i] for i in xrange(numCandidates))
    previous_scores = result["scores"]
    if complete:
      datum["winner"] = result["winner"]
      datum["steps"] = sub_rounds_count
      datum["satisfaction_population"] = result["satisfaction_population"]
      # we need to now generate the ultimate leader satisfactions
      #for result_data in datum["progress"]:
        #result_data["satisfaction_ultimate_leader"] = 


  # Shift for the next round
  map(lambda voter: voter.shift_preference(), voters)

  if step:
    raw_input("Start New Round?")
  return datum

if __name__ == "__main__":
  main()
