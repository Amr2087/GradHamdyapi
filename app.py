from flask import Flask, request, jsonify
import os
import json
from datetime import datetime
from groq import Groq

app = Flask(__name__)

# Initialize the Groq client with your API key
client = Groq(
    api_key="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",
)

# File where chat logs will be saved (using .jsonl extension for JSON Lines)
CHAT_LOG_FILE = 'chat_log.jsonl'


def save_chat_log(user_message, assistant_message):
    """Append a new chat entry with a timestamp to the log file."""
    chat_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_message": user_message,
        "assistant_message": assistant_message
    }
    with open(CHAT_LOG_FILE, 'a') as f:
        f.write(json.dumps(chat_entry) + "\n")


def load_chat_history():
    """Load the entire chat history from the log file."""
    if not os.path.exists(CHAT_LOG_FILE):
        return []
    history = []
    with open(CHAT_LOG_FILE, 'r') as f:
        for line in f:
            try:
                history.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return history


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Missing 'message' in request body"}), 400

    new_user_message = data['message']

    # Build the conversation messages list:
    # Start with the system prompt
    messages = [{"role": "system", "content": "you are a helpful assistant."}]

    # Load previous chat history and add them to the messages list
    history = load_chat_history()
    for entry in history:
        messages.append({"role": "user", "content": entry["user_message"]})
        messages.append({"role": "assistant", "content": entry["assistant_message"]})

    # Append the new user message at the end of the conversation
    messages.append({"role": "user", "content": new_user_message})

    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            max_completion_tokens=1024,
            top_p=1,
            stop=None,
            stream=False,
        )

        assistant_message = chat_completion.choices[0].message.content

        # Save the new conversation turn to the log file
        save_chat_log(new_user_message, assistant_message)

        return jsonify({"assistant_message": assistant_message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/history', methods=['GET'])
def history():
    """Endpoint to fetch all chat history."""
    chat_history = load_chat_history()
    return jsonify({"chat_history": chat_history})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
