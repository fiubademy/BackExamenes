from fastapi import FastAPI, status
from typing import List, Optional
from pydantic import EmailStr
from pydantic.main import BaseModel
from starlette.responses import JSONResponse
import uvicorn
import uuid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert
from sqlalchemy.orm.exc import NoResultFound
import os

DATABASE_URL = "postgresql://fwvgbztmprfrsw:4ebcc733023c58076b68c792d8d918de53b41869d659cb729ab1408bc7658c11@ec2-44-198-29-193.compute-1.amazonaws.com:5432/dmkfrcjs45li0"

engine = create_engine(DATABASE_URL)
Base = declarative_base()

app = FastAPI()

class ExamResponse(BaseModel):
    ExamId: int  # TODO: Armar este modelo

@app.get('/exams', response_model = List[ExamResponse], status_code=status.HTTP_200_OK)
async def getExams():  # TODO: Filtros
    return [{'ExamId': 1}]  # Hardcoded para probar

Session = sessionmaker(bind=engine)
session = Session()

if __name__ == '__main__':
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    uvicorn.run(app, host='0.0.0.0', port=8001)