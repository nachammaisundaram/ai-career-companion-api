import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from openai import OpenAI
from google import genai
from pymongo import MongoClient
from PyPDF2 import PdfReader

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

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


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

class SkillGap(BaseModel):
    skill: str
    current_level: str
    importance: str
    reason: str


class SkillGapAnalysis(BaseModel):
    target_role: str
    skill_gaps: list[SkillGap]
    priority_skills: list[str]
    learning_plan: list[str]

class RoadmapStep(BaseModel):
    phase: str
    focus: str
    skills: list[str]
    projects: list[str]
    outcome: str

class CareerRoadmap(BaseModel):
    target_role: str
    roadmap_duration: str
    steps: list[RoadmapStep]

class ResumeAnalysis(BaseModel):
    summary: str
    skills: list[str]
    strengths: list[str]
    missing_skills: list[str]
    suggestions: list[str]

class AIResponse(BaseModel):
    answer: str
    key_points: list[str]
    next_steps: list[str]


app = FastAPI()


@app.get("/")
def home():
    return {
        "message": "welcome to AI Career Companion API!"
    }


@app.get("/about")
def about():
    return {
        "project": "AI Career Companion API",
        "developer": "Nachammai",
        "version": "1.0"
    }


@app.get("/hello")
def hello():
    return {
        "message": "Hello Naz! Welcome to FastAPI."
    }


@app.get("/student/{name}")
def student(name: str):
    return {
        "student_name": name,
        "message": f"welcome {name} !"
    }


@app.get("/college/{college_name}")
def college(college_name: str):
    return {
        "college_name": college_name,
        "message": f"Welcome to {college_name} !"
    }


@app.get("/greet")
def greet(name: str = "Guest"):
    return {
        "message": f"Hello {name}, welcome to AI Career Companion!"
    }


@app.get("/profile")
def profile(name: str = "Guest", age: int = 20):
    return {
        "name": name,
        "age": age
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

    profile_data = profiles_collection.find_one(
        {"name": name},
        {"_id": 0}
    )

    if not profile_data:
        return {
            "message": "Career profile not found"
        }

    return {
        "message": "Career profile retrieved successfully",
        "profile": profile_data
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


def generate_recommendations(profile: UserProfile):

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

    return CareerRecommendations.model_validate_json(
        response.output_text
    )

def analyze_skill_gap(profile: UserProfile):

    prompt = f"""
    Analyze this user's career profile and identify the most important skill gaps
    for their target role.

    Use ONLY the information provided below.
    Do not invent skills, experience, certifications, or achievements.

    Education: {profile.education}
    Skills: {profile.skills}
    Experience: {profile.experience}
    Interests: {profile.interests}
    Target Role: {profile.target_role}

    Identify practical skills the user should strengthen for their target role.

    For each skill gap:
    - Give the skill name
    - Estimate the user's current level
    - Give its importance
    - Briefly explain why the skill matters

    Also provide:
    - The highest-priority skills
    - A practical learning plan

    Keep everything concise and suitable for a fresher.
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
            "schema": SkillGapAnalysis.model_json_schema()
        }
    )

    return SkillGapAnalysis.model_validate_json(
        response.output_text
    )

def generate_career_roadmap(profile: UserProfile):

    prompt = f"""
    Create a practical career roadmap for this user.

    Use ONLY the information provided below.
    Do not invent qualifications, experience, or achievements.

    Education: {profile.education}
    Skills: {profile.skills}
    Experience: {profile.experience}
    Interests: {profile.interests}
    Target Role: {profile.target_role}

    Create a realistic roadmap for a fresher targeting the user's target role.

    Divide the roadmap into clear learning phases.

    For each phase provide:
    - Phase name
    - Main focus
    - Skills to learn or strengthen
    - Practical projects to build
    - Expected outcome

    Keep the roadmap practical and concise.
    Focus on skills and projects that can improve employability.
    """

    response = gemini_client.interactions.create(
        model="gemini-3.5-flash",
        input=prompt,
        generation_config={
            "max_output_tokens": 3000
        },
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": CareerRoadmap.model_json_schema()
        }
    )

    return CareerRoadmap.model_validate_json(
        response.output_text
    )

def analyze_resume(resume_text: str, target_role: str | None = None):

    prompt = f"""
    Analyze the following resume for a fresher.

    Target Role:
    {target_role}

    Resume Text:
    {resume_text}

    Use ONLY the information present in the resume.
    Do not invent qualifications, skills, experience, or achievements.

    Provide:
    - A brief resume summary
    - Skills explicitly found in the resume
    - The candidate's strengths based on the resume
    - Skills or areas that appear to be missing or need strengthening for the target role
    - Practical suggestions for improvement

    Keep the analysis concise and useful for a fresher.
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
            "schema": ResumeAnalysis.model_json_schema()
        }
    )

    return ResumeAnalysis.model_validate_json(
        response.output_text
    )

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

    return generate_recommendations(profile)

@app.post("/skill-gap/{name}")
def skill_gap(name: str):

    profile_data = profiles_collection.find_one(
        {"name": name},
        {"_id": 0}
    )

    if not profile_data:
        return {
            "message": "Career profile not found. Please create your career profile first."
        }

    profile = UserProfile(**profile_data)

    return analyze_skill_gap(profile)

@app.post("/career-roadmap/{name}")
def career_roadmap(name: str):

    profile_data = profiles_collection.find_one(
        {"name": name},
        {"_id": 0}
    )

    if not profile_data:
        return {
            "message": "Career profile not found. Please create your career profile first."
        }

    profile = UserProfile(**profile_data)

    return generate_career_roadmap(profile)

@app.post("/upload-resume/{name}")
async def upload_resume(name: str, file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):
        return {
            "message": "Only PDF resumes are supported."
        }

    profile_data = profiles_collection.find_one(
        {"name": name},
        {"_id": 0}
    )

    if not profile_data:
        return {
            "message": "Career profile not found. Please create your career profile first."
        }

    profile = UserProfile(**profile_data)

    contents = await file.read()

    with open("temp_resume.pdf", "wb") as resume_file:
        resume_file.write(contents)

    reader = PdfReader("temp_resume.pdf")

    resume_text = ""

    for page in reader.pages:
        text = page.extract_text()

        if text:
            resume_text += text + "\n"

    if not resume_text.strip():
        return {
            "message": "Could not extract text from the uploaded PDF."
        }

    analysis = analyze_resume(
        resume_text,
        profile.target_role
    )

    return {
        "filename": file.filename,
        "target_role": profile.target_role,
        "analysis": analysis
    }

@app.post("/ask-ai")
def ask_ai(request: AIRequest):

    profile_data = profiles_collection.find_one(
        {"name": request.name},
        {"_id": 0}
    )

    if not profile_data:
      return {
         "message": "Career profile not found. Please create your career profile first."
        }

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
            "max_output_tokens": 2000
        },
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": AIResponse.model_json_schema()
        },
        system_instruction="""
        You are AI Career Companion, a personal AI career assistant.

        Give clear, practical and personalized answers.

        Return the response in this exact structure:
        - answer: A clear answer to the user's question.
        - key_points: Important points related to the answer.
        - next_steps: Practical actions the user can take next.

        Keep the response concise and useful.
        Do not include unnecessary information.
        """
    )

    ai_response = AIResponse.model_validate_json(
        response.output_text
    )

    conversations_collection.insert_one({
        "name": request.name,
        "question": request.question,
        "answer": ai_response.answer
    })

    return {
        "question": request.question,
        "answer": ai_response.answer,
        "key_points": ai_response.key_points,
        "next_steps": ai_response.next_steps
    }