import pickle
from openai import OpenAI
import threading

with open("C:/Users/Cowga/OneDrive/Desktop/WPI/AI Ethics Project/WebLLMReasonLimit/backend/keys/openai.key", 'r') as f:
    API_KEY = f.readline()
    API_KEY = API_KEY.rstrip('\n')
openai_client = OpenAI(api_key=API_KEY)

def query_chatgpt(model, prompt):
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
    print(prompt + '\n')
    print(answer + '\n')

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

def threaded_query(scenario):
    prompts = build_prompts(scenario)

    threads = []
    for prompt in prompts:
        t = threading.Thread(target=query_chatgpt, args=["gpt-4o", prompt])
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