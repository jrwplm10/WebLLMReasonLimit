# Adapted from testing_prompts_from_pickle.py, heavy modifications.
import datetime
import pickle
from openai import OpenAI
import threading
import os
import json
import time
import random
from functools import partial
import re

import multiprocessing

# Put your api key path here.
with open("/home/jeremy/Documents/WPI_Spring_25/CS_555/Project/OpenAI_Api_free", 'r') as f:
    API_KEY = f.readline()
    API_KEY = API_KEY.rstrip('\n')


# A scenario augmentation function.
NUM_DUPS = 3  # not too many...
def dup_answer_prem(premise_list, people_list, question):
    # Extract people in question statement.
    important_people = get_question_subjects(question)

    # find all predicates that have one of the important people.
    duppable_premises = []
    for p in premise_list:
        prem_tokens = re.split("[ ,.]+", p)
        for im in important_people:
            if im in prem_tokens:
                duppable_premises.append(p)
                one_match = True
                break

    # Randomly insert duppable premises randomly.
    for a in range(NUM_DUPS):
        rand_prem = random.choice(duppable_premises)
        rand_pos = random.choice(range(len(premise_list)+1))
        premise_list.insert(rand_pos, rand_prem)

    return premise_list, people_list

def get_question_subjects(question):
    question_tokens = re.split("[ ,.]+", question)
    p1 = question_tokens[0]
    important_people = [p1]

    p2 = question_tokens[-1]
    if p2.lower() != 'female' and p2.lower() != 'male':  # The only unary predicates that we don't count.
        important_people.append(p2)

    return important_people

# Really simple string replacement.
def negate(relation_str):
    return relation_str.replace(" is ", " is not ")

def build_prompts(scenario, scenario_augmenter=None, factor_redundancy=True, negate_question_count=0, random_and_count=0):

    # prompts = [part + scenario['easy_infer'] + "."]

    question_set = scenario['hard_infer_list']

    # Redundancy is in the question; does it relate to anyone in premises?

    prompts = []
    for q_idx, question in enumerate(question_set):

        premise_list = scenario['premises']
        people_list = scenario['people']

        # Allow some sort of filtering/modification to occur
        if scenario_augmenter is not None:
            premise_list, people_list = scenario_augmenter(premise_list, people_list, question)

        # if we want to make sure the question premise has some sort of redundancy associated with it.
        if factor_redundancy:
            redundancy_dict = build_two_way_redundancy_dict(premise_list)
            # Check question keys; any redundant info related directly to the question?

            important_people = get_question_subjects(question)
            some_match = False
            for im in important_people:
                for k in redundancy_dict.keys():
                    if im == k[0] or im == k[1]:
                        # has to actually be redundant.
                        if redundancy_dict[k] > 1:
                            some_match = True
                            break

                if some_match:
                    break

            if not some_match:
                continue  # Skip this question.

        part = "The following scenario describes a family tree. "
        # part += "It may contain redundant relationships, but the described relationships described are correct. "
        # part += "There is a lot of complexity in this family tree. " # Silly test?
        part += "You may assume siblings always share the same parents. "
        # part += "The people in this scenario are "
        # for name in people_list:
        #     part = part + name + ", "
        # part = part[:-2] + ". "

        for premises in premise_list:
            part = part + premises + ". "

        # part += "You may assume there are no step-relationships unless explicitly mentioned. "

        part = part + "Is this statement true:"

        if random_and_count > 0:
            # select random other question
            and_set = [question]
            other_q_choices = question_set[:q_idx] + question_set[(q_idx+1):]

            num_to_sample = random_and_count
            if num_to_sample > len(other_q_choices):
                num_to_sample = len(other_q_choices)

            others = random.sample(other_q_choices, k=num_to_sample)
            and_set = and_set + others

            # for a in range(random_and_count):
            #     other_q = question
            #     while other_q in and_set:
            #         other_q = random.choice(question_set)
            #     and_set.append(other_q)

            # randomly negate in the and_set
            if negate_question_count > 0:
                num_to_negate = negate_question_count
                if num_to_negate > len(and_set):
                    num_to_negate = and_set
                idx_rand_negate = random.sample(range(len(and_set)), k=num_to_negate)
                for i in idx_rand_negate:
                    and_set[i] = negate(and_set[i])

            prompt_str = part
            for idx in range(len(and_set)):
                prompt_str += " " + and_set[idx]
                if idx < (len(and_set)-1):
                    prompt_str += " and"

            prompt_str += "."
            prompts.append(prompt_str)

        elif negate_question_count > 0:
            prompts.append(part + " " + negate(question) + ".")
        else:
            prompts.append(part + " " + question + ".")

    return prompts

