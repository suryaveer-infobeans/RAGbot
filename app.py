import os
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from models import db, User, Conversation, Message
from rag import answer_question
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'devkey')
db.init_app(app)


# -----------------------------
# Helpers
# -----------------------------
def login_required_page(f):
    """For routes that require HTML page login (redirect)"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def login_required_api(f):
    """For API routes (returns JSON error if not logged in)"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'unauthenticated'}), 401
        return f(*args, **kwargs)
    return wrapper


@app.cli.command('db_init')
def db_init():
    with app.app_context():
        db.create_all()
        print('DB initialized.')


# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def root():
    """If logged in → chat page, else → login"""
    if 'user_id' in session:
        return redirect(url_for('chat_page'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    """Login/Register page"""
    if 'user_id' in session:
        return redirect(url_for("chat_page"))
    return render_template("login.html")

@app.route('/chat')
@login_required_page
def chat_page():
    """Chat UI page — pass username so the template can show welcome on load."""
    user_id = session.get("user_id")
    user = None
    if user_id:
        user = User.query.get(user_id)
    username = user.username if user else ""
    return render_template("chat.html", username=username)


# -----------------------------
# API endpoints
# -----------------------------
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
    return jsonify({'message': 'Registered successfully',
                    'user': {'id': user.id, 'username': user.username},
                    'is_new': True})

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'Invalid username'}), 400

    session['user_id'] = user.id
    return jsonify({'message': 'Logged in',
                    'user': {'id': user.id, 'username': user.username},
                    'is_new': False})

@app.route('/api/logout', methods=['POST'])
def logout_user():
    session.clear()
    return jsonify({'message': 'Logged out'})

@app.route('/api/me', methods=['GET'])
def get_current_user():
    """Return logged in user info"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'authenticated': False})
    user = User.query.get(user_id)
    if not user:
        return jsonify({'authenticated': False})
    return jsonify({'authenticated': True,
                    'user': {'id': user.id, 'username': user.username}})

@app.route('/api/chat', methods=['POST'])
@login_required_api
def chat():
    data = request.json
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'empty question'}), 400

    user_id = session['user_id']

    # Get conversation from session
    conv_id = session.get('conversation_id')
    if conv_id:
        conversation = Conversation.query.filter_by(id=conv_id, user_id=user_id).first()
    else:
        conversation = None

    # If no conversation exists, create one
    if not conversation:
        conversation = Conversation(user_id=user_id)
        db.session.add(conversation)
        db.session.commit()
        session['conversation_id'] = conversation.id

    # Save user message
    user_msg = Message(conversation_id=conversation.id, sender='user', text=text)
    db.session.add(user_msg)
    db.session.commit()

    # RAG answer (using fine-tuned OpenAI model in rag.py)
    try:
        print(f"User question: {text}")
        assistant_text, meta = answer_question(text)
    except Exception as e:
        assistant_text = f"Error processing question: {e}"
        meta = {}

    # Save assistant message
    bot_msg = Message(conversation_id=conversation.id, sender='assistant',
                      text=assistant_text, meta=json.dumps(meta))
    print(f"Assistant reply: {assistant_text}")
    db.session.add(bot_msg)
    db.session.commit()

    return jsonify({'reply': assistant_text, 'meta': meta, 'conversation_id': conversation.id})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
