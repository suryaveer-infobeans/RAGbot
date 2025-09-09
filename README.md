# RAGbot — Ask Anything, Answered from Your Data.

Local RAG Assistant with Gemini (Flask + MySQL)

## Overview

This project is a **Local Retrieval-Augmented Generation (RAG) Assistant** that answers questions about your custom database schema and data. It combines local retrieval using TF-IDF with MySQL for factual results and integrates with Google Gemini (or any LLM with an HTTP API) for summarization and contextualization.

### Key Features
- **Chat-based assistant** with per-account chat history stored in MySQL.
- **Local Retriever** (TF-IDF) for schema and document-based context retrieval.
- **SQL Query Generation** for actionable data queries.
- **LLM Integration** for summarizing SQL results and providing user-friendly answers.
- **Frontend** built with Bootstrap and jQuery for a simple chat UI.

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
CREATE DATABASE customGPT;
CREATE USER 'rag_user'@'localhost' IDENTIFIED BY 'changeme';
GRANT ALL PRIVILEGES ON customGPT.* TO 'rag_user'@'localhost';
```

### 4. Create `.env` File
At the project root, create a `.env` file with the following content:
```
DB_USER=DBUSER
DB_PASS=DBPASSWORD
DB_HOST=DBHOST
DB_NAME=DBNAME
SQLALCHEMY_DATABASE_URI=mysql+pymysql://${DB_USER}:${DB_PASS}@${DB_HOST}/${DB_NAME}

FLASK_ENV=development
SECRET_KEY=replace_this

GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent

```

### 5. Initialize Database Tables
Run the following command to create the necessary tables:
```bash
flask db_init
```

### 6. (Optional) Ingest Schema and Documents
If you have a schema SQL file (e.g., `database/customGPT.sql`), import it into the database using:
```bash
mysql -u rag_user -p customGPT < database/customGPT.sql
```

### 7. Run the Application
Start the Flask application:
```bash
flask run --host=0.0.0.0 --port=5000
```

---

## How It Works

1. **User Interaction**: A user asks a question via the chat interface.
2. **Local Retrieval**: The system retrieves relevant context from the schema and documents using TF-IDF.
3. **SQL Query Generation**: If the question is actionable, a SQL query is generated and executed against the MySQL database.
4. **LLM Summarization**: The SQL results are sent to the Gemini API (or another LLM) for summarization and user-friendly response generation.
5. **Chat History**: The conversation, including SQL queries and results, is stored in MySQL for future reference.

---

## Security Notes

- **Environment Variables**: Keep `.env` file secure and out of version control.
- **SQL Safety**: The SQL builder includes basic sanitization. Review and extend it for production use.
- **Production Considerations**: Use a secure vector database for embeddings and protect access with authentication.

---

## Project Structure

- **`app.py`**: Main Flask application and API endpoints.
- **`models.py`**: SQLAlchemy models for users, conversations, and messages.
- **`rag.py`**: Core logic for retrieval, SQL generation, and LLM integration.
- **`rag_ingest.py`**: Utility for ingesting schema and documents.
- **`templates/index.html`**: Frontend HTML template.
- **`static/js/chat.js`**: JavaScript for chat functionality.
- **`static/css/style.css`**: Basic styling for the chat UI.
- **`database/`**: Contains SQL scripts and schema files.
- **`models/`**: Stores trained models (e.g., TF-IDF vectorizer and classifier).
- **`training_data.json`**: Training data for the local SQL model.

---

## Requirements

- Python 3.8+
- MySQL 8.0+
- Flask
- Flask-SQLAlchemy
- scikit-learn
- pdfminer.six (for PDF schema ingestion)

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

