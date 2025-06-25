import traceback
from datetime import datetime, timezone

import bcrypt
from fastapi.params import Depends
from pymongo import MongoClient, errors
from fastapi import APIRouter
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from tutor import user
from validation_functions import is_valid_phone, is_valid_email, is_valid_password, create_token, hash_text, \
    validate_token

client = MongoClient("mongodb://atlas-sql-68595ac755a50c4c1c0375eb-"
                     "tg2o9l.a.query.mongodb.net/sample_mflix?ssl=true&authSource=admin ")
admin_registration = APIRouter()
db = client["Admin_database"]
tutor_registration = db["Admin"]
course = db["Course"]
class Admin(BaseModel):
    name:str
    email:str
    phone_number:str
    password:str

class Login(BaseModel):
    name: str
    password: str

class Course(BaseModel):
    title:str
    description:str
    instructor:str
    lessons:str
    lesson_title:str
    content:str
    tags:list
    level:str
@admin_registration.post("/admin/register")
def register_admin(data:Admin):
    valid, msg = is_valid_phone(data.phone_number)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)
    valid, msg = is_valid_email(data.email)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)
    valid, msg = is_valid_password(data.password)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)
    hashed_password = hash_text(data.password)
    try:
        tutor_registration.insert_one({"name": data.name, "email":data.email, "phone_number":data.phone_number, "password": hashed_password, "created_at":datetime.now(timezone.utc)})
        user.insert_one({"name": data.name, "email": data.email, "password": hashed_password, "Role": "Student", "created_at":datetime.now(timezone.utc)})
    except errors.DuplicateKeyError:
        traceback.print_exc()
        raise HTTPException(status_code=409, detail="Resource already exists")
    except errors.OperationFailure:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail="Bad request")
    except errors.ConfigurationError:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Oops thats on us we'll start fixing that")
    except errors.ConnectionFailure:
        traceback.print_exc()
        raise HTTPException(status_code=503, detail="service unavailable")
    except errors.PyMongoError:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="something broke")
    token = create_token(data.name)
    return {"token": token,"message": "Beware thy actions the script watches you"}

@admin_registration.post("admin/login")
def login_admin(data:Login):
    valid, msg = is_valid_password(data.password)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)
    user_ = tutor_registration.find_one({"username": data.name})
    if not user_:
        return False
    stored = user_["password"]
    # Convert back to bytes if necessary
    if isinstance(stored, str):
        stored = stored.encode()
    if bcrypt.checkpw(data.password.encode(), stored):
        token = create_token(data.name)
        return {"token": token, "message": "login successful"}
    else:
        raise HTTPException(status_code=401, detail="Details  not found")
@admin_registration.post("/create/course")
def create_course(data:Course,valid=Depends(validate_token)):
    docs = [{
        "title": data.title,
        "description": data.description,
        "instructor": data.instructor,

        "created_at": datetime.now(timezone.utc)
    }]
    course.insert_one(docs[0])



