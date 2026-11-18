import streamlit as st
from crew import run_lesson, evaluate_quiz
from memory import get_student, memory_summary, save_session

st.set_page_config(page_title="Leo — Multi-Agent AI Tutor", page_icon="🦁", layout="wide")

st.markdown("""
<style>
.main-title {font-size: 2.5rem; font-weight: 800; margin-bottom: 0;}
.sub-title {color: #8b949e; margin-top: .2rem;}
.agent-card {padding: 1rem; border: 1px solid rgba(128,128,128,.25); border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

st.title("🦁 Leo — Multi-Agent AI Tutor")
st.caption("Four AI specialists collaborate to teach, quiz, evaluate, and help you improve.")

if "stage" not in st.session_state:
    st.session_state.stage = "setup"
if "session" not in st.session_state:
    st.session_state.session = {}
if "last_error" not in st.session_state:
    st.session_state.last_error = None

with st.sidebar:
    st.header("About Leo")
    st.write("**Coordinator** — plans your session")
    st.write("**Explainer** — teaches the topic")
    st.write("**Quiz Master** — creates your quiz")
    st.write("**Evaluator** — checks your answers")
    st.divider()
    st.caption("Sequential CrewAI orchestration · Groq GPT-OSS 120B")
    if st.button("Start a new session", use_container_width=True):
        st.session_state.stage = "setup"
        st.session_state.session = {}
        st.session_state.last_error = None
        st.rerun()

def show_quiz(quiz, form_key, submit_label):
    with st.form(form_key):
        selected = {}
        for i, q in enumerate(quiz.questions):
            st.markdown(f"**Q{i+1}. {q.question}**")
            selected[str(i)] = st.radio(
                "Choose one answer:",
                options=q.options,
                index=None,
                key=f"{form_key}_q{i}",
                label_visibility="collapsed",
            )
            st.caption(f"Concept: {q.concept} · Difficulty: {q.difficulty}")
            st.divider()
        submitted = st.form_submit_button(submit_label, type="primary", use_container_width=True)
    return submitted, selected

def run_evaluation(quiz, answers, attempt):
    s = st.session_state.session
    student = get_student(s["student_name"])
    with st.spinner("🧑‍🏫 Evaluator is checking your answers..."):
        report = evaluate_quiz(
            s["topic"], s["student_name"], quiz, answers,
            memory_summary(student)
        )
    s[f"report_{attempt}"] = report
    s[f"answers_{attempt}"] = answers
    s["attempt"] = attempt
    if attempt == 1 and report.score < 70:
        st.session_state.stage = "reteach"
    else:
        st.session_state.stage = "results"
        save_session(
            s["student_name"], s["topic"], report.score,
            report.weak_areas, report.summary
        )

if st.session_state.stage == "setup":
    st.subheader("Start learning")
    with st.form("start_session"):
        student_name = st.text_input("Your name", placeholder="e.g. Alex")
        topic = st.text_input("What do you want to learn?", placeholder="e.g. Python OOP, DFA, photosynthesis")
        level = st.selectbox("Your current level", ["Beginner", "Intermediate", "Advanced"])
        start = st.form_submit_button("Start my lesson", type="primary", use_container_width=True)

    if start:
        if not student_name.strip() or not topic.strip():
            st.warning("Please enter your name and a topic.")
        else:
            st.session_state.session = {
                "student_name": student_name.strip(),
                "topic": topic.strip(),
                "level": level,
                "attempt": 1,
            }
            student = get_student(student_name)
            with st.status("Leo's agents are collaborating...", expanded=True) as status:
                try:
                    st.write("1/3 — Coordinator is planning the learning session.")
                    st.write("2/3 — Explainer is preparing your lesson.")
                    st.write("3/3 — Quiz Master is creating a structured quiz.")
                    result = run_lesson(
                        topic.strip(), student_name.strip(), level,
                        memory_summary(student)
                    )
                    status.update(label="Lesson and quiz are ready!", state="complete", expanded=False)
                    st.session_state.session.update(result)
                    st.session_state.stage = "lesson"
                    st.rerun()
                except Exception as exc:
                    status.update(label="Leo could not complete this session.", state="error")
                    st.error(f"Session error: {exc}")
                    st.info("Check your .env API key, internet connection, and package installation, then try again.")

elif st.session_state.stage == "lesson":
    s = st.session_state.session
    st.subheader(f"📘 Your lesson: {s['topic']}")
    with st.expander("Coordinator's learning plan", expanded=False):
        st.markdown(s["coordinator"])
    st.markdown(s["lesson"])
    st.success("The Quiz Master has prepared your practice quiz.")
    if st.button("Continue to quiz →", type="primary"):
        st.session_state.stage = "quiz"
        st.rerun()

elif st.session_state.stage == "quiz":
    s = st.session_state.session
    st.subheader(f"📝 Quiz: {s['topic']}")
    st.caption("Answer all questions. Your answers will be sent to Leo's Evaluator.")
    submitted, answers = show_quiz(s["quiz"], "first_quiz", "Submit answers")
    if submitted:
        if any(value is None for value in answers.values()):
            st.warning("Please answer every question before submitting.")
        else:
            try:
                run_evaluation(s["quiz"], answers, 1)
                st.rerun()
            except Exception as exc:
                st.error(f"Evaluation error: {exc}. Please try submitting again.")

elif st.session_state.stage == "reteach":
    s = st.session_state.session
    report = s["report_1"]
    st.subheader("🔁 Leo's bonus feedback loop")
    st.warning(f"Your first score was {report.score}%. Leo will revisit the concepts that need more practice.")
    st.markdown("**Evaluator's feedback**")
    st.write(report.summary)
    st.write("**Concepts to revisit:** " + (", ".join(report.weak_areas) or "Review the lesson once more."))
    if st.button("Ask Explainer to re-teach and create a new quiz", type="primary"):
        student = get_student(s["student_name"])
        with st.status("Explainer and Quiz Master are working on your improvement...", expanded=True) as status:
            try:
                retry = run_lesson(
                    s["topic"], s["student_name"], s["level"],
                    memory_summary(student),
                    weak_areas=report.weak_areas
                )
                status.update(label="Your targeted revision and second quiz are ready!", state="complete")
                s["retry_lesson"] = retry["lesson"]
                s["retry_quiz"] = retry["quiz"]
                st.session_state.stage = "retry_quiz"
                st.rerun()
            except Exception as exc:
                status.update(label="Re-teaching could not be completed.", state="error")
                st.error(f"Feedback loop error: {exc}")

elif st.session_state.stage == "retry_quiz":
    s = st.session_state.session
    st.subheader("📚 Targeted revision")
    st.markdown(s["retry_lesson"])
    st.divider()
    st.subheader("Second quiz")
    submitted, answers = show_quiz(s["retry_quiz"], "second_quiz", "Submit second quiz")
    if submitted:
        if any(value is None for value in answers.values()):
            st.warning("Please answer every question.")
        else:
            try:
                run_evaluation(s["retry_quiz"], answers, 2)
                st.rerun()
            except Exception as exc:
                st.error(f"Evaluation error: {exc}. Please try again.")

elif st.session_state.stage == "results":
    s = st.session_state.session
    report = s[f"report_{s['attempt']}"]
    st.subheader("🏆 Your learning report")
    col1, col2, col3 = st.columns(3)
    col1.metric("Final score", f"{report.score}%")
    col2.metric("Correct answers", f"{report.correct_count}/{report.total_questions}")
    col3.metric("Attempts", s["attempt"])
    st.progress(report.score / 100)
    st.markdown("### Evaluator's summary")
    st.write(report.summary)
    left, right = st.columns(2)
    with left:
        st.markdown("**Strengths**")
        for item in report.strengths:
            st.write(f"✅ {item}")
    with right:
        st.markdown("**Areas to improve**")
        for item in report.weak_areas:
            st.write(f"📌 {item}")
    st.markdown("### Question-by-question feedback")
    for item in report.question_feedback:
        icon = "✅" if item.is_correct else "❌"
        with st.expander(f"{icon} Question {item.question_number} — {item.concept}"):
            st.write(f"Your answer: {item.student_answer}")
            st.write(f"Correct answer: {item.correct_answer}")
            st.write(item.feedback)
    st.info(report.recommendation)
    if s["attempt"] == 2:
        first = s["report_1"]
        st.caption(f"Progress: first attempt {first.score}% → second attempt {report.score}%")
    st.success("Your session has been saved to Leo's local student memory.")
    with st.expander("View saved learning history"):
        student = get_student(s["student_name"])
        st.json(student)
    if st.button("Learn another topic", type="primary"):
        st.session_state.stage = "setup"
        st.session_state.session = {}
        st.rerun()
