from pydantic import BaseModel, Field
from typing import List

class QuizQuestion(BaseModel):
    question: str = Field(description="A clear question about the lesson.")
    options: List[str] = Field(description="Exactly four answer options.")
    correct_answer: str = Field(description="The exact text of the correct option.")
    explanation: str = Field(description="Why the correct answer is correct.")
    concept: str = Field(description="The concept being tested.")
    difficulty: str = Field(description="Easy, Medium, or Hard.")

class QuizPack(BaseModel):
    title: str
    instructions: str
    questions: List[QuizQuestion]

class QuestionEvaluation(BaseModel):
    question_number: int
    is_correct: bool
    student_answer: str
    correct_answer: str
    feedback: str
    concept: str

class EvaluationReport(BaseModel):
    score: int = Field(ge=0, le=100)
    total_questions: int
    correct_count: int
    summary: str
    strengths: List[str]
    weak_areas: List[str]
    question_feedback: List[QuestionEvaluation]
    recommendation: str
