import os,json
from dotenv import load_dotenv
load_dotenv()

INPUT="data/training_data_100.json"
OUTPUT="data/finetune_sql.jsonl"

def run():
    data=json.load(open(INPUT,"r"))
    with open(OUTPUT,"w",encoding="utf-8") as f:
        for ex in data:
            record={
                "messages":[
                    {"role":"system","content":"You are an expert MySQL assistant. Generate valid SQL only."},
                    {"role":"user","content":ex["question"]},
                    {"role":"assistant","content":ex["sql"]}
                ]
            }
            f.write(json.dumps(record)+"\n")
    print("✅ Wrote",OUTPUT)

if __name__=="__main__":
    run()
