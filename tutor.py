import traceback

from pymongo import MongoClient, errors
from fastapi import APIRouter
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from validation_functions import is_valid_phone, is_valid_email, is_valid_password, create_token, hash_text

client = MongoClient("mongodb://atlas-sql-68595ac755a50c4c1c0375eb-"
                     "tg2o9l.a.query.mongodb.net/sample_mflix?ssl=true&authSource=admin ")
registration = APIRouter()
db = client["Registration_database"]
tutor_registration = db["tutors"]
class Tutor(BaseModel):
    first_name:str
    second_name:str
    email:str
    phone_number:str
    password:str

class Login(BaseModel):
    first_name: str
    second_name: str
    password: str
@registration.post("/tutor/register")
def register_tutor(data:Tutor):
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
        tutor_registration.insert_one({"first_name": data.first_name, "second_name":data.second_name,
                                   "email":data.email, "phone_number":data.phone_number, "password": hashed_password})
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
    token_name = data.first_name + data.second_name
    token = create_token(token_name)
    return {"token": token,"message": "Welcome Start Teaching Now"}
@registration.post("/tutor/login")
def login_tutor(data:Login):
    valid, msg = is_valid_password(data.password)
    if not valid:
        raise HTTPException(status_code=401, detail=msg)



