from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
import multiprocessing
from multiprocessing import Process
from functools import partial
import queue

with open("keys/openai.key", 'r') as f:
    API_KEY = f.readline()
    API_KEY = API_KEY.rstrip('\n')
openai_client = OpenAI(api_key=API_KEY)

# Absolute path to frontend directory gathered from relative location
FRONTEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

app = Flask(__name__,
            static_folder=os.path.join(FRONTEND_PATH),
            template_folder=FRONTEND_PATH)

scenario_failures = queue.Queue()
GENERATING = False

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

    part = part + "Is this statement true: "
    
    prompts = []
    for question in scenario['hard_infer_list']:
        prompts.append(part + question + ".")
    return prompts

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
    
    if answer[-4:-1].lower() != "yes":
        print("Found failure")
        scenario_failures.put([question_scenario, answer])

def generate_failures_background(num_processes=12):
    model = "gpt-4o"

    dev_prompt = ("You are being prompted with a scenario. "
              "Your job is to determine the answer to the question as 'yes', 'no', or in the case that the answer is unknown, 'unknown'. "
              "Provide a brief paragraph explaining your reasoning for your answer, but it is critical that this paragraph is brief and contained in one single paragraph with no line breaks. "
              "End your response with 'yes', 'no', or 'unknown', specifically structured as 'Final Answer = [Your Answer]'. "
              "Your response should ONLY contain a paragraph of reasoning and a final answer.")
    
    while(GENERATING):
        # Generate a scenario
        # Assumes dict with hard_infer_list contained within
        scenario = generate_scenario()
    
        # Build prompts
        prompts = build_prompts(scenario)

        # All prompts are tested and failures are saved in queue
        print("Number of scenarios total to try: " + str(len(prompts)))
        multi_pool = multiprocessing.Pool()
        multi_pool.map(partial(query_completion, API_KEY, model, dev_prompt), prompts)
        multi_pool.close()
        multi_pool.join()

# Initializes a background process for generating prompts
generator = Process(target=generate_failures_background)

# Pulls a failure example from the queue for display on webpage
@app.route('/pop_failure_example', methods=['POST'])
def generate_prompt():
    if scenario_failures.empty():
        print("ERROR: Tried to grab an example failure where there is none")
        return jsonify({"success": False, "prompt" : None, "response" : None})
    else:
        example = scenario_failures.get()
        return jsonify({"success": True, "prompt" : example[0], "response" : example[1]})

@app.route('/')
def index():
    if not GENERATING:
        GENERATING = True
        generator.start()
    return render_template('index.html')

@app.route('/index')
def index2():
    if not GENERATING:
        GENERATING = True
        generator.start()
    return render_template('index.html')

@app.route('/about')
def about():
    if GENERATING:
        GENERATING = False
        generator.join()
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)