# For multiprocessing.
def query_completion(api_key, model, dev_prompt, question_scenario):
    openai_client = OpenAI(api_key=api_key)

    completion = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "developer",
             "content": dev_prompt},
            {
                "role": "user",
                "content": question_scenario,
            },
        ],
    )

    answer = completion.choices[0].message.content
    # print(answer) # Making sure it works!
    # not sure if needed
    # time.sleep(0.1)

    return answer

def clear_data(dicts_list):
    for d in dicts_list:
        d['hard_infer_successes'] = [None] * len(d['hard_infer_responses'])
        d['hard_infer_responses'] = [None for x in d['hard_infer_responses']]


# Functions for filtering scenarios
# Specific cases exist that break the logic more consistently?

# True if any redundancy, false otherwise
def any_one_way_redundancy(premise_strings_list):
    arg_pairings = {}
    for premise in premise_strings_list:
        tokens = re.split("[ ,.]+", premise)
        arg1 = tokens[0]
        arg2 = tokens[-1]
        if not (arg1, arg2) in arg_pairings:
            arg_pairings[(arg1, arg2)] = 1
        else:
            arg_pairings[(arg1, arg2)] += 1

    for key_pairing in arg_pairings.keys():
        if arg_pairings[key_pairing] > 1:
            return True

    return False

def build_two_way_redundancy_dict(premise_strings_list):
    arg_pairings = {}
    for premise in premise_strings_list:
        tokens = re.split("[ ,.]+", premise)
        arg1 = tokens[0]
        arg2 = tokens[-1]

        # check both orders.
        order_1 = ((arg1, arg2) in arg_pairings)
        order_2 = ((arg2, arg1) in arg_pairings)

        if (not order_1) and (not order_2):
            arg_pairings[(arg1, arg2)] = 1 # Favor order_1
        else:
            if order_1:
                arg_pairings[(arg1, arg2)] += 1
            else:
                arg_pairings[(arg2, arg1)] += 1

    return arg_pairings

# Scenarios that have redundant information in them.
def specifically_redundant(scenarios_list):
    retlist = []
    for s in scenarios_list:
        if any_one_way_redundancy(s['premises']):
            retlist.append(s)

    return retlist

# Measure rate of this group.
def specifically_not_redundant(scenarios_list):
    retlist = []
    for s in scenarios_list:
        if not any_one_way_redundancy(s['premises']):
            retlist.append(s)

    return retlist


