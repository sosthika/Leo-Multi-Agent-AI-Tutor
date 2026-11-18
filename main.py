"""Optional command-line smoke test for Leo's multi-agent lesson workflow."""
from memory import get_student, memory_summary
from crew import run_lesson

if __name__ == "__main__":
    name = input("Student name: ").strip() or "Student"
    topic = input("Topic to learn: ").strip()
    level = input("Level (Beginner/Intermediate/Advanced): ").strip() or "Beginner"
    student = get_student(name)
    result = run_lesson(topic, name, level, memory_summary(student))
    print("\n=== COORDINATOR ===\n", result["coordinator"])
    print("\n=== EXPLAINER ===\n", result["lesson"])
    print("\n=== QUIZ MASTER ===\n", result["quiz"].model_dump_json(indent=2))
