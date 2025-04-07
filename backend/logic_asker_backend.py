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

# Building the flask app with new relative path
app = Flask(__name__,
            static_folder=os.path.join(FRONTEND_PATH),
            template_folder=FRONTEND_PATH)

def load_model(model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,  # Use FP16 cause I am using an RTX2060
        device_map="auto",
        trust_remote_code=True
    )
    return TextGenerationPipeline(model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)

# Initialize the model cache
model_cache = {}

def prompt_model(model_name, prompt):
    """
    Prompts a huggingface model given the model name and the prompt
    Also caches models after creation for faster use later
    Example model names:
        meta-llama/Llama-3.2-3B-Instruct
        deepseek-ai/deepseek-R1
    """
    if model_name not in model_cache:
        print("Model \"" + model_name + "\" not found in cache, loading the model")
        model = load_model(model_name)
        if model == -1:
            return "model not found"
        model_cache[model_name] = load_model(model_name)
    
    response = model_cache[model_name](prompt, max_new_tokens=200, temperature=0.7)
    return response[0]["generated_text"]

@app.route('/query_openai', methods=['POST'])
def query_openai():
    data = request.get_json()
    prompt = data.get('prompt')
    model_name = data.get('prompt')
    
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

if __name__ == '__main__':
    app.run(debug=True)