import os
import json
import faiss
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import pickle
import re

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SCHEMA_FILE = "database/schema.txt"
TRAINING_JSON = "data/training_data_100.json"
INDEX_FILE = "data/faiss_index.bin"
DOCS_FILE = "data/faiss_docs.pkl"


def embed(text: str):
    """Generate embeddings from OpenAI."""
    return client.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding


def build():
    if not os.path.exists(SCHEMA_FILE):
        raise RuntimeError("Schema file not found!")
    if not os.path.exists(TRAINING_JSON):
        raise RuntimeError("Training data not found!")

    schema = open(SCHEMA_FILE).read()
    schema_chunks = re.split(r'\n\s*\n', schema.strip())
    data = json.load(open(TRAINING_JSON))

    docs = []
    for i, c in enumerate(schema_chunks):
        docs.append({"id": f"schema-{i}", "text": f"Table Schema:\n{c}"})
    for i, ex in enumerate(data):
        docs.append({"id": f"example-{i}", "text": f"Q: {ex['question']}\nSQL: {ex['sql']}"})

    # Convert embeddings to numpy
    embeddings = np.array([embed(d["text"]) for d in docs], dtype="float32")

    # Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # Save index + docs
    faiss.write_index(index, INDEX_FILE)
    with open(DOCS_FILE, "wb") as f:
        pickle.dump(docs, f)

    print(f"✅ FAISS index built with {len(docs)} docs")


if __name__ == "__main__":
    build()
