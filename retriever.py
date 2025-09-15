# retrieve.py

import faiss
import numpy as np
import pickle
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INDEX_FILE = "data/faiss_index.bin"
DOCS_FILE = "data/faiss_docs.pkl"


def embed(text: str):
    """Generate embeddings from OpenAI."""
    return client.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding


def retrieve(query: str, k: int = 3, required_tables=None, mode="any", max_len=2000):
    """
    Retrieve relevant documents from FAISS with validation.
    
    :param query: User question
    :param k: Number of docs to retrieve
    :param required_tables: List of table names to check in docs
    :param mode: "any" (doc contains any table) or "all" (doc must contain all tables)
    :param max_len: Max length of a doc to include
    :return: List of validated doc texts
    """
    # Load FAISS index
    index = faiss.read_index(INDEX_FILE)
    print(f"✅ Loaded FAISS index with {index.ntotal} vectors")

    # Load docs
    with open(DOCS_FILE, "rb") as f:
        docs = pickle.load(f)

    # Embed query
    q_emb = np.array([embed(query)], dtype="float32")
    D, I = index.search(q_emb, k)

    retrieved_texts = [docs[i]["text"] for i in I[0]]

    # Validate docs
    validated_docs = []
    for doc in retrieved_texts:
        if not doc.strip():
            continue
        if len(doc) > max_len:
            continue
        if required_tables:
            tables_found = [table.lower() in doc.lower() for table in required_tables]
            if mode == "all" and not all(tables_found):
                continue
            if mode == "any" and not any(tables_found):
                continue
        validated_docs.append(doc)

    if not validated_docs:
        print("⚠️ No validated docs found. Returning top k unfiltered docs.")
        validated_docs = retrieved_texts

    print(f"🔍 Retrieved {len(validated_docs)} validated documents for query: {query}")
    return validated_docs


if __name__ == "__main__":
    query = "For each department, give me the average salary of employees who are working on at least one project and live in city Velezfurt"
    required_tables = ["employees", "employee_projects", "employee_addresses"]
    docs = retrieve(query, k=10, required_tables=required_tables, mode="all")
    for i, doc in enumerate(docs, 1):
        print(f"--- Doc {i} ---\n{doc}\n")
    print(f"Total docs retrieved: {len(docs)}")