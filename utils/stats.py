import json
from pathlib import Path
from datetime import datetime

STATS_FILE = Path("logs/stats.json")
STATS_FILE.parent.mkdir(parents=True, exist_ok=True)

# Обновляем статистику
def update_stats(user_id, username, action):
    stats = load_stats()

    stats["total_visits"] += 1
    stats["last_users"].append({
        "user_id": user_id,
        "username": username,
        "action": action,
        "time": datetime.now().isoformat()
    })

    if len(stats["last_users"]) > 20:
        stats["last_users"] = stats["last_users"][-20:]

    save_stats(stats)

def load_stats():
    if STATS_FILE.exists():
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"total_visits": 0, "last_users": []}

def save_stats(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
