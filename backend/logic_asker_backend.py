from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, TextGenerationPipeline
import torch

with open("keys/openai.key", 'r') as f:
    API_KEY = f.readline()
    API_KEY = API_KEY.rstrip('\n')
openai_client = OpenAI(api_key=API_KEY)

# Absolute path to frontend directory gathered from relative location
FRONTEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

app = Flask(__name__,
            static_folder=os.path.join(FRONTEND_PATH),
            template_folder=FRONTEND_PATH)
# Initialize the model cache
model_cache = {}

@app.route('/query_openai', methods=['POST'])
def query_openai():
    data = request.get_json()
    prompt = data.get('prompt')
    model_name = data.get('model_name')
    
    completion = openai_client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "developer", "content": "You are being prompted with a series of propositional statements and a question. Your job is to determine the answer to the question as 'yes', 'no', or in the case that the answer is unknown, 'unknown'. Provide a brief paragraph explaining your reasoning for your answer, but it is critical that this paragraph is brief and contained in one single paragraph with no line breaks. End your response with 'yes', 'no', or 'unknown', specifically structured as 'Final Answer = [Your Answer]'. Your response should ONLY contain a paragraph of reasoning and a final answer."},
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    
    answer = completion.choices[0].message.content
    return jsonify({"response": answer})

@app.route('/generate_prompt', methods=['POST'])
def generate_prompt():
    prompt1 = "If it is raining outside, then Bob is wearing a coat. If it is raining outside, then the ground is wet. If the ground is wet, then Bob is wearing boots. It is raining outside. Is Bob wearing boots?"
    prompt2 = "If it is raining outside, then Bob is wearing a coat. If it is raining outside, then the ground is wet. If the ground is wet, then Bob is wearing boots. Bob is wearing boots. Is it raining outside?"
    return jsonify({"response": prompt1})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index')
def index2():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/llm1')
def llm1():
    return render_template('llm1.html')

@app.route('/llm2')
def llm2():
    return render_template('llm2.html')

@app.route('/llm3')
def llm3():
    return render_template('llm3.html')

if __name__ == '__main__':
    app.run(debug=True)