import json
from crewai import Crew, Process, Task
from agents import build_agents
from models import QuizPack, EvaluationReport

def _raw(task):
    return task.output.raw if task.output else ""

def _structured(task, model_class):
    output = task.output
    if output and getattr(output, "pydantic", None):
        return output.pydantic
    if output and getattr(output, "json_dict", None):
        return model_class.model_validate(output.json_dict)
    if output:
        # A final fallback for providers that return valid JSON as raw text.
        raw = output.raw.strip()
        try:
            return model_class.model_validate_json(raw)
        except Exception:
            pass
    raise ValueError(f"Could not parse structured {model_class.__name__} output. Please retry.")

def run_lesson(topic, student_name, level, memory_text, weak_areas=None):
    coordinator, explainer, quiz_master, _ = build_agents()
    weak_areas = weak_areas or []

    coordinator_task = Task(
        description=(
            f"Student: {student_name}. Topic: {topic}. Level: {level}. "
            f"Student memory:\n{memory_text}\n"
            f"Known weak areas to consider: {weak_areas}\n\n"
            "Clarify the learning objective, identify 3-5 sub-concepts, and write a concise "
            "instruction brief for the Explainer and Quiz Master. If the topic is unclear or "
            "not a teachable academic topic, say so and suggest a clarification."
        ),
        expected_output="A concise learning brief with learning objectives, sub-concepts, level, and guidance.",
        agent=coordinator,
        markdown=True,
    )

    explainer_task = Task(
        description=(
            "Teach the student using the Coordinator's brief. Topic: {topic}. "
            "Student level: {level}. Name: {student_name}. "
            "Write a clear lesson with: overview, step-by-step explanation, at least two examples, "
            "common mistakes, and a short recap. Use beginner-friendly language where appropriate. "
            "Address these weak areas if present: {weak_areas}. Keep it focused and factually careful."
        ),
        expected_output="A complete, readable lesson in Markdown.",
        agent=explainer,
        context=[coordinator_task],
        markdown=True,
    )

    quiz_task = Task(
        description=(
            "Create exactly 5 multiple-choice questions based on the Explainer's lesson and "
            "the Coordinator's learning objectives. Topic: {topic}; learner level: {level}. "
            "Each question must have exactly four options and one correct answer. "
            "Use a mix of easy, medium, and hard questions. Do not make questions depend on facts "
            "that were not taught. Return the required structured output."
        ),
        expected_output="A structured quiz with exactly five MCQ questions, four options each, answer keys, and explanations.",
        agent=quiz_master,
        context=[coordinator_task, explainer_task],
        output_pydantic=QuizPack,
    )

    crew = Crew(
        agents=[coordinator, explainer, quiz_master],
        tasks=[coordinator_task, explainer_task, quiz_task],
        process=Process.sequential,
        verbose=True,
    )
    crew.kickoff(inputs={
        "topic": topic,
        "student_name": student_name,
        "level": level,
        "weak_areas": ", ".join(weak_areas) if weak_areas else "None",
    })

    return {
        "coordinator": _raw(coordinator_task),
        "lesson": _raw(explainer_task),
        "quiz": _structured(quiz_task, QuizPack),
    }

def evaluate_quiz(topic, student_name, quiz, answers, memory_text):
    _, _, _, evaluator = build_agents()

    quiz_data = quiz.model_dump()
    submitted = [
        {"question_number": i + 1, "question": q.question,
         "student_answer": answers.get(str(i), "No answer"),
         "correct_answer": q.correct_answer,
         "concept": q.concept, "explanation": q.explanation}
        for i, q in enumerate(quiz.questions)
    ]

    evaluation_task = Task(
        description=(
            f"Evaluate this student's quiz.\nStudent: {student_name}\nTopic: {topic}\n"
            f"Student memory:\n{memory_text}\n\n"
            f"Quiz and answer key:\n{json.dumps(quiz_data, ensure_ascii=False)}\n\n"
            f"Student submissions:\n{json.dumps(submitted, ensure_ascii=False)}\n\n"
            "Evaluate all questions. Be fair and consistent. For MCQs, compare the submitted "
            "option text with the correct answer. Score = correct_count / total_questions * 100, "
            "rounded to the nearest integer. Identify specific weak concepts and give actionable "
            "feedback. Return the required structured EvaluationReport."
        ),
        expected_output="A structured evaluation report with score, question feedback, strengths, and weak areas.",
        agent=evaluator,
        output_pydantic=EvaluationReport,
    )

    crew = Crew(
        agents=[evaluator],
        tasks=[evaluation_task],
        process=Process.sequential,
        verbose=True,
    )
    crew.kickoff()
    report = _structured(evaluation_task, EvaluationReport)

    # Calculate the final score from the Evaluator's per-question decisions.
    # This prevents an inconsistent total score from being returned by the LLM.
    if len(report.question_feedback) != len(quiz.questions):
        raise ValueError("Evaluator returned incomplete question feedback. Please retry.")

    report.total_questions = len(quiz.questions)
    report.correct_count = sum(1 for item in report.question_feedback if item.is_correct)
    report.score = round((report.correct_count / report.total_questions) * 100)
    return report
