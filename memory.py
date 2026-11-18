import json
from pathlib import Path
from datetime import datetime, timezone

MEMORY_PATH = Path(__file__).parent / "data" / "student_memory.json"

def load_memory():
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not MEMORY_PATH.exists():
        return {}
    try:
        return json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # Recover gracefully if the memory file is damaged.
        return {}

def get_student(student_name):
    data = load_memory()
    return data.get(student_name.strip().lower(), {
        "display_name": student_name.strip(),
        "topics_studied": [],
        "weak_areas": [],
        "sessions": []
    })

def save_session(student_name, topic, score, weak_areas, summary):
    data = load_memory()
    key = student_name.strip().lower()
    student = data.get(key, {
        "display_name": student_name.strip(),
        "topics_studied": [],
        "weak_areas": [],
        "sessions": []
    })

    student["display_name"] = student_name.strip()
    if topic not in student["topics_studied"]:
        student["topics_studied"].append(topic)

    existing = set(student.get("weak_areas", []))
    existing.update(weak_areas or [])
    student["weak_areas"] = sorted(existing)

    student["sessions"].append({
        "topic": topic,
        "score": int(score),
        "summary": summary,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    data[key] = student
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def memory_summary(student):
    if not student.get("sessions"):
        return "This is the student's first recorded Leo session."
    recent = student["sessions"][-5:]
    lines = [
        f"Previously studied topics: {', '.join(student.get('topics_studied', [])) or 'None'}",
        f"Known weak areas: {', '.join(student.get('weak_areas', [])) or 'None recorded'}",
        "Recent sessions:"
    ]
    for item in recent:
        lines.append(f"- {item['topic']}: {item['score']}% — {item.get('summary', '')}")
    return "\n".join(lines)