def main(scenario_path, num_processes=12):
    # sequential evaluation.
    openai_client = OpenAI(api_key=API_KEY)
    model = "gpt-4o"

    dev_prompt = ("You are being prompted with a scenario. "
              "Your job is to determine the answer to the question as 'yes', 'no', or in the case that the answer is unknown, 'unknown'. "
              "Provide a brief paragraph explaining your reasoning for your answer, but it is critical that this paragraph is brief and contained in one single paragraph with no line breaks. "
              "End your response with 'yes', 'no', or 'unknown', specifically structured as 'Final Answer = [Your Answer]'. "
              "Your response should ONLY contain a paragraph of reasoning and a final answer.")

    # message_role = "user"
    # message_role = "developer"
    with open(scenario_path, 'rb') as f:
        scenarios = pickle.load(f)

    # Clear data real quick.
    clear_data(scenarios)

    print("Number of unique scenarios: " + str(len(scenarios)))

    scenarios = specifically_redundant(scenarios)
    # scenarios = specifically_not_redundant(scenarios)
    # Number of unique scenarios: 1000
    # Number of unique scenarios, after filtering: 653 -> Rules out 35% of samples actually.

    print("Number of unique scenarios, after filtering: " + str(len(scenarios)))

    print("Starting pool evaluation")
    starttime = datetime.datetime.now()

    # Build prompts.
    # Choose a random scenario
    hard_infer_indices = []
    prompts = []
    scenario_indices = []
    for idx, s in enumerate(scenarios):
        # all_scenarios = build_prompts(s, scenario_augmenter=dup_answer_prem)
        # Generate scenarios, make some changes
        all_scenarios = build_prompts(s, scenario_augmenter=None, factor_redundancy=True, negate_question_count=1, random_and_count=2)
        # hard_infer_indices.append(random.choice(range(len(all_scenarios[1:]))))
        # prompts.append(all_scenarios[hard_infer_indices[-1]])

        # ALL QUESTIONS MODE~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Do ALL hard questions; try to find a pattern!
        # This requires annoying indexing to do with multiprocessing though...
        hard_infer_indices = hard_infer_indices + list(range(len(all_scenarios)))
        prompts = prompts + list(all_scenarios)
        scenario_indices = scenario_indices + [idx] * len(all_scenarios)
        # The actual prompts we're using...
        s['hard_infer_tested_prompts'] = all_scenarios

    print("Number of questions total to try: " + str(len(prompts)))

    resample_size = 500
    # resample_size = 750
    if len(prompts) > resample_size:

        resample_idxs = list(range(len(scenario_indices)))

        print("Subsample to " + str(resample_size) + ": ")
        # For limiting max evaluations done at once.
        resample_idxs = random.sample(resample_idxs, k=resample_size)

        hard_infer_indices = [hard_infer_indices[x] for x in resample_idxs]
        prompts = [prompts[x] for x in resample_idxs]
        scenario_indices = [scenario_indices[x] for x in resample_idxs]

    multi_pool = multiprocessing.Pool()

    scenario_answers = multi_pool.map(partial(query_completion, API_KEY, model, dev_prompt), prompts)

    multi_pool.close()
    multi_pool.join()

    # evaluate answers
    # for idx, s in enumerate(scenarios):
    failure_count = 0
    equivocate_count = 0
    yes_count = 0
    for idx in range(len(scenario_indices)):
        s = scenarios[scenario_indices[idx]]
        hard_idx = hard_infer_indices[idx]
        answer = scenario_answers[idx]
        if 'hard_infer_successes' not in s:
            # initialize.
            s['hard_infer_successes'] = [None] * len(s['hard_infer_responses'])

        s['hard_infer_responses'][hard_idx] = answer

        if answer[-4:-1].lower() == "yes":
            # print("Success")
            s['hard_infer_successes'][hard_idx] = "yes"
            yes_count += 1
        elif answer[-3:-1].lower() == "no":
            # Parse failures will go here too.
            s['hard_infer_successes'][hard_idx] = "no"
            failure_count += 1
            # print("Hard Failure")
        else:
            s['hard_infer_successes'][hard_idx] = "unknown"
            equivocate_count += 1
            # print("Equivocation Failure")

    # Slow!
    # print("Starting sequential evaluation...")
    # starttime = datetime.datetime.now()
    # # sequential for now
    # for idx, s in enumerate(scenarios):
    #     # if idx % 10 == 0:
    #     #     # save partial progress!
    #     #     with open(scenario_path, 'wb') as f:
    #     #         pickle.dump(scenarios, f)
    #     print("Idx: " + str(idx) + "...")
    #
    #     all_scenarios = build_prompts(s)
    #     # choose random hard.
    #     # scenario_idx = random.choice(range(len(all_scenarios[1:])))
    #     # question_scenario = all_scenarios[scenario_idx+1]
    #     scenario_idx = random.choice(range(len(all_scenarios)))
    #     question_scenario = all_scenarios[scenario_idx]
    #
    #     completion = openai_client.chat.completions.create(
    #         model=model,
    #         messages=[
    #             {"role": "developer",
    #              "content": dev_prompt},
    #             {
    #                 "role": "user",
    #                 "content": question_scenario,
    #             },
    #         ],
    #     )
    #
    #     answer = completion.choices[0].message.content
    #     if 'hard_infer_successes' not in s:
    #         # initialize.
    #         s['hard_infer_successes'] = [None] * len(s['hard_infer_responses'])
    #
    #     s['hard_infer_responses'][scenario_idx] = answer
    #
    #     if answer[-4:-1].lower() == "yes":
    #         print("Success")
    #         s['hard_infer_successes'][scenario_idx] = "yes"
    #     elif answer[-3:-1].lower() == "no":
    #         # Parse failures will go here too.
    #         s['hard_infer_successes'][scenario_idx] = "no"
    #         print("Hard Failure")
    #     else:
    #         s['hard_infer_successes'][scenario_idx] = "unknown"
    #         print("Equivocation Failure")
    #
    #     time.sleep(0.1)

    # write results.
    with open(scenario_path, 'wb') as f:
        pickle.dump(scenarios, f)

    # make json version
    with open(os.path.splitext(scenario_path)[0] + '.json', 'w') as f2:
        json.dump(scenarios, f2)

    elapsed = datetime.datetime.now() - starttime
    print("Elapsed time: " + str(elapsed.total_seconds()))
    # Time to beat: 100 seconds for 100 scenarios in sequential mode...
    # mp with 100 scenarios did 17 secs for 12 processes...
    # 88 seconds with 647 scenarios for 40 processes. Sufficient performance.

    print("Number of scenarios total tried: " + str(len(prompts)))
    print("Yes count: " + str(yes_count))
    print("Failure count: " + str(failure_count))
    print("Equivocation count: " + str(equivocate_count))
    print("Failure + Equivocation proportion: " + str((failure_count+equivocate_count)/len(prompts)))
    print("Yes + Equivocation proportion: " + str((yes_count+equivocate_count)/len(prompts)))

