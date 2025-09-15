import os
import json
import subprocess
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_MODEL = "gpt-4.1-nano-2025-04-14"

INPUT_PATH = "data/training_data_100.json"
OUTPUT_PATH = "data/finetune_sql.jsonl"
SCHEMA_FILE = "database/schema.txt"


def load_schema():
    """Load schema from schema.txt if available."""
    if not os.path.exists(SCHEMA_FILE):
        print(f"⚠️ Schema file not found at {SCHEMA_FILE}, continuing without schema.")
        return None
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def prepare_finetune_jsonl(embed_schema=True):
    """Prepare fine-tuning JSONL file."""
    if not os.path.exists(INPUT_PATH):
        raise RuntimeError(f"❌ Input file not found: {INPUT_PATH}")

    schema = load_schema() if embed_schema else None

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for ex in data:
            system_prompt = "You are an expert MySQL assistant. Generate valid SQL only."
            if schema and embed_schema:
                system_prompt = (
                    "You are an expert MySQL assistant. "
                    "Given the following database schema, generate ONLY valid SQL:\n\n"
                    f"{schema}"
                )

            record = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": ex["question"]},
                    {"role": "assistant", "content": ex["sql"]},
                ]
            }
            f.write(json.dumps(record) + "\n")

    print(f"✅ Wrote fine-tune dataset: {OUTPUT_PATH}")
    return OUTPUT_PATH


def run_finetune(embed_schema=True):
    """Upload dataset & start fine-tuning job."""
    path = prepare_finetune_jsonl(embed_schema=embed_schema)

    # Upload training file
    res = subprocess.run(
        ["openai", "api", "files.create", "-f", path, "-p", "fine-tune"],
        capture_output=True, text=True
    )
    print(res.stdout)

    file_id = None
    for line in res.stdout.splitlines():
        if '"id":' in line:
            file_id = line.split(":")[1].strip().strip('",')
            break

    if not file_id:
        raise RuntimeError("❌ Could not extract file_id from upload output")

    # Start fine-tuning job
    subprocess.run(
        ["openai", "api", "fine_tuning.jobs.create", "-m", BASE_MODEL, "-F", file_id],
        check=True
    )
    print("🚀 Fine-tuning job started!")


if __name__ == "__main__":
    # Option 1: Only prepare dataset
    # prepare_finetune_jsonl(embed_schema=True)

    # Option 2: Prepare + upload + run fine-tune
    run_finetune(embed_schema=True)
