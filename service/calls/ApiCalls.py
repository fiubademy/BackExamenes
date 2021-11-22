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


@router.get('/{exam_id}/questions')
async def getQuestionsForExam(exam_id: str):
    exam_questions = session.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id)
    if not exam_questions.first():
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "That exam has no questions in the database.")
    return_message = []
    for question in exam_questions:
        if question.question_type != 'DES':
            list_choices = []
            choices = session.query(ChoiceResponse).filter(ChoiceResponse.question_id == question.question_id)
            for choice in choices:
                list_choices.append(
                    {
                        "Number": choice.choice_number,
                        "Content": choice.choice_content,
                        "Correct": choice.correct
                    }
                )
            return_message.append(
                {
                    "QuestionID": question.question_id, 
                    "ExamID": question.exam_id, 
                    "QuestionContent": question.question_content, 
                    "QuestionType": question.question_type,
                    "ChoiceOptions": list_choices
                }
            )
        else:
            return_message.append(
                {
                    "QuestionID": question.question_id, 
                    "ExamID": question.exam_id, 
                    "QuestionContent": question.question_content, 
                    "QuestionType": question.question_type
                }
            )
    return JSONResponse(status_code = status.HTTP_200_OK, content = return_message)


@router.get('/student/{user_id}/student_response/{question_id}')
async def getStudentResponseForQuestion(question_id: str, user_id: str):
    student_response = session.query(UserResponse).filter(UserResponse.question_id == question_id and UserResponse.us).first()
    if not student_response:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "User " + user_id + " has not responded to question " + question_id)
    return JSONResponse(status_code = status.HTTP_200_OK, content = student_response)


@router.patch('/edit_exam/{exam_id}')
async def editExam(exam_id:str, exam_date:datetime):
    exam = session.query(Exam).filter(Exam.exam_id == exam_id).first()
    if not exam:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "Exam with ID " + exam_id + " was not found in the database.")
    exam.exam_date = exam_date
    session.add(exam)
    session.commit()
    return JSONResponse(status_code = status.HTTP_202_ACCEPTED, content = "Exam with ID " + exam_id + " was correctly modified.")
    


@router.patch('/edit_question/{question_id}')
async def editExamQuestions(question_id:str, question_content: questionsContent):
    if question_content.question_type != 'DES' and not question_content.choice_responses:
        return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = "Can not send a question different of DES without choice options...")
    elif question_content.question_type != 'DES' and question_content.choice_responses != None:     
        num_choices_correct = 0
        for choice_response in question_content.choice_responses:
            if choice_response.correct == 'Y':
                num_choices_correct += 1
        if num_choices_correct > 1 and (question_content.question_type == 'VOF' or question_content.question_type == 'SC'):
            return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = 'Incorrect quantity of correct responses in VOF or SC. Must be only one')
        if len(question_content.choice_responses) != 2 and question_content.question_type == 'VOF': 
            return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = "True or False question has more than 2 possible options.")
    question = session.query(ExamQuestion).filter(ExamQuestion.question_id == question_id).first()
    if not question:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "Question with id " + question_id + " does not exist in the database.")
    if question_content.question_type == 'DES':
        session.query(ChoiceResponse).filter(ChoiceResponse.question_id == question_id).delete()
        session.commit()
    question.question_type = question_content.question_type
    question.question_content = question_content.question_content
    for choice_response in question_content.choice_responses:
        session.add(
                        ChoiceResponse(
                            question_id = question_id,
                            choice_number = choice_response.number,
                            choice_content = choice_response.content,
                            correct = choice_response.correct
                        )
                    )
    session.commit()
    session.add(question)
    session.commit()
    return JSONResponse(status_code = status.HTTP_202_ACCEPTED, content = "Question " + question_id + " has been correctly modified.")


@router.post('/{exam_id}/answer')
async def postAnswersExam(exam_id:str , question_id: str , response_content: Optional[str] = None , choice_number: Optional[int] = None):
    if response_content == None and choice_number == None:
        return JSONResponse(status_code = status.HTTP_422_VALIDATION_ERROR, content = "Response Content and Choice Number can not be None together.")
    if response_content != None and choice_number != None:
        return JSONResponse(status_code = status.HTTP_422_VALIDATION_ERROR, content = "Response Content and Choice Number can not have a value together.")
    try:
        if response_content == None:
            response_content = null()
        if choice_number == None:
            choice_number = null()
        session.add(UserResponse(exam_id , question_id, response_content , choice_number))
        session.commit()
    except Exception as e:
        session.rollback()
        return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = 'Exception raised when response was submitted: ' + str(e))
    return JSONResponse(
        status_code = status.HTTP_200_OK, 
        content = {
            "exam_id":exam_id, 
            "question_id":question_id, 
            "response_content": response_content, 
            "choice_number":choice_number
            }
    )
    

@router.delete('/{exam_id}')
async def deleteExam(exam_id: str):
    if not session.query(Exam).filter(Exam.exam_id == exam_id).first():
        return JSONResponse (status_code = status.HTTP_404_NOT_FOUND, content = "Exam with ID " + exam_id + " does not exist in the database.")
    questions = session.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id)
    for question in questions:
        session.query(ChoiceResponse).filter(ChoiceResponse.question_id == question.question_id).delete()
    session.commit()
    session.query(ExamQuestion).filter(ExamQuestion.exam_id == exam_id).delete()
    session.commit()
    session.query(Exam).filter(Exam.exam_id == exam_id).delete()
    session.commit()
    return JSONResponse(status_code = status.HTTP_200_OK, content = "Exam with ID " + exam_id + " has been correctly deleted.")


@router.delete('/questions/{question_id}')
async def deleteExam(question_id: str):
    if not session.query(ExamQuestion).filter(ExamQuestion.question_id == question_id).first():
        return JSONResponse (status_code = status.HTTP_404_NOT_FOUND, content = "Question with ID " + question_id + " does not exist in the database.")
    session.query(ChoiceResponse).filter(ChoiceResponse.question_id == question_id).delete()
    session.commit()
    session.query(ExamQuestion).filter(ExamQuestion.question_id == question_id).delete()
    session.commit()
    return JSONResponse(status_code = status.HTTP_200_OK, content = "Question with ID " + question_id + " has been correctly deleted.")

