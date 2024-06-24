from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    user_email: str
    question_index: int
    user_responses: list

class ChatResponse(BaseModel):
    reply: str
    next_question_index: int
    current_question: str = None

init_prompt = "You are Remy, a user's personal assistant who learns user preferences and details about their eating habits and helps them in anything related to kitchen."

# Define the initial hardcoded questions
initial_questions = [
    "What is your favorite cuisine?",
    "Do you have any food allergies?",
    "What are your dietary preferences/restrictions?",
    "What is your daily calorie intake goal?",
    "Can you tell me what you currently have in your pantry?"
]

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_email = request.user_email  # Use user email to track state
    question_index = request.question_index
    user_responses = request.user_responses
    
    if question_index < len(initial_questions):
        question = initial_questions[question_index]
        reply = question
        next_question_index = question_index + 1
        return ChatResponse(reply=reply, next_question_index=next_question_index, current_question=question)
    else:
        # Include user responses in the prompt
        responses = "\n".join([f"User: {resp['answer']}\nRemy: {resp['question']}" for resp in user_responses])
        full_prompt = f"{init_prompt}\n{responses}\nUser: {request.message}\nRemy:"
        try:
            response = openai.Completion.create(
                engine="gpt-3.5-turbo-instruct",
                prompt=full_prompt,
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.9,
            )

            reply = response.choices[0].text.strip()
            return ChatResponse(reply=reply, next_question_index=question_index)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))