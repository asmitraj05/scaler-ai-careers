import sys
import os
# Add vendor directory to path for dependencies
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vendor'))

from flask import Flask, request, jsonify
from flask_cors import CORS
from orchestrator import CareersSalesOrchestrator

app = Flask(__name__)
CORS(app)

# Initialize orchestrator
orchestrator = CareersSalesOrchestrator()

# In-memory storage for messages
messages_db = {}


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})


@app.route('/workflow/run', methods=['POST'])
def run_workflow():
    data = request.get_json()
    role = data.get('role')
    location = data.get('location')
    num_results = data.get('num_results', 5)

    if not role or not location:
        return jsonify({"error": "Missing role or location"}), 400

    result = orchestrator.run_workflow(role, location, num_results)

    # Store messages in memory
    for msg in result.get('results', []):
        messages_db[msg['id']] = msg

    return jsonify(result)


@app.route('/messages', methods=['GET'])
def get_all_messages():
    return jsonify(list(messages_db.values()))


@app.route('/messages/<message_id>', methods=['GET'])
def get_message(message_id):
    if message_id not in messages_db:
        return jsonify({"error": "Message not found"}), 404
    return jsonify(messages_db[message_id])


@app.route('/messages/<message_id>', methods=['PUT'])
def update_message(message_id):
    if message_id not in messages_db:
        return jsonify({"error": "Message not found"}), 404

    data = request.get_json()
    msg = messages_db[message_id]

    # Store original if first edit
    if not msg.get('edited_by_user'):
        msg['original_message'] = f"Subject: {msg['subject_line']}\n\n{msg['message_body']}"
        msg['edited_by_user'] = True

    if 'subject_line' in data:
        msg['subject_line'] = data['subject_line']
    if 'message_body' in data:
        msg['message_body'] = data['message_body']

    messages_db[message_id] = msg
    return jsonify(msg)


@app.route('/messages/<message_id>/approve', methods=['POST'])
def approve_message(message_id):
    if message_id not in messages_db:
        return jsonify({"error": "Message not found"}), 404

    msg = messages_db[message_id]
    msg['approval_status'] = 'approved'
    messages_db[message_id] = msg
    return jsonify(msg)


@app.route('/messages/<message_id>/reject', methods=['POST'])
def reject_message(message_id):
    if message_id not in messages_db:
        return jsonify({"error": "Message not found"}), 404

    msg = messages_db[message_id]
    msg['approval_status'] = 'rejected'
    messages_db[message_id] = msg
    return jsonify(msg)


@app.route('/stats', methods=['GET'])
def get_stats():
    all_messages = list(messages_db.values())

    approved = sum(1 for m in all_messages if m.get('approval_status') == 'approved')
    rejected = sum(1 for m in all_messages if m.get('approval_status') == 'rejected')
    pending = sum(1 for m in all_messages if m.get('approval_status') == 'pending')

    return jsonify({
        "total_messages": len(all_messages),
        "approved": approved,
        "pending": pending,
        "rejected": rejected,
        "approval_rate": approved / len(all_messages) if all_messages else 0
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
