import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import List

import bcrypt
from bson import ObjectId
from pymongo import MongoClient, errors
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from validation_functions import (
    is_valid_phone,
    is_valid_email,
    is_valid_password,
    create_token,
    hash_text,
    validate_token,
)

# DB Setup
client = MongoClient("mongodb://atlas-sql-68595ac755a50c4c1c0375eb-"
                     "tg2o9l.a.query.mongodb.net/sample_mflix?ssl=true&authSource=admin ")
student = APIRouter()
db = client["Registration_database"]
student_registration = db["student"]
user_db = client["User_database"]
user = user_db["user"]
assignment_db = client["Assignments_Database"]
course_collection = assignment_db["Course"]

# Models
class Student(BaseModel):
    name: str
    email: str
    phone_number: str
    password: str

class Login(BaseModel):
    name: str
    password: str

class Assignment(BaseModel):
    course_id: str
    topic: str
    exercise: str
    level: str
    tags: List[str]
    lesson_title: str

class Mark(BaseModel):
    id: str  # ObjectId string
    correction: str
    course_id: str

class Work(Enum):
    assignment = "Assignment"
    quiz = "quiz"

# Endpoints
@student.post("/student/register")
def register_student(data: Student):
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

    if student_registration.find_one({"email": data.email}):
        raise HTTPException(status_code=409, detail="Student already exists")

    hashed_password = hash_text(data.password)
    try:
        student_data = {
            "name": data.name,
            "email": data.email,
            "phone_number": data.phone_number,
            "password": hashed_password,
            "created_at": datetime.now(timezone.utc),
        }
        student_registration.insert_one(student_data)
        user.insert_one({**student_data, "Role": "Student"})
    except errors.PyMongoError as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    token = create_token(data.name)
    return {"token": token, "message": "Welcome, start learning now"}

@student.post("/student/login")
def login_student(data: Login):
    valid, msg = is_valid_password(data.password)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    user_ = student_registration.find_one({"name": data.name})
    if not user_:
        raise HTTPException(status_code=404, detail="User not found")

    stored = user_["password"].encode() if isinstance(user_["password"], str) else user_["password"]

    if bcrypt.checkpw(data.password.encode(), stored):
        token = create_token(data.name)
        return {"token": token, "message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Incorrect credentials")

@student.post("/student/doassignment")
def do_assignment(data: Assignment, valid=Depends(validate_token)):
    _, user_id = valid
    try:
        course_id = ObjectId(data.course_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid course ID format")

    course_doc = course_collection.find_one({"_id": course_id})
    if not course_doc:
        raise HTTPException(status_code=404, detail="Course not found")

    doc = {
        "student_id": user_id,
        "course_id": str(course_id),
        "course_title": course_doc.get("title"),
        "description": "Assignment",
        "content": data.exercise,
        "timestamp": datetime.now(timezone.utc)
    }
    course_collection.insert_one(doc)
    return {"message": "Assignment submitted successfully"}

@student.post("/student/takequiz")
def take_quiz(data: Assignment, wrk: Work = Query(...), valid=Depends(validate_token)):
    _, user_id = valid
    try:
        course_id = ObjectId(data.course_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid course ID format")

    course_doc = course_collection.find_one({"_id": course_id})
    if not course_doc:
        raise HTTPException(status_code=404, detail="Course not found")

    doc = {
        "student_id": user_id,
        "course_id": str(course_id),
        "course_title": course_doc.get("title"),
        "description": wrk.value,
        "content": data.exercise,
        "timestamp": datetime.now(timezone.utc)
    }
    course_collection.insert_one(doc)
    return {"message": "Quiz submitted successfully"}

@student.get("/student/viewresult")
def view_result(wrk: Work = Query(...), valid=Depends(validate_token)):
    return list(course_collection.find({"description": wrk.value, "correction": {"$exists": True}}, {"_id": 0}))

@student.get("/student/viewall")
def view_all(wrk: Work = Query(...), valid=Depends(validate_token)):
    return list(course_collection.find({"description": wrk.value}, {"_id": 0}))
