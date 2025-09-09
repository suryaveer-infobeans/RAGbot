import os, json, requests, re, joblib
from dotenv import load_dotenv
from sqlalchemy import create_engine, text as sql_text
from sklearn.feature_extraction.text import TfidfVectorizer


load_dotenv()

# ------------------------
# Globals
# ------------------------
_ENGINE = None
VEC = None
CLF = None

# ------------------------
# DB Connection
# ------------------------
def get_engine():
    global _ENGINE
    if _ENGINE is None:
        dburi = os.getenv("SQLALCHEMY_DATABASE_URI")
        if not dburi:
            raise RuntimeError("SQLALCHEMY_DATABASE_URI not set")
        _ENGINE = create_engine(dburi)
    return _ENGINE

# ------------------------
# Gemini API helper
# ------------------------
def call_gemini_system(prompt: str) -> str:
    api_url = os.getenv("GEMINI_API_URL")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_url or not api_key:
        raise RuntimeError("GEMINI_API_URL or GEMINI_API_KEY not set")

    url = f"{api_url}?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)

    if resp.status_code != 200:
        raise RuntimeError(f"LLM API error: {resp.status_code} {resp.text}")

    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return json.dumps(data)

# ------------------------
# Load schema from .txt file
# ------------------------
def load_full_schema(path="database/schema.txt"):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

FULL_SCHEMA = load_full_schema()

# ------------------------
# Local Model Loader
# ------------------------
def load_local_model():
    global VEC, CLF
    try:
        VEC = joblib.load("models/vectorizer.pkl")
        CLF = joblib.load("models/sql_model.pkl")
        print("✅ Local SQL model loaded.")
    except Exception:
        VEC, CLF = None, None
        print("⚠️ No local SQL model found, will fallback to Gemini.")

load_local_model()

def predict_sql_local(question: str):
    if not VEC or not CLF:
        return None, 0.0
    X_vec = VEC.transform([question])
    proba = CLF.predict_proba(X_vec).max()
    sql = CLF.predict(X_vec)[0]
    return sql, proba

# ------------------------
# SQL Generator (Gemini)
# ------------------------
def generate_sql_with_gemini(question: str) -> str:
    prompt = f"""
You are an expert MySQL assistant. Based ONLY on the following schema, 
write a valid SQL query to answer the user's question.

Schema:
{FULL_SCHEMA}

Question: {question}

Rules:
- If the question asks for "names", include first_name and last_name.
- If the question asks for departments, include the department column.
- Never return just COUNT(*) unless explicitly asked for a count.
- Always alias aggregates clearly, e.g. COUNT(*) AS cnt.
- Return ONLY the SQL query (no explanations, no markdown).
"""
    raw_sql = call_gemini_system(prompt)
    sql = raw_sql.strip()
    sql = re.sub(r"^```.*?\n", "", sql, flags=re.DOTALL)
    sql = re.sub(r"\n```$", "", sql, flags=re.DOTALL)
    if sql.lower().startswith("sql"):
        sql = sql[3:].strip()
    return sql

# ------------------------
# Run SQL safely
# ------------------------
def run_sql_query(sql: str):
    forbidden = ["drop", "delete", "update", "alter", "insert"]
    if any(f in sql.lower() for f in forbidden):
        raise RuntimeError(f"Unsafe SQL blocked: {sql}")

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(sql_text(sql))
        rows = result.fetchall()
        return {"query": sql, "result": [dict(r._mapping) for r in rows]}

# ------------------------
# Save Training Data
# ------------------------
def save_training_example(question: str, sql: str, answer: str):
    record = {"question": question, "sql": sql, "answer": answer}
    path = "training_data.json"
    data = []

    # Load existing data if file exists
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

    # Skip if question already exists
    for d in data:
        if d["question"].strip().lower() == question.strip().lower():
            print(f"⚠️ Skipping duplicate question: {question}")
            return "Skipped (duplicate)"

    # Append new record
    data.append(record)

    # Save updated dataset
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Retrain model
    from train_model import train_sql_model  # import inside to avoid circular import
    train_sql_model()

    print(f"✅ Added new training example and retrained model: {question}")
    return "Saved & retrained"

# ------------------------
# Build final answer prompt
# ------------------------
def build_prompt(question: str, sql_meta: dict) -> str:
    parts = []
    parts.append("You are an assistant that answers user questions using the provided SQL results.")
    parts.append(f"Question: {question}")
    if sql_meta and sql_meta.get("query"):
        parts.append("SQL Query executed:")
        parts.append(sql_meta["query"])
    if sql_meta and sql_meta.get("result") is not None:
        parts.append("SQL Result (rows):")
        parts.append(json.dumps(sql_meta["result"], indent=2))
    parts.append("Provide a short, clear answer based strictly on the SQL results.")
    return "\n\n".join(parts)

# ------------------------
# Main answer function
# ------------------------
def answer_question(question: str):
    sql_meta = None
    sql_used = None

    try:
        # 1. Try local NLP model first
        sql_pred, confidence = predict_sql_local(question)
        if sql_pred and confidence > 0.6:  # threshold
            sql_used = sql_pred
        else:
            sql_used = generate_sql_with_gemini(question)

        # 2. Run SQL
        sql_meta = run_sql_query(sql_used)

    except Exception as e:
        sql_meta = {"error": str(e)}

    # 3. Build final answer prompt
    prompt = build_prompt(question, sql_meta)
    llm_response = call_gemini_system(prompt)

    # 4. Save training data
    if sql_meta and sql_meta.get("query") and sql_meta.get("result"):
        save_training_example(question, sql_meta["query"], llm_response)

    meta = {"sql_meta": sql_meta}
    return llm_response, meta
