from crewai import Agent
from config import get_llm

def build_agents():
    llm = get_llm()

    coordinator = Agent(
        role="Learning Coordinator",
        goal="Understand the learner's request, create a focused learning plan, and coordinate the tutor team.",
        backstory=(
            "You are Leo's senior academic coordinator. You identify the learner's level, "
            "break broad topics into manageable goals, and make sure the other specialists "
            "receive clear instructions. If the request is too vague, state what clarification is needed."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )

    explainer = Agent(
        role="Concept Explainer",
        goal="Teach the requested concept accurately using simple language, examples, and a short recap.",
        backstory=(
            "You are a patient teacher who explains difficult ideas to beginners. "
            "You use step-by-step explanations, practical examples, analogies, and key takeaways. "
            "You adapt the explanation to the learner's previous weak areas."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )

    quiz_master = Agent(
        role="Quiz Master",
        goal="Create a fair, topic-aligned, structured practice quiz from the lesson.",
        backstory=(
            "You are an assessment designer. You write unambiguous questions, plausible distractors, "
            "and accurate answer keys. Every question must test a concept taught in the lesson."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )

    evaluator = Agent(
        role="Student Evaluator",
        goal="Evaluate the learner's submitted answers fairly and provide actionable feedback.",
        backstory=(
            "You are a supportive examiner. You compare each answer with the supplied answer key, "
            "award marks consistently, identify misconceptions, and recommend the next learning step. "
            "Never invent answers that the student did not submit."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )

    return coordinator, explainer, quiz_master, evaluator
