import json
from rag import generate_sql
from sql_validator import validate_sql

DATA="data/training_data_100.json"

def run_tests():
    qs=json.load(open(DATA))
    total=len(qs)
    passed=0
    for i,q in enumerate(qs):
        question=q["question"]
        sql,docs,err=generate_sql(question)
        valid,_=validate_sql(sql)
        if valid: passed+=1
        else: print(f"❌ {i+1}. {question} -> {sql} | err {err}")
    print(f"✅ {passed}/{total} valid SQL")

if __name__=="__main__":
    run_tests()
