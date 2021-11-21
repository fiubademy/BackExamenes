from fastapi import status
from typing import List, Optional
from pydantic import EmailStr
from starlette.responses import JSONResponse
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.sql import null
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Models.Models import *
import uuid
import hashlib

router = APIRouter()
Session = None
session = None
engine = None

def set_engine(engine_rcvd):
    global engine
    global Session
    global session
    engine = engine_rcvd
    Session = sessionmaker(bind=engine)
    session = Session()

@router.get('/course/{course_id}', status_code = status.HTTP_200_OK)
async def getExamByCourses(course_id: str):
    exams = session.query(Exam).filter(Exam.course_id == course_id)
    if not exams.first():
        return JSONResponse(
            status_code = status.HTTP_404_NOT_FOUND, 
            content = 'No exams in course ' + course_id + ' were found in the DataBase.'
        )
    returnList = []
    for exam in exams:
        returnList.append(
            {
                'ExamID': exam.exam_id, 
                'CourseID': exam.course_id,
                'Date': exam.exam_date.strftime('%d/%m/%y %H:%M')
            }
        )
    return JSONResponse(
        status_code = status.HTTP_200_OK, 
        content = returnList
    )


@router.get('/{exam_id}', status_code=status.HTTP_200_OK)
async def getExamById(exam_id: str):
    exam = session.query(Exam).filter(Exam.exam_id == exam_id).first()
    if not exam:
        return JSONResponse(
            status_code = status.HTTP_404_NOT_FOUND, 
            content = 'Exam with id ' + exam_id + ' was not found in the DataBase.'
        )
    return JSONResponse(
        status_code = status.HTTP_200_OK, 
        content = {
                'ExamID': exam.exam_id, 
                'CourseID': exam.course_id,
                'Date': exam.exam_date.strftime('%d/%m/%y %H:%M')
            }
    )


def rollback_exam_creation(exam_id):
    session.rollback()
    questions = session.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id)
    for examQuestion in questions:
        session.query(ChoiceResponse).filter(ChoiceResponse.question_id == examQuestion.question_id).delete()
        session.commit()
        session.query(ExamQuestion).filter(ExamQuestion.question_id == examQuestion.question_id).delete()
        session.commit()
    session.query(Exam).filter(Exam.exam_id == exam_id).delete()
    session.commit()


@router.post('/create_exam/{course_id}')
async def createExam(course_id: str, questionsList: List[questionsContent], examDate: datetime):
    exam_id = str(uuid.uuid4())
    try:
        session.add(Exam(exam_id = exam_id, course_id = course_id, exam_date = examDate))
        session.commit()
    except Exception as e:
        session.rollback()
        return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = 'Exception raised when creating exam: ' + str(e))
    for question in questionsList:
        question_id = str(uuid.uuid4())
        try:
            session.add(
                ExamQuestion(
                    exam_id = exam_id, 
                    question_id = question_id, 
                    question_type = question.question_type, 
                    question_content = question.question_content
                )
            )
            session.commit()
        except Exception as e:
            rollback_exam_creation(exam_id)
            return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = 'Exception raised when creating question: ' + str(e))
        if question.choice_responses != None:
            num_choices_correct = 0
            for choice_response in question.choice_responses:
                if choice_response.correct == 'Y':
                    num_choices_correct += 1
                try:
                    if num_choices_correct > 1 and (question.question_type == 'VOF' or question.question_type == 'SC'):
                        raise Exception('Incorrect quantity of correct responses in VOF or SC.')

                    if len(question.choice_responses) != 2 and question.question_type == 'VOF': 
                        raise Exception("True or False question has more than 2 possible options.")
                
                    session.add(
                        ChoiceResponse(
                            question_id = question_id,
                            choice_number = choice_response.number,
                            choice_content = choice_response.content,
                            correct = choice_response.correct
                        )
                    )
                    session.commit()
                except Exception as e:
                    rollback_exam_creation(exam_id)
                    return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = 'Exception raised when creating choice response: ' + str(e))
            if num_choices_correct == 0:
                 rollback_exam_creation(exam_id)
                 return JSONResponse(status_Code = status.HTTP_400_BAD_REQUEST, content = 'Choice answers with no correct answer has been found.')
    return JSONResponse(status_code = status.HTTP_200_OK, content = {"exam_id":exam_id, "course_id":course_id, "exam_date": examDate.strftime('%d/%m/%y %H:%M')})

