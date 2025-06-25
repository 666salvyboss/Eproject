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
registration = APIRouter()
db = client["Registration_database"]
tutor_registration = db["tutors"]
user_db = client["User_database"]
user = user_db["user"]
assignment_db = client["Assignments_Database"]
course_collection = assignment_db["Course"]

# Models
class Tutor(BaseModel):
    name: str
    email: str
    phone_number: str
    password: str

class Login(BaseModel):
    name: str
    password: str

class Assignment(BaseModel):
    course: str
    topic: str
    exercise: str
    level: str
    tags: List[str]
    lesson_title: str

class Mark(BaseModel):
    id: str  # ObjectId string
    correction: str
    course: str

class Work(Enum):
    assignment = "Assignment"
    quiz = "quiz"

# Endpoints
@registration.post("/tutor/register")
def register_tutor(data: Tutor):
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

    if tutor_registration.find_one({"email": data.email}):
        raise HTTPException(status_code=409, detail="Tutor already exists")

    hashed_password = hash_text(data.password)
    try:
        tutor_data = {
            "name": data.name,
            "email": data.email,
            "phone_number": data.phone_number,
            "password": hashed_password,
            "created_at": datetime.now(timezone.utc),
        }
        tutor_registration.insert_one(tutor_data)
        user.insert_one({**tutor_data, "Role": "Tutor"})
    except errors.PyMongoError as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    token = create_token(data.name)
    return {"token": token, "message": "Welcome Start Teaching Now"}

@registration.post("/tutor/login")
def login_tutor(data: Login):
    valid, msg = is_valid_password(data.password)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)

    user_ = tutor_registration.find_one({"name": data.name})
    if not user_:
        raise HTTPException(status_code=404, detail="User not found")

    stored = user_["password"].encode() if isinstance(user_["password"], str) else user_["password"]

    if bcrypt.checkpw(data.password.encode(), stored):
        token = create_token(data.name)
        return {"token": token, "message": "login successful"}
    else:
        raise HTTPException(status_code=401, detail="Details not found")

@registration.post("/tutor/giveassignment")
def give_assignment(data: Assignment, valid=Depends(validate_token)):
    _, user_id = valid
    if not course_collection.find_one({"title": data.course}):
        raise HTTPException(status_code=404, detail="Course Not Found")

    doc = {
        "tutor_id": user_id,
        "course": data.course,
        "title": data.lesson_title,
        "content": data.exercise,
        "tags": data.tags,
        "level": data.level,
        "description": "Assignment",
         "timestamp": datetime.now(timezone.utc)
    }
    result = course_collection.insert_one(doc)
    return {"course_id": str(result.inserted_id), "message": "Assignment submitted successfully"} # cache course id autoinput asif token for backeend refrence

@registration.post("/tutor/givequiz")
def give_quiz(data: Assignment, wrk: Work = Query(...), valid=Depends(validate_token)):
    _, user_id = valid
    if not course_collection.find_one({"title": data.course}):
        raise HTTPException(status_code=404, detail="Course Not Found")

    doc = {
        "description": wrk.value,
        "tutor_id": user_id,
        "course": data.course,
        "title": data.lesson_title,
        "content": data.exercise,
        "tags": data.tags,
        "level": data.level,
        "timestamp": datetime.now(timezone.utc)
    }
    result = course_collection.insert_one(doc)
    return {"course_id": str(result.inserted_id), "message": "Quiz submitted successfully"}

@registration.post("/tutor/mark")
def mark(data: Mark, wrk: Work = Query(...), valid=Depends(validate_token)):
    _, user_id = valid
    course_doc = course_collection.find_one({"title": data.course})
    if not course_doc:
        raise HTTPException(status_code=404, detail="Course Not Found")

    try:
        course_id = course_collection.find_one({"_id": ObjectId(data.id)})
        if not course_id:
            raise HTTPException(status_code=404, detail="Assignment Not Found")

        correction_doc = {
            "description": wrk.value,
            "tutor_id": user_id,
            "correction": data.correction,
            "timestamp": datetime.now(timezone.utc)
        }
        course_collection.insert_one(correction_doc)
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail="Invalid ID")

    return {"message": "Successfully marked"}

@registration.get("/tutor/viewall")
def view_all( wrk: Work = Query(...),valid=Depends(validate_token)):
    return list(course_collection.find({"description": [i for i in wrk.value]}, {"_id": 0}))

