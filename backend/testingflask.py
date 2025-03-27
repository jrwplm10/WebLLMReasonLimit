from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from frontend import mainpage

app = Flask(__name__)

# Set your OpenAI API key here
client = OpenAI(api_key="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")

@app.route('/')
def index():
    return render_template('index.html')

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