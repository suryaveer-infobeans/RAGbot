import os
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from models import db, User, Conversation, Message
from rag import answer_question
from functools import wraps
import json

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'devkey')
db.init_app(app)

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error':'unauthenticated'}), 401
        return f(*args, **kwargs)
    return wrapper

@app.cli.command('db_init')
def db_init():
    with app.app_context():
        db.create_all()
        print('DB initialized.')

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Username required'}), 400
    
    existing = User.query.filter_by(username=username).first()
    if existing:
        return jsonify({'error': 'User already exists'}), 400

    user = User(username=username)
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    return jsonify({'message': 'Registered successfully', 'user': {'id': user.id, 'username': user.username}})

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'Invalid username'}), 400
    
    session['user_id'] = user.id
    return jsonify({'message': 'Logged in', 'user': {'id': user.id, 'username': user.username}})

@app.route('/api/logout', methods=['POST'])
def logout_user():
    session.pop('user_id', None)
    session.clear()
    return jsonify({'message': 'Logged out'})

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    text = data.get('text', '').strip()

    if not text:
        return jsonify({'error': 'empty question'}), 400

    user_id = session['user_id']

    # Get current conversation ID from session
    conv_id = session.get('conversation_id')
    if conv_id:
        conversation = Conversation.query.filter_by(id=conv_id, user_id=user_id).first()
    else:
        conversation = None

    # If no active conversation, create a new one for this user
    if not conversation:
        conversation = Conversation(user_id=user_id)
        db.session.add(conversation)
        db.session.commit()
        session['conversation_id'] = conversation.id  # 🔑 save in session

    # Save user message
    user_msg = Message(conversation_id=conversation.id, sender='user', text=text)
    db.session.add(user_msg)
    db.session.commit()

    # RAG answer
    try:
        assistant_text, meta = answer_question(text)
    except Exception as e:
        assistant_text = f"Error processing question: {e}"
        meta = {}

    # Save assistant message
    bot_msg = Message(conversation_id=conversation.id, sender='assistant', text=assistant_text, meta=json.dumps(meta))
    db.session.add(bot_msg)
    db.session.commit()

    return jsonify({'reply': assistant_text, 'meta': meta, 'conversation_id': conversation.id})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
