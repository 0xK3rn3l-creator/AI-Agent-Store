import json
import os
from datetime import datetime

os.makedirs("logs", exist_ok=True)

def log_step(step_name: str, details: dict):
    """Пише трейс виконання у файл logs/trace.jsonl"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "step": step_name,
        "details": details
    }
    with open("logs/trace.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