def newlineify(in_str):
    # make it not a pain to read.
    return in_str.replace(". ", ".\n")

def analyze_results(scenario_path, expect_negative=True):
    # TODO: Need to put in the updated prompts in the pickle file somehow...
    with open(scenario_path, 'rb') as f:
        scenarios = pickle.load(f)

    num_scenarios = len(scenarios)
    # print("Total number of scenarios: " + str(len(scenarios)))

    count_scenario_tests = 0
    count_incorrect = 0

    examples = []
    for scenario in scenarios:
        # Build prompts.
        # all_scenarios = build_prompts(scenario)
        # look at hard_infer responses

        # s['hard_infer_tested_prompts']
        for idx, result in enumerate(scenario['hard_infer_successes']):
            # We only answered one for now.
            if result is None:
                continue

            count_scenario_tests += 1

            if expect_negative:
                if result != "no":
                    count_incorrect += 1
                    examples.append({
                        'prompt': scenario['hard_infer_tested_prompts'][idx],
                        'answer': scenario['hard_infer_responses'][idx]
                    })
            else:
                if result != "yes":
                    count_incorrect += 1
                    examples.append({
                        'prompt': scenario['hard_infer_tested_prompts'][idx],
                        'answer': scenario['hard_infer_responses'][idx]
                    })

    print("Total number of questions asked: " + str(count_scenario_tests))
    print("Num incorrect: " + str(count_incorrect))
    prop_incorrect = count_incorrect / count_scenario_tests
    print("Proportion incorrect: " + str(prop_incorrect))

    with open("incorrect_examples.txt", 'w') as f2:
        f2.write('Listed examples:\n')
        for ex in examples:
            f2.write('PROMPT~~~~~~~~~~~~~~\n')
            f2.write(newlineify(ex['prompt']) + '\n')
            f2.write('ANSWER~~~~~~~~~~~~~~\n')
            f2.write(newlineify(ex['answer']) + '\n')
            f2.write('\n')

    # with open("examples.json", 'w') as f2:
    #     json.dump(examples, f2)

    # Analysis:
    # Number of people?
    # Number of relationships

    print("Done")

