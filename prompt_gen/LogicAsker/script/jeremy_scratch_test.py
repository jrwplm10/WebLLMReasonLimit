
import LogicAsker

# From the example notebook:

#

# problems = ["inference", "contradiction", "unrelated"]
# logics = ["propositional", "predicate"]
# rule_categories = ["equivalent", "inference", "fallacy"]
# cases = []
# rule_dict = {"propositional equivalent": lib.PROPOSITIONAL_EQUIV_RULES,
#              "propositional inference": lib.PROPOSITIONAL_INFERENCE_RULES,
#              "propositional fallacy": lib.PROPOSITIONAL_FALLACY_RULES,
#              "predicate equivalent": lib.QUANTIFIER_EQUIV_RULES,
#              "predicate inference": lib.QUANTIFIER_INFERENCE_RULES,
#              "predicate fallacy": lib.QUANTIFIER_FALLACY_RULES}


# From logic_inference_lib.py:
# EXAMPLE_PROBLEM_TYPES = [
#     "1",
#     "2a", "2a-cont", "2a-empty",
#     "2b", "2b-cont", "2b-empty",
#     "3a", "3a-cont", "3a-premise", "3a-no", "3a-no-1",
#     "3a-unrelated",
#     "3b", "3b-cont", "3b-premise", "3b-no", "3b-no-1",
#     "3b-unrelated"]
def main():

    # Try all rules:
    # full_ruleset = LogicAsker.lib.ALL_INFERENCE_RULES

    # seems unstable; fails frequently!
    success = False
    failcount = 0

    while not success:
        try:


            cases = LogicAsker.gen_cases(n=20, type='3b', category="equivalent", length=2)
            success = True
        except ValueError as e:
            print(e)
            failcount += 1
            print("Failcount: " + str(failcount))

    print("Generated cases:")
    for c in cases:
        print(c[0])

    print("Done")

if __name__ == "__main__":
    main()