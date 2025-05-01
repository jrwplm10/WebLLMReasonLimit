from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
import multiprocessing as mp
import pickle
import random
from time import sleep

# Should only run once to fix the working directory
if __name__ == '__main__':
    print(os.getcwd())
    os.chdir('..')
    print(os.getcwd())

import prompt_gen.update_prompt_test as gen_tools

# Front end path is instantiated to make the flask app
FRONTEND_PATH = os.path.abspath(os.path.join(os.getcwd(), "frontend"))
app = Flask("WEBLLMREASONLIMIT", static_folder=os.path.join(FRONTEND_PATH), template_folder=FRONTEND_PATH)

def build_prompts(scenario):
    part = "The following scenario describes a family tree. "
    # part += "It may contain redundant relationships, but the described relationships described are correct. "
    part += "You may assume siblings always share the same parents. "
    # part += "The people in this scenario are "
    # for name in scenario['people']:
    #     part = part + name + ", "
    # part = part[:-2] + ". "
    
    for premises in scenario['premises']:
        part = part + premises + ". "

    part = part + "Is this statement true: "
    
    prompts = []
    for question in scenario['hard_infer_list']:
        prompts.append(part + question + ".")
    return prompts

def query_completion(api_key, model, dev_prompt, failure_queue, question_scenario):
    openai_client = OpenAI(api_key=api_key)

    # We need to show the dev prompt. Put it in the user message body.
    completion = openai_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": dev_prompt + "\nScenario:\n" + question_scenario,
            },
        ],
    )

    # completion = openai_client.chat.completions.create(
    #     model=model,
    #     messages=[
    #         {"role": "developer",
    #          "content": dev_prompt},
    #         {
    #             "role": "user",
    #             "content": question_scenario,
    #         },
    #     ],
    # )

    answer = completion.choices[0].message.content
    
    #print("Testing prompt:")
    if answer[-4:-1].lower() != "yes":
        print("\tFound failure")
        print(question_scenario)
        print(answer)
        failure_queue.put([question_scenario, answer])

def generate_failures_background(failure_queue):
    model = "gpt-4o"

    dev_prompt = ("You are being prompted with a scenario. "
              "Your job is to determine the answer to the question as 'yes', 'no', or in the case that the answer is unknown, 'unknown'. "
              "Provide a brief paragraph explaining your reasoning for your answer, but it is critical that this paragraph is brief and contained in one single paragraph with no line breaks. "
              "End your response with 'yes', 'no', or 'unknown', specifically structured as 'Final Answer = [Your Answer].'. "
              "Your response should ONLY contain a paragraph of reasoning and a final answer.")
    
    # Generate a scenario **********
    # Assumes dict with hard_infer_list contained within
    #scenario = generate_scenario()
    print(os.getcwd())
    with open("prompt_gen/scenarios_set_medium_large.pickle", 'rb') as f:
        scenarios = pickle.load(f)
    
    with open("backend/keys/openai.key", 'r') as f:
        API_KEY = f.readline()
        API_KEY = API_KEY.rstrip('\n')

    # randomly sample.
    random.shuffle(scenarios)

    for idx, s in enumerate(scenarios):

        prompts = gen_tools.backend_build_scenario_prompts(s)
        print("Scenario idx: " + str(idx) + "; # prompts: " + str(len(prompts)))
        # prompts = build_prompts(s)
        # print(failure_queue.empty())
        print("Approx. queue size: " + str(failure_queue.qsize()))

        # All prompts are tested and failures are saved in queue
        print("Number of scenarios total to try: " + str(len(prompts)))
        processes = []
        timeout_counter = 0
        for prompt in prompts:
            process = mp.Process(target=query_completion, args=[API_KEY, model, dev_prompt, failure_queue, prompt])
            process.start()
            processes.append(process)
            timeout_counter += 1
            if timeout_counter >= 10:
                # print("Timeout time!")
                # sleep(5)
                timeout_counter = 0

        for process in processes:
            process.join()
        #print(list(failure_queue.queue))
        

# Pulls a failure example from the queue for display on webpage
@app.route('/get_failure_example', methods=['POST'])
def generate_prompt():
    scenario_failures = app.config["failures"]
    print(scenario_failures)
    if scenario_failures.empty():
        print("ERROR: Tried to grab an example failure where there is none")
        return jsonify({"success": False, "prompt" : None, "response" : None})
    else:
        example = scenario_failures.get()
        return jsonify({"success": True, "prompt" : example[0], "response" : example[1]})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index')
def index2():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    fail_queue = mp.Queue(maxsize=5)
    # Initializes a background process for generating prompts
    generator = mp.Process(target=generate_failures_background, args=[fail_queue])
    generator.start()
    app.config["failures"] = fail_queue
    app.run(debug=True, use_reloader=False)

    # To see this locally, look at this url: http://127.0.0.1:5000