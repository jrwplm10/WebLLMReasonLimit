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


import multiprocessing

# Put your api key path here.
with open("/home/jeremy/Documents/WPI_Spring_25/CS_555/Project/OpenAI_Api_free", 'r') as f:
    API_KEY = f.readline()
    API_KEY = API_KEY.rstrip('\n')

def build_prompts(scenario):
    part = "The following scenario describes a family tree. "
    part += "It may contain redundant relationships, but the described relationships described are correct. "
    part += "You may assume siblings always share the same parents. "
    part += "The people in this scenario are "
    for name in scenario['people']:
        part = part + name + ", "
    part = part[:-2] + ". "
    
    for premises in scenario['premises']:
        part = part + premises + ". "

    # part += "You may assume there are no step-relationships unless explicitly mentioned. "

    part = part + "Is this statement true: "
    
    # prompts = [part + scenario['easy_infer'] + "."]
    prompts = []
    for question in scenario['hard_infer_list']:
        prompts.append(part + question + ".")
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

    print("Starting pool evaluation")
    starttime = datetime.datetime.now()

    # Build prompts.
    # Choose a random scenario
    hard_infer_indices = []
    prompts = []
    scenario_indices = []
    for idx, s in enumerate(scenarios):
        all_scenarios = build_prompts(s)
        # hard_infer_indices.append(random.choice(range(len(all_scenarios[1:]))))
        # prompts.append(all_scenarios[hard_infer_indices[-1]])

        # ALL QUESTIONS MODE~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Do ALL hard questions; try to find a pattern!
        # This requires annoying indexing to do with multiprocessing though...
        hard_infer_indices = hard_infer_indices + list(range(len(all_scenarios)))
        prompts = prompts + list(all_scenarios)
        scenario_indices = scenario_indices + [idx] * len(all_scenarios)

    print("Number of scenarios total to try: " + str(len(prompts)))

    multi_pool = multiprocessing.Pool()

    scenario_answers = multi_pool.map(partial(query_completion, API_KEY, model, dev_prompt), prompts)

    multi_pool.close()
    multi_pool.join()

    # evaluate answers
    # for idx, s in enumerate(scenarios):
    failure_count = 0
    equivocate_count = 0
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
    print("Failure count: " + str(failure_count))
    print("Equivocation count: " + str(equivocate_count))

def newlineify(in_str):
    # make it not a pain to read.
    return in_str.replace(". ", ".\n")

def analyze_results(scenario_path, ):
    with open(scenario_path, 'rb') as f:
        scenarios = pickle.load(f)

    num_scenarios = len(scenarios)
    # print("Total number of scenarios: " + str(len(scenarios)))

    count_scenario_tests = 0
    count_incorrect = 0
    examples = []
    for scenario in scenarios:
        # Build prompts.
        all_scenarios = build_prompts(scenario)
        # look at hard_infer responses
        for idx, result in enumerate(scenario['hard_infer_successes']):
            # We only answered one for now.
            if result is None:
                continue

            count_scenario_tests += 1

            if result != "yes":
                count_incorrect += 1
                examples.append({
                    'prompt': all_scenarios[idx],
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
    analyze_results('test_mini.pickle')
    # main('test_moderate.pickle', num_processes=20)
    # analyze_results('test_moderate.pickle')

    # initially: 11% incorrect rate
    # fix 1:
    # 8% incorrect rate
    # fix 2; prompt has more information on edge cases:
    # 5% incorrect rate
    # fix 3; reword prompt, fix siblings being parents again.
    # 1% incorrect rate (BAD!)
    # Test all possible "hard" questions:
    #