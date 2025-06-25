import traceback
from datetime import datetime, timezone

import bcrypt
from fastapi.params import Depends
from pymongo import MongoClient, errors
from fastapi import HTTPException, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from tutor import user
from validation_functions import is_valid_phone, is_valid_email, is_valid_password, create_token, hash_text, validate_token

client = MongoClient("mongodb://atlas-sql-68595ac755a50c4c1c0375eb-"
                     "tg2o9l.a.query.mongodb.net/sample_mflix?ssl=true&authSource=admin ")
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # ⚠️ "*" only allowed when...
    allow_credentials=False,  # ...credentials are False
    allow_methods=["*"],
    allow_headers=["*"],
)
db = client["Admin_database"]
admin_collection = db["Admin"]
course_collection = db["Course"]

class Admin(BaseModel):
    name: str
    email: str
    phone_number: str
    password: str

class Login(BaseModel):
    name: str
    password: str

class Course(BaseModel):
    title: str
    description: str
    instructor: str
    lessons: str
    lesson_title: str
    content: str
    tags: list
    level: str

@app.post("/admin/register")
def register_admin(data: Admin):
    validators = {
        "phone": is_valid_phone,
        "email": is_valid_email,
        "password": is_valid_password
    }

    for field, validator in validators.items():
        value = getattr(data, field, None)
        valid, msg = validator(value)
        if not valid:
            raise HTTPException(status_code=401, detail=msg)

    hashed_password = hash_text(data.password)
    try:
        admin_data = {
            "name": data.name,
            "email": data.email,
            "phone_number": data.phone_number,
            "password": hashed_password,
            "created_at": datetime.now(timezone.utc),
        }
        admin_collection.insert_one(admin_data)
        user.insert_one({**admin_data, "Role": "Admin"})
    except errors.DuplicateKeyError:
        traceback.print_exc()
        raise HTTPException(status_code=409, detail="Resource already exists")
    except errors.OperationFailure:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail="Bad request")
    except errors.ConfigurationError:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Configuration error")
    except errors.ConnectionFailure:
        traceback.print_exc()
        raise HTTPException(status_code=503, detail="Service unavailable")
    except errors.PyMongoError:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Unexpected database error")

    token = create_token(data.name)
    return {"token": token, "message": "Beware thy actions — the script watches you."}

@app.post("/admin/login")
def login_admin(data: Login):
    valid, msg = is_valid_password(data.password)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    user_ = admin_collection.find_one({"name": data.name})
    if not user_:
        raise HTTPException(status_code=404, detail="Admin not found")

    stored = user_["password"].encode() if isinstance(user_["password"], str) else user_["password"]

    if bcrypt.checkpw(data.password.encode(), stored):
        token = create_token(data.name)
        return {"token": token, "message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Incorrect credentials")

@app.post("/create/course")
def create_course(data: Course, valid=Depends(validate_token)):
    doc = {
        "title": data.title,
        "description": data.description,
        "instructor": data.instructor,
        "lessons": data.lessons,
        "lesson_title": data.lesson_title,
        "content": data.content,
        "tags": data.tags,
        "level": data.level,
        "created_at": datetime.now(timezone.utc)
    }
    try:
        course_collection.insert_one(doc)
        return {"message": "Course created successfully"}
    except errors.PyMongoError as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to create course: " + str(e))

