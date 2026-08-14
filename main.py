import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from google import genai
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

mongo_client = MongoClient(MONGODB_URI)

db = mongo_client["ai_career_companion"]
conversations_collection = db["conversations"]
profiles_collection = db["profiles"]

try:
    mongo_client.admin.command("ping")
    print("MongoDB connected successfully!")
except Exception as e:
    print("MongoDB connection failed:", e)


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class AIRequest(BaseModel):
    name: str
    question: str

class UserProfile(BaseModel):
    name: str
    education: str
    skills: str
    experience: str
    interests: str
    target_role: str | None = None

class CareerRole(BaseModel):
    role: str
    why: str
    skills_to_strengthen: list[str]


class CareerRecommendations(BaseModel):
    roles: list[CareerRole]

app = FastAPI()

conversation_history = {}

@app.get("/")
def home():
    return{"message":"welcome to AI Career Companion API!"}

@app.get("/about")
def about():
    return{
        "project": "AI Career Companion API",
        "developer": "Nachammai",
        "version": "1.0"
    }

@app.get("/hello")
def hello():
    return{"message": "Hello Naz! Welcome to FastAPI."}

@app.get("/student/{name}")
def student(name:str):
    return{
        "student_name": name,
        "message": f"welcome {name} !"
    }

@app.get("/college/{college_name}")
def college(college_name:str):
    return{
        "college_name":college_name,
        "message": f"Welcome to {college_name} !"
    }

@app.get("/greet")
def greet(name: str = "Guest"):
    return {
        "message": f"Hello {name}, welcome to AI Career Companion!"
    }

@app.get("/profile")
def profile(name: str = "Guest", age: int = 20):
    return{
        "name":name,
        "age":age
    }
@app.post("/career-profile")
def career_profile(profile: UserProfile):

    profiles_collection.update_one(
        {"name": profile.name},
        {"$set": profile.model_dump()},
        upsert=True
    )

    return {
        "message": "Career profile saved successfully",
        "profile": profile
    }

@app.get("/career-profile/{name}")
def get_career_profile(name: str):

    profile = profiles_collection.find_one(
        {"name": name},
        {"_id": 0}
    )

    if not profile:
        return {
            "message": "Career profile not found"
        }

    return {
        "message": "Career profile retrieved successfully",
        "profile": profile
    }

@app.get("/career-summary/{name}")
def career_summary(name: str):

    profile_data = profiles_collection.find_one(
        {"name": name},
        {"_id": 0}
    )

    if not profile_data:
        return {
            "message": "Career profile not found"
        }

    profile = UserProfile(**profile_data)

    return {
        "name": profile.name,
        "target_role": profile.target_role,
        "education": profile.education,
        "skills": profile.skills,
        "experience": profile.experience,
        "interests": profile.interests
    }


@app.post("/recommend-roles/{name}")
def recommend_roles(name: str):

    profile_data = profiles_collection.find_one(
        {"name": name},
        {"_id": 0}
    )

    if not profile_data:
        return {
            "message": "Career profile not found"
        }

    profile = UserProfile(**profile_data)

    prompt = f"""
    Analyze this user's career profile and recommend 3 to 5 suitable corporate job roles.

    Use ONLY the information provided below. Do not invent details.

    Education: {profile.education}
    Skills: {profile.skills}
    Experience: {profile.experience}
    Interests: {profile.interests}
    Target Role: {profile.target_role}

    For each role:
    - Give the role name
    - Explain briefly why it suits the user
    - List the important skills they should strengthen

    Keep the recommendations practical and concise.
    """

    response = gemini_client.interactions.create(
        model="gemini-3.5-flash",
        input=prompt,
        generation_config={
            "max_output_tokens": 2500
        },
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": CareerRecommendations.model_json_schema()
        }
    )

    return CareerRecommendations.model_validate_json(response.output_text)

@app.post("/ask-ai")
def ask_ai(request: AIRequest):

    if request.name not in conversation_history:
      conversation_history[request.name] = []

    profile_data = profiles_collection.find_one(
      {"name": request.name},
      {"_id": 0}
    )

    saved_conversations = conversations_collection.find(
      {"name": request.name}
    ).sort("_id", -1).limit(10)

    mongo_history = list(saved_conversations)
    mongo_history.reverse()


    response = gemini_client.interactions.create(
        model="gemini-3.5-flash",
        input=(
            "Career Profile:\n"
            + str(profile_data)
            + "\n\nPrevious Conversations:\n"
            + str(mongo_history)
            + "\n\nUser: "
            + request.question
        ),
        generation_config={
           "max_output_tokens": 1000
        },
        system_instruction="""
        You are AI Career Companion, a personal AI career assistant.

        Give clear, practical and personalized answers.
        Avoid unnecessary information, repetition and filler.
        Use bullet points or numbered lists when they improve clarity.
        Explain important points properly instead of giving incomplete answers.
        Give practical career guidance and suggestions when relevant.
        Keep simple questions short and explain complex questions sufficiently.
        Keep the entire response under 350 words.
        Do not include a career profile summary or a long introduction.
        Start directly with the recommended roles.
        """
    )

    answer = response.output_text

    conversation_history[request.name].append({
      "user": request.question,
      "ai": response.output_text
    })

    conversations_collection.insert_one({
       "name": request.name,
       "question": request.question,
       "answer": response.output_text
    })


    conversation_history[request.name] = conversation_history[request.name][-10:]

    return {
        "question": request.question,
        "answer": answer
    }
    
