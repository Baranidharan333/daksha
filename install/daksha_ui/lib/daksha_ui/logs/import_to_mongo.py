import json
import pymongo
from pymongo import MongoClient
import os

def main():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['telemetry_db']
    
    # Store system_telemetry.json as the latest state
    state_collection = db['latest_state']
    
    state_file = '/home/jetson/Documents/logs/dataset/system_telemetry.json'
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state_data = json.load(f)
            state_collection.replace_one({'_id': 'latest'}, {'_id': 'latest', **state_data}, upsert=True)
            print("Inserted latest state data.")
    
    # Store telemetry_history.jsonl
    history_collection = db['history']
    documents = []
    history_file = '/home/jetson/Documents/logs/dataset/telemetry_history.jsonl'
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    documents.append(json.loads(line))
                
        if documents:
            history_collection.insert_many(documents)
            print(f"Inserted {len(documents)} records into telemetry_db.history")

if __name__ == '__main__':
    main()
