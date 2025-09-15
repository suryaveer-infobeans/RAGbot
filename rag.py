import os
import json
import re
from dotenv import load_dotenv
from sqlalchemy import create_engine, text as sql_text
from openai import OpenAI
from retriever import retrieve
from sql_validator import validate_sql
from decimal import Decimal

# ------------------------
# Load ENV + init
# ------------------------
load_dotenv()
_ENGINE = None
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Model IDs
BASE_MODEL = "gpt-4.1-nano-2025-04-14"
FINE_TUNED_MODEL = os.getenv("OPENAI_FINE_TUNED_MODEL")


# ------------------------
# DB connection
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
# Generate SQL with RAG
# ------------------------
def generate_sql_with_openai(question: str) -> str:
    """Generate SQL using fine-tuned model + retrieved schema context."""
    context_docs = retrieve(question, k=10)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert MySQL assistant. "
                "Generate ONLY valid SQL based on schema and examples below. "
                "Rules:\n"
                "- If the question asks for names, include first_name and last_name.\n"
                "- If the question asks for departments, include the department column.\n"
                "- Never return just COUNT(*) unless explicitly asked for a count.\n"
                "- Always alias aggregates clearly, e.g. COUNT(*) AS cnt.\n"
                "- If the query is unanswerable with schema, return SELECT * FROM employees WHERE 1=0.\n"
                "- Use correct table and column names from schema.\n"
            )
        },
        {"role": "system", "content": "\n\n".join(context_docs)},
        {"role": "user", "content": question},
    ]

    print  ("❗ Prompt to OpenAI:")
    for m in messages:
        role = m["role"]
        content = m["content"]
        print(f"[{role}]: {content}\n")
    
    model_id = FINE_TUNED_MODEL or BASE_MODEL
    resp = client.chat.completions.create(model=model_id, messages=messages, temperature=0)
    raw_sql = resp.choices[0].message.content.strip()

    print(f"✅ Raw SQL from OpenAI: {raw_sql}")
    # Clean SQL (remove markdown formatting if present)
    sql = re.sub(r"^```(sql)?\n", "", raw_sql, flags=re.IGNORECASE)
    sql = re.sub(r"\n```$", "", sql).strip()

    # Validate & repair if needed
    valid, errors = validate_sql(sql)
    if not valid:
        fix_prompt = [
            {"role": "system", "content": f"Fix this SQL query. Issues: {'; '.join(errors)}"},
            {"role": "user", "content": sql},
        ]
        resp2 = client.chat.completions.create(model=model_id, messages=fix_prompt, temperature=0)
        sql = resp2.choices[0].message.content.strip()
        sql = re.sub(r"^```(sql)?\n", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"\n```$", "", sql).strip()

    print(f"✅ Final SQL: {sql}")
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
        return {"query": sql, "result": [serialize_row(r) for r in rows]}


# ------------------------
# Build final answer
# ------------------------
def build_prompt(question: str, sql_meta: dict) -> list:
    parts = []
    parts.append("You are an assistant that answers based strictly on SQL results.")
    parts.append(f"Question: {question}")

    if sql_meta and sql_meta.get("result") is not None:
        parts.append("SQL Result (rows):")
        parts.append(json.dumps(sql_meta["result"], indent=2))
    else:
        parts.append(f"Error: {sql_meta.get('error')}")

    parts.append(
        "Rules:\n"
        "- Provide a short, clear answer.\n"
        "- If rows exist, return them as an HTML <table>.\n"
        "- If no results, say 'No data found.'\n"
        "- Do not fabricate or guess beyond the SQL results.\n"
        "- Use <br> for line breaks if needed.\n"
    )

    return [{"role": "user", "content": "\n\n".join(parts)}]


# ------------------------
# Main pipeline
# ------------------------
def answer_question(question: str):
    print(f"❓ User asked: {question}")
    sql_meta = None
    try:
        sql = generate_sql_with_openai(question)
        sql_meta = run_sql_query(sql)
    except Exception as e:
        sql_meta = {"error": str(e)}

    # Generate natural language answer
    messages = build_prompt(question, sql_meta)
    completion = client.chat.completions.create(model=BASE_MODEL, messages=messages, temperature=0)
    answer = completion.choices[0].message.content.strip()

    return answer, {"sql_meta": sql_meta}

def serialize_row(row):
    """
    Convert row values to JSON-serializable types and auto-generate user-friendly labels.
    """
    new_row = {}
    for k, v in row._mapping.items():
        label = to_friendly_label(k)  # automatically generate friendly label
        new_row[label] = float(v) if isinstance(v, Decimal) else v
    return new_row

# Dictionary of common columns → human-friendly names
COLUMN_PREDICTIONS = {
    "avg_salary": "Average Salary",
    "salary": "Salary",
    "dept": "Department",
    "department": "Department",
    "first_name": "First Name",
    "last_name": "Last Name",
    "city": "City",
    "project_name": "Project Name",
    "employee_id": "Employee ID",
    "hire_date": "Hire Date",
    "manager_id": "Manager ID",
    # Add more common patterns if needed
}

def to_friendly_label(col_name):
    """Convert DB column name to human-readable label using prediction dictionary."""
    col_lower = col_name.lower()
    if col_lower in COLUMN_PREDICTIONS:
        return COLUMN_PREDICTIONS[col_lower]
    # fallback: convert snake_case → Title Case
    return col_name.replace("_", " ").title()

# Manual test
if __name__ == "__main__":
    q = "List all cities where HR employees live"
    ans, meta = answer_question(q)
    print("---- Answer ----")
    print(ans)
    print("---- Meta ----")
    print(meta)
