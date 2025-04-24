import pickle
from openai import OpenAI
import threading
import os
import json

log_lock = threading.Lock() # global locking mechanism during results logging

with open("C:/Users/Cowga/OneDrive/Desktop/WPI/AI Ethics Project/WebLLMReasonLimit/backend/keys/openai.key", 'r') as f:
    API_KEY = f.readline()
    API_KEY = API_KEY.rstrip('\n')
openai_client = OpenAI(api_key=API_KEY)

# A function to log query results
def log_result(prompt, answer, status, log_file='processing_log.json'):
    result = {
        "prompt": prompt,
        "answer": answer,
        "status": status
    }

    with log_lock:
        if os.path.exists(log_file): # if log file exists, read the current log, else create a new one
            with open(log_file, 'r') as f:
                try:
                    log_data = json.load(f)
                except json.JSONDecodeError:
                    log_data = []
        else:
            log_data = []

        log_data.append(result)

        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=4)

def query_chatgpt(model, prompt, log_file='processing_log.json'):
    try:
        completion = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "developer", "content": "You are being prompted with a scenario. Your job is to determine the answer to the question as 'yes', 'no', or in the case that the answer is unknown, 'unknown'. Provide a brief paragraph explaining your reasoning for your answer, but it is critical that this paragraph is brief and contained in one single paragraph with no line breaks. End your response with 'yes', 'no', or 'unknown', specifically structured as 'Final Answer = [Your Answer]'. Your response should ONLY contain a paragraph of reasoning and a final answer."},
            {
                "role": "user",
                "content": prompt,
            },
        ],
        )
    
        answer = completion.choices[0].message.content
        print(f"Prompt: {prompt}\nAnswer: {answer}\n")
        #print(prompt + '\n')
        #print(answer + '\n')
        
        log_result(prompt, answer, status="success", log_file=log_file)
    
    except Exception as e:
        print(f"Error processing prompt: {prompt}\nError: {str(e)}")
        log_result(prompt, "", status="error", log_file=log_file)

def loadData():
    # for reading also binary mode is important
    dbfile = open('pickles/Scenarios_2000.pickle', 'rb')
    p = pickle.load(dbfile)
    dbfile.close()
    return p

def build_prompts(scenario):
    part = "The people in this scenario are "
    for name in scenario['people']:
        part = part + name + ", "
    part = part[:-2] + ". "
    
    for premises in scenario['premises']:
        part = part + premises + ". "
    part = part + "Is this statement true: "
    
    prompts = [part + scenario['easy_infer'] + "."]
    for question in scenario['hard_infer']:
        prompts.append(part + question + ".")
    return prompts

def threaded_query(scenario, log_file='processing_log.json'):
    prompts = build_prompts(scenario)

    threads = []
    for prompt in prompts:
        t = threading.Thread(target=query_chatgpt, args=["gpt-4o", prompt, log_file])
        threads.append(t)
        t.start()

    for thread in threads:
        thread.join()
    
def main():
    scenarios = loadData()
    for s in scenarios:
        threaded_query(s)

if __name__ == '__main__':
    main()