import json
import sys

for filename in sys.argv:
  if ".txt" in filename:
    with open(filename) as f:
      data = json.loads(f.read())
      with open(filename.replace(".txt", "-tabulated.csv"), "w") as ff:
        ff.write("Candidates,%d\n" % data["parameters"]["Candidates"])
        ff.write("Population,%d\n" % data["parameters"]["Voters"])
        ff.write("Rounds,%d\n" % data["parameters"]["Rounds"])
        ff.write("Equilibrium Value,%f\n" % data["average_to_equilibrium"]["value"])
        ff.write("Equilibrium Variance,%f\n" % data["average_to_equilibrium"]["variance"])
        ff.write("Turnover Value,%f\n" % data["turnover_average"]["value"])
        ff.write("Turnover Variance,%f\n" % data["turnover_average"]["variance"])
        ff.write("Staying Power Value,Staying Power Variance\n")
        for i in xrange(len(data["staying_power"]["value"])):
          ff.write("%f,%f\n" % (data["staying_power"]["value"][i], data["staying_power"]["variance"][i]))
