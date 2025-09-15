# RAGbot — Ask Anything, Answered from Your Data.

Local RAG Assistant with Gemini (Flask + MySQL)

## Overview

RAGbot is a **Retrieval-Augmented Generation (RAG) assistant** built with **Flask, FAISS, and OpenAI GPT**. It allows users to ask natural language questions about a database, retrieves relevant schema/document context, generates **validated SQL queries**, and summarizes results into user-friendly answers.  

## Features  
- **User Authentication** (Flask sessions + SQLAlchemy models)  
- **Chat Interface** with stored conversation history  
- **FAISS Vector Store Retrieval** for schema/document context  
- **OpenAI Integration** (SQL generation + natural language summarization)  
- **SQL Validator** for safe query execution  
- **MySQL Support** for running generated queries  
- **Frontend** with Bootstrap, jQuery, and Flask templates  

---


## Requirements

- Python 3.10+
- MySQL 8.0+
- Flask
- FAISS
- OpenAI API KEY


---

## Project Structure  
```
RAGbot/
├── app.py                 # Flask app entry point
├── rag.py                 # Core RAG pipeline (retrieval + SQL + LLM)
├── retriever.py           # FAISS retrieval logic with embeddings
├── sql_validator.py       # SQL validation utilities
├── models.py              # SQLAlchemy models (User, Conversation, Message)
├── build_index.py         # Build FAISS index from schema/docs
├── train_model.py         # Lightweight local training for SQL mapping
├── scripts/               # Data preparation scripts (prepare_finetune.py)
├── templates/             # HTML templates (chat, login, index)
├── static/                # CSS/JS frontend assets
├── data/                  # FAISS index + training datasets (finetune jsonl)
├── database/schema.txt    # Example database schema
├── models/                # ML artifacts (vectorizer.pkl, sql_model.pkl)
├── tests/                 # Unit tests
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```
---

## Installation (Ubuntu / Debian)

### 1. Clone the Repository
```bash
git clone https://github.com/suryaveer-infobeans/RAGbot.git
cd RAGbot
```

### 2. Set Up Python Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure MySQL Database
Create a MySQL database and user:
```sql
CREATE DATABASE DB_NAME;
CREATE USER 'DB_USER'@'localhost' IDENTIFIED BY 'changeme';
GRANT ALL PRIVILEGES ON DB_NAME.* TO 'DB_USER'@'localhost';
```

### 4. Create `.env` File
At the project root, create a `.env` file with the following content:

```env
# Database settings
DB_USER=XXXX
DB_PASS=XXXX
DB_HOST=localhost
DB_NAME=XXXX
SQLALCHEMY_DATABASE_URI=mysql+pymysql://${DB_USER}:${DB_PASS}@${DB_HOST}/${DB_NAME}

# Flask settings
FLASK_ENV=development
SECRET_KEY=replace_this

# OpenAI settings
OPENAI_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-nano-2025-04-14
OPENAI_FINE_TUNED_MODEL=  XXXXXXXXXXXXXXXXXXXXXX # (optional) set this to your ft:... model id after fine-tuning
```

### 5. Initialize Database Tables
Run the following command to create the necessary tables:
```bash
flask db_init
```

### 6. (Optional) Ingest Schema and Documents
If you have a schema SQL file (e.g., `database/RAGbot.sql`), import it into the database using:
```bash
mysql -u rag_user -p RAGbot < database/RAGbot.sql
```
### 7. Build FAISS Index  
```bash
python build_index.py
```

This uses your `OPENAI_API_KEY` to embed the schema / docs and writes `data/faiss_index.bin` + `data/faiss_docs.pkl`.

---

## 🔧 Fine-tuning the SQL generation model

RAGbot supports common approache for "fine-tuning" SQL generation behavior:

 **OpenAI-hosted fine-tuning (recommended for best LLM results)** — produce a JSONL training file in *chat* format and create a fine-tune job on OpenAI (or via the OpenAI UI). The project already includes `scripts/prepare_finetune.py` which builds a `data/finetune_sql.jsonl` file from `data/training_data_100.json`.

---

### OpenAI-hosted fine-tune (chat-style JSONL)

**Prepare training data (chat messages format), Upload & create a fine-tune job using the OpenAI API:**  
The project provides a script to generate a JSONL file in chat format (each line is one example with a `messages` array: system, user, assistant). Run:

```bash
python scripts/prepare_finetune.py
# -> writes data/finetune_sql.jsonl
```
> After the job completes you'll receive a fine‑tuned model id (something starting with `ft:`). Set that id in your `.env` as `OPENAI_FINE_TUNED_MODEL` so `rag.py` will prefer it automatically:

```env
OPENAI_FINE_TUNED_MODEL=ft:your-finetuned-model-id
```

### 8. Run the Application
Start the Flask application:
```bash
flask run --host=0.0.0.0 --port=5000
```

Open: **http://127.0.0.1:5000**

---

## Security Notes

- **Environment Variables**: Keep `.env` file secure and out of version control.
- **SQL Safety**: The SQL builder includes basic sanitization. Review and extend it for production use.
- **Production Considerations**: Use a secure vector database for embeddings and protect access with authentication.


---

## Example Workflow

1. **Question**: "How many employees are from Australia?"
2. **SQL Query**:
   ```sql
   SELECT COUNT(DISTINCT T1.employee_id) AS employee_count
   FROM employees AS T1
   INNER JOIN employee_addresses AS T2
     ON T1.employee_id = T2.employee_id
   WHERE T2.country = 'Australia';
   ```
3. **LLM Response**: "There is 1 employee from Australia."

---

## License

This project is licensed under the MIT License. See the LICENSE

