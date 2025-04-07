from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, TextGenerationPipeline
import torch

client = OpenAI(api_key="None")

# Absolute path to frontend directory gathered from relative location
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

# Building the flask app with new relative path
app = Flask(__name__,
            static_folder=os.path.join(frontend_path),
            template_folder=frontend_path)

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

@app.route('/')
def index():
    return render_template('index.html')

#print(prompt_model("deepseek-ai/deepseek-R1", "Hello, what are you?"))

if __name__ == '__main__':
    app.run(debug=True)