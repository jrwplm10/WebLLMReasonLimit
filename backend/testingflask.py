from flask import Flask, render_template, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Set your OpenAI API key here
client = OpenAI(api_key="None")

@app.route('/')
def index():
    return render_template('frontend/index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": user_input}]
    )

    return jsonify({"response": response.choices[0].message.content})

if __name__ == '__main__':
    app.run(debug=True)