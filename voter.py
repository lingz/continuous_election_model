import random

class Voter():
  def __init__(self):
    self.cannonical_preference = random.random()
    self.current_preference = self.cannonical_preference

  def shift_preference(self):
    shifted_preference = random.normalvariate(self.cannonical_preference, 0.1)
    if shifted_preference > 1:
      shifted_preference = 1
    elif shifted_preference < 0:
      shifted_preference = 0
    self.current_preference = shifted_preference
    return shifted_preference

  def get_satisfaction(self, candidate):
    distance = candidate.current_preference - self.current_preference
    if distance < 0:
      distance *= -1
    if distance == 0:
      distance += 0.001
    satisfaction = candidate.votes / distance
    return satisfaction

  def cast_vote(self, voters, numCandidates):
    max_score = 0
    max_candidate = -1
    scores = [0] * numCandidates
    for index in xrange(numCandidates):
      candidate = voters[index]
      score = self.get_satisfaction(candidate)
      if score > max_score:
        max_score = score
        max_candidate = index
      scores[index] = score
    scores = map(lambda score: score / max_score, scores)
    return (max_candidate, scores)

  def __str__(self):
    return "Voter\nCanonical Preference: %.2f\nCurrent Preference: %.2f\n" %\
      (self.cannonical_preference, self.current_preference)

class Candidate(Voter):
  def __init__(self, index):
    Voter.__init__(self)
    self.index = index
    self.votes = 1

  def get_satisfaction(self, candidate):
    if candidate == self:
      return 1
    else:
      return 0

  def cast_vote(self, voters, numCandidates):
    scores = [1 if x == self.index else 0 for x in xrange(numCandidates)]
    return (self.index, scores)

  def set_votes(self, newVotes):
    self.votes = newVotes