if __name__ == '__main__':
    # main('test_mini.pickle', num_processes=40)
    # analyze_results('test_mini.pickle')
    main('test_moderate.pickle', num_processes=25)
    # analyze_results('test_moderate.pickle', expect_negative=True)

    # initially: 11% incorrect rate
    # fix 1:
    # 8% incorrect rate
    # fix 2; prompt has more information on edge cases:
    # 5% incorrect rate
    # fix 3; reword prompt, fix siblings being parents again.
    # 1% incorrect rate (BAD!)
    # Test all possible "hard" questions:
    # 0.9% incorrect rate (BAD!)
    # -If I rerun, do the same examples fail?
    # Unstable: only 0.3% (2/647) were incorrect this time... very unstable...
    # Run #3: Looking for consistent logic issues.
    # 0.9% again. - No consistency between specific scenarios it seems. Base randomness is affecting the output...

    # using moderate dataset, looking specifically at redundant info provided.
    # 1.6% roughly. Slight improvement?

    # trying premise duplication
    # Exactly the same proportion: 1.6% -> failure!

    # opposite: Look at scenarios without redundancy; is it even worse?
    # Failure rate is actually 0.2% -> Significantly lower! Redundancy is actually causing some effect
    # rerun 2x...
    # Failure rate is actually zero -> so redundancy is inducing some weak effect!

    # Redundancy question filter test...
    # Actually 2% failure rate... improvement? Not sure.
    # Filtering reduced from 4704 to 4030 questions, so it is narrowig it down.
    # Rerun: 1.6%... margin of error probably.

    # Silly: Add "confusing sentences" into the prompt.
    # Run 1x: 2.2%
    # Run 2x: 1%
    # Not extremely effective.

    # Don't mention the people:
    # Interestingly: Increases failure rate a bit?
    # Run 1x: 0.037 -> 3.7%
    # Run 2x: 0.02 -> 2%
    # Run 3x: 0.024

    # Actually the most promising so far... small change.

    # remove statement on redundant relationships.
    # Run 1x: Failure + Equivocation proportion: 0.030666666666666665
    # Run 2x: Failure + Equivocation proportion: 0.029333333333333333

    # Negate every question statement:
    # Run 1x: Yes + Equivocation proportion: 0.026
    # Run 2x: Yes + Equivocation proportion: 0.024

    # Add "and" and randomly select another statement:
    # Detectable improvement
    # Run 1x: Failure + Equivocation proportion: 0.056
    # Run 2x (w/750 samples): Failure + Equivocation proportion: 0.058666666666666666
    # Run 3x (w/750 samples): Failure + Equivocation proportion: 0.04666666666666667

    # Try 2 "ands" - 3 statements. Whenever possible.
    # More ands -> More difference
    # Run 1x: Failure + Equivocation proportion: 0.088
    # Run 2x: Failure + Equivocation proportion: 0.062

    # Triple and, 1 negation.
    # Expect this to be similar to normal triple and.
    # Run 1x: Yes + Equivocation proportion: 0.044; Elapsed time: 137.332191 (50 processes)
    # Run 2x: Yes + Equivocation proportion: 0.054; Elapsed time: 131.83958 (100 processes)
    # Run 3x: Yes + Equivocation proportion: 0.06; Elapsed time: 100.312859 (25 processes)

    # Ideas:
    # 2 negations? -> probably weak.
    # Combine negation and normal in same test set - are they attacking different weaknesses? Would you see improvement?
    # Add more relationships -> HARD, scenario generation work!
    #



# For report:
# overall results
# Redundant premises
# no redundant premises