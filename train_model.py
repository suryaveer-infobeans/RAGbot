import json, joblib, os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

MODEL_DIR = "models"
VEC_PATH = os.path.join(MODEL_DIR, "vectorizer.pkl")
CLF_PATH = os.path.join(MODEL_DIR, "sql_model.pkl")
DATA_PATH = "training_data.json"


def train_sql_model(new_example=None):
    """
    Train or update the SQL NLP model.

    Args:
        new_example (dict): optional, {"question": "...", "sql": "...", "answer": "..."} 
                            If given, it's added to training_data.json before training.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)

    # 1. Load existing data
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    # 2. Append new example if provided
    if new_example:
        required = {"question", "sql", "answer"}
        if not required.issubset(new_example.keys()):
            raise ValueError(f"New example must contain keys: {required}")
        data.append(new_example)
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    if not data:
        raise RuntimeError("No training data found!")

    # 3. Prepare training sets
    questions = [d["question"] for d in data]
    sqls = [d["sql"] for d in data]

    # 4. Train model
    vec = TfidfVectorizer(stop_words="english")
    X = vec.fit_transform(questions)

    clf = LogisticRegression(max_iter=2000)
    clf.fit(X, sqls)

    # 5. Save artifacts
    joblib.dump(vec, VEC_PATH)
    joblib.dump(clf, CLF_PATH)

    return f"✅ Model trained with {len(data)} examples. Files saved to {MODEL_DIR}/"

