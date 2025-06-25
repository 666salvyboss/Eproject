from fastapi import FastAPI

import validation_functions
from tutor import registration
from student import student
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
@app.get("/")
def main():
    return {"message":"server is up"}
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # ⚠️ "*" only allowed when...
    allow_credentials=False,  # ...credentials are False
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(registration)
app.include_router(student)