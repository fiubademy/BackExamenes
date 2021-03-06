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

from starlette.status import HTTP_201_CREATED
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
async def getExamByCourses(course_id: str, exam_status: Optional[str] = ''):
    exams = session.query(Exam).filter(Exam.course_id == course_id).filter(Exam.status.like('%'+exam_status.upper()+'%'))
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
                'Date': exam.exam_date.isoformat(), # exam.exam_date.strftime('%d/%m/%y %H:%M'),
                'ExamTitle': exam.exam_title,
                'Status': exam.status
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
                'Date': exam.exam_date.isoformat(), # exam.exam_date.strftime('%d/%m/%y %H:%M'),
                'ExamTitle': exam.exam_title,
                'Status': exam.status
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
async def createExam(course_id: str, examDate: datetime, examTitle: str, questionsList: Optional[List[questionsContent]] = None):
    exam_id = str(uuid.uuid4())
    try:
        session.add(Exam(exam_id = exam_id, course_id = course_id, exam_date = examDate, exam_title = examTitle, status='EDITION'))
        session.commit()
    except Exception as e:
        session.rollback()
        return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = 'Exception raised when creating exam: ' + str(e))
    if questionsList != None:
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
                #num_choices_correct = 0
                for choice_response in question.choice_responses:
                    #if choice_response.correct == 'Y':
                    #    num_choices_correct += 1
                    try:
                        #if num_choices_correct > 1 and (question.question_type == 'VOF' or question.question_type == 'SC'):
                        #    raise Exception('Incorrect quantity of correct responses in VOF or SC.')

                        if len(question.choice_responses) != 2 and question.question_type == 'VOF': 
                            raise Exception("True or False question has more than 2 possible options.")
                    
                        session.add(
                            ChoiceResponse(
                                question_id = question_id,
                                choice_number = choice_response.number,
                                choice_content = choice_response.content
                                #correct = choice_response.correct
                            )
                        )
                        session.commit()
                    except Exception as e:
                        rollback_exam_creation(exam_id)
                        return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = 'Exception raised when creating choice response: ' + str(e))
                #if num_choices_correct == 0:
                #     rollback_exam_creation(exam_id)
                #     return JSONResponse(status_Code = status.HTTP_400_BAD_REQUEST, content = 'Choice answers with no correct answer has been found.')
    return JSONResponse(
        status_code = status.HTTP_200_OK, 
        content = {
            "exam_id":exam_id, 
            "course_id":course_id, 
            "exam_date": examDate.isoformat(), # examDate.strftime('%d/%m/%y %H:%M'), 
            'ExamTitle': examTitle
        }
    )


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
                        #"Correct": choice.correct
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
    student_response = session.query(UserResponse).filter(UserResponse.question_id == question_id).filter(UserResponse.user_id == user_id).first()
    if not student_response:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "User " + user_id + " has not responded to question " + question_id)
    return JSONResponse(
        status_code = status.HTTP_200_OK, 
        content = {
            'exam_id': student_response.exam_id,
            'user_id' : student_response.user_id,
            'question_id': student_response.question_id,
            'response_content': student_response.response_content
        }
    )


@router.patch('/edit_exam/{exam_id}')
async def editExam(exam_id:str, exam_date:datetime = None, exam_title: str = None):
    exam = session.query(Exam).filter(Exam.exam_id == exam_id).first()
    if not exam:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "Exam with ID " + exam_id + " was not found in the database.")
    if exam.status != 'EDITION':
        return JSONResponse(status_code = status.HTTP_403_FORBIDDEN, content = "Exam is currently not in edition status and cannot be edited.")
    if exam_date != None:
        exam.exam_date = exam_date
    if exam_title != None:
        exam.exam_title = exam_title
    session.add(exam)
    session.commit()
    return JSONResponse(status_code = status.HTTP_202_ACCEPTED, content = "Exam with ID " + exam_id + " was correctly modified.")
    


@router.patch('/edit_question/{question_id}')
async def editExamQuestions(question_id:str, question_content: questionsContent):
    if question_content.question_type != 'DES' and not question_content.choice_responses:
        return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = "Can not send a question different of DES without choice options...")
    elif question_content.question_type != 'DES' and question_content.choice_responses != None:     
        #num_choices_correct = 0
        #for choice_response in question_content.choice_responses:
            #if choice_response.correct == 'Y':
            #    num_choices_correct += 1
        #if num_choices_correct > 1 and (question_content.question_type == 'VOF' or question_content.question_type == 'SC'):
        #    return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = 'Incorrect quantity of correct responses in VOF or SC. Must be only one')
        if len(question_content.choice_responses) != 2 and question_content.question_type == 'VOF': 
            return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = "True or False question has more than 2 possible options.")
    question = session.query(ExamQuestion).filter(ExamQuestion.question_id == question_id).first()
    if not question:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "Question with id " + question_id + " does not exist in the database.")
    exam = session.query(Exam).filter(Exam.exam_id == question.exam_id).first()
    if exam.status != 'EDITION':
        return JSONResponse(status_code = status.HTTP_403_FORBIDDEN, content = "Exam is currently not in edition status and cannot be edited.")
    #if question_content.question_type == 'DES':
    session.query(ChoiceResponse).filter(ChoiceResponse.question_id == question_id).delete()
    session.commit()
    question.question_type = question_content.question_type
    question.question_content = question_content.question_content
    if question_content.choice_responses != None:
        for choice_response in question_content.choice_responses:
            session.add(
                            ChoiceResponse(
                                question_id = question_id,
                                choice_number = choice_response.number,
                                choice_content = choice_response.content,
                                #correct = choice_response.correct
                            )
                        )
    session.commit()
    session.add(question)
    session.commit()
    return JSONResponse(status_code = status.HTTP_202_ACCEPTED, content = "Question " + question_id + " has been correctly modified.")


@router.post('/{exam_id}/answer/{question_id}')
async def postAnswersExam(exam_id:str , question_id: str, user_id:str, response_content: str):
    if session.query(UserResponse).filter(UserResponse.exam_id == exam_id).filter(UserResponse.question_id == question_id).filter(
        UserResponse.user_id == user_id).first() != None: 
            if session.query(ExamMark).filter(ExamMark.student_id == user_id and ExamMark.exam_id == exam_id).first() != None:
                # The user is redoing the exam because his previous try has been already corrected and he is answering again.
                session.query(UserResponse).filter(UserResponse.exam_id == exam_id).filter(UserResponse.user_id == user_id).delete()
                session.query(ExamMark).filter(ExamMark.exam_id == exam_id).filter(ExamMark.student_id == user_id).delete()
                session.commit()
            else:
                return JSONResponse(status_code = status.HTTP_403_FORBIDDEN, content = "User has already responded to this exam and has yet not been graded.")
        
    try:
        session.add(UserResponse(
            exam_id = exam_id, 
            question_id = question_id, 
            user_id = user_id, 
            response_content = response_content,
            date_answered = datetime.now()))
        session.commit()
    except Exception as e:
        session.rollback()
        return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = 'Exception raised when response was submitted: ' + str(e))
    return JSONResponse(
        status_code = status.HTTP_200_OK, 
        content = {
            "exam_id":exam_id, 
            "question_id":question_id, 
            "response_content": response_content
        }
    )

@router.delete('/responses/{user_id}/{question_id}')
async def deleteUserResponse(user_id: str, question_id:str):
    if not session.query(UserResponse).filter(UserResponse.user_id == user_id).filter(UserResponse.question_id == question_id).first():
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "User " + user_id + " has no responses for question " + question_id)
    session.query(UserResponse).filter(UserResponse.user_id == user_id).filter(UserResponse.question_id == question_id).delete()
    session.commit()
    return JSONResponse(status_code = status.HTTP_200_OK, content= "Response from user "+user_id+" was deleted sucessfuly for question " + question_id)


@router.delete('/marks/{user_id}/{exam_id}')
async def deleteExamMark(user_id: str, exam_id:str):
    if not session.query(ExamMark).filter(ExamMark.student_id == user_id).filter(ExamMark.exam_id == exam_id).first():
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "User " + user_id + " has no mark for exam " + exam_id)
    session.query(ExamMark).filter(ExamMark.student_id == user_id).filter(ExamMark.exam_id == exam_id).delete()
    session.commit()
    return JSONResponse(status_code = status.HTTP_200_OK, content= "Mark from user "+user_id+" was deleted sucessfuly for exam " + exam_id)
    

@router.delete('/{exam_id}')
async def deleteExam(exam_id: str):
    if not session.query(Exam).filter(Exam.exam_id == exam_id).first():
        return JSONResponse (status_code = status.HTTP_404_NOT_FOUND, content = "Exam with ID " + exam_id + " does not exist in the database.")
    session.query(ExamMark).filter(ExamMark.exam_id == exam_id).delete()
    session.commit()
    session.query(UserResponse).filter(UserResponse.exam_id == exam_id).delete()
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
async def deleteQuestion(question_id: str):
    question = session.query(ExamQuestion).filter(ExamQuestion.question_id == question_id).first()
    if not question:
        return JSONResponse (status_code = status.HTTP_404_NOT_FOUND, content = "Question with ID " + question_id + " does not exist in the database.")
    exam = session.query(Exam).filter(Exam.exam_id == question.exam_id).first()
    if exam.status != 'EDITION':
        return JSONResponse(status_code = status.HTTP_403_FORBIDDEN, content = "Exam is currently not in edition status and cannot be edited.")
    session.query(ChoiceResponse).filter(ChoiceResponse.question_id == question_id).delete()
    session.commit()
    session.query(ExamQuestion).filter(ExamQuestion.question_id == question_id).delete()
    session.commit()
    return JSONResponse(status_code = status.HTTP_200_OK, content = "Question with ID " + question_id + " has been correctly deleted.")


@router.post('/{exam_id}/add_question')
async def addQuestion(exam_id: str , question: questionsContent):
    exam = session.query(Exam).filter(Exam.exam_id == exam_id).first()
    if exam.status != 'EDITION':
        return JSONResponse(status_code = status.HTTP_403_FORBIDDEN, content = "Exam is currently not in edition status and cannot be edited.")
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
        return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = 'Exception raised when creating question: ' + str(e))
    if question.choice_responses != None:
        #num_choices_correct = 0
        for choice_response in question.choice_responses:
            #if choice_response.correct == 'Y':
            #    num_choices_correct += 1
            try:
                #if num_choices_correct > 1 and (question.question_type == 'VOF' or question.question_type == 'SC'):
                #    raise Exception('Incorrect quantity of correct responses in VOF or SC.')

                if len(question.choice_responses) != 2 and question.question_type == 'VOF': 
                    raise Exception("True or False question has more than 2 possible options.")
            
                session.add(
                    ChoiceResponse(
                        question_id = question_id,
                        choice_number = choice_response.number,
                        choice_content = choice_response.content,
                        #correct = choice_response.correct
                    )
                )
                session.commit()
            except Exception as e:
                session.rollback()
                session.query(ChoiceResponse).filter(ChoiceResponse.question_id == question_id).delete()
                session.commit()
                session.query(ExamQuestion).filter(ExamQuestion.question_id == question_id).delete()
                session.commit()
                return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = 'Exception raised when creating choice response: ' + str(e))
        #if num_choices_correct == 0:
        #    session.rollback()
        #    session.query(ChoiceResponse).filter(ChoiceResponse.question_id == question_id).delete()
        #    session.commit()
        #    session.query(ExamQuestion).filter(ExamQuestion.question_id == question_id).delete()
        #    session.commit()
        #    return JSONResponse(status_Code = status.HTTP_400_BAD_REQUEST, content = 'Choice answers with no correct answer has been found.')
    return JSONResponse(status_code = status.HTTP_200_OK, content = {"question_id": question_id, "exam_id": exam_id})


@router.post('/{exam_id}/qualify/{user_id}')
async def qualifyExam(user_id: str, exam_id: str, mark: float, comments: str):
    if not session.query(Exam).filter(Exam.exam_id == exam_id).first():
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "Exam with id " + exam_id + " does not exist in the database." )
    if mark < 0 or mark > 10:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content = "Mark must be a float between 0 and 10")
    if session.query(ExamMark).filter(ExamMark.student_id == user_id).filter(ExamMark.exam_id == exam_id).first() != None:
        return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = "Student " + user_id + " has been already graded in this exam.")
    session.add(ExamMark(exam_id = exam_id, student_id = user_id, mark = mark, comments = comments))
    try:
        session.commit()
    except Exception as e:
        return JSONResponse(status_code = status.HTTP_403_FORBIDDEN, content = "Exception raised when commiting mark into database: " + str(e))
    return JSONResponse(status_code = status.HTTP_201_CREATED, content = "Student " + user_id + " was graded with " + str(mark) + " in exam " + exam_id + " correctly.")


@router.get('/{exam_id}/is_able_to_do_exam/{user_id}')
async def is_able_to_do_exam(exam_id: str, user_id: str):
    if session.query(UserResponse).filter(UserResponse.exam_id == exam_id).filter(UserResponse.user_id == user_id).first() != None: 
        if session.query(ExamMark).filter(ExamMark.student_id == user_id and ExamMark.exam_id == exam_id).first() == None:
            return JSONResponse(status_code = status.HTTP_406_NOT_ACCEPTABLE, content=False)
        else:
            return JSONResponse(status_code = status.HTTP_200_OK, content=True)
    return JSONResponse(status_code = status.HTTP_200_OK, content = True)


@router.patch('/{exam_id}/publish')
async def publish_exam(exam_id: str):
    exam = session.query(Exam).filter(Exam.exam_id == exam_id).first()
    if not exam:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "Exam with id " + exam_id + " does not exist in the database." )
    exam.status = 'PUBLISHED'
    session.add(exam)
    session.commit()
    return JSONResponse(status_code= status.HTTP_200_OK, content= "Exam with id" + exam_id + " was correctly published")


@router.get('/{exam_id}/students_who_answered')
async def get_students_that_answered_exam(exam_id: str):
    if not session.query(Exam).filter(Exam.exam_id == exam_id).first():
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "That exam does not exist.")
    students = []
    students_query = session.query(UserResponse).filter(UserResponse.exam_id == exam_id)
    if not students_query.first():
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "No users have answered this exam yet.")
    for student in students_query:
        if student.user_id not in students:
            students.append(student.user_id)
    return JSONResponse(status_code = status.HTTP_200_OK, content = students)


def check_student_in_list(student, students):
    for student_in_list in students:
        if student_in_list['student_id'] == student.student_id:
            return True
    return False


def check_student_in_list_user_response(student, students_list):
    for student_in_list in students_list:
        if student_in_list['student_id'] == student.user_id:
            return True
    return False


@router.get('/{exam_id}/students_with_qualification')
async def get_students_that_have_qualifications(exam_id: str, student_id: Optional[str]=''):
    if not session.query(Exam).filter(Exam.exam_id == exam_id).first():
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "That exam does not exist.")
    students = []
    students_query = session.query(ExamMark).filter(ExamMark.exam_id == exam_id).filter(ExamMark.student_id.like('%' + student_id + '%'))
    if students_query.first() == None:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "No qualificated students were found.")
    for student in students_query:
        if not check_student_in_list(student, students):
            students.append({'student_id': student.student_id, 'mark': student.mark, 'comments': student.comments})
    return JSONResponse(status_code = 200, content = students)


@router.get('/{exam_id}/students_without_qualification')
async def get_students_that_dont_have_qualifications(exam_id: str):
    if not session.query(Exam).filter(Exam.exam_id == exam_id).first():
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "That exam does not exist.")

    # Obtengo los usuarios que respondieron y tienen nota
    students_with_mark = []
    students_query = session.query(ExamMark).filter(ExamMark.exam_id == exam_id)
    for student in students_query:
        if student not in students_with_mark:
            students_with_mark.append(student.student_id)

    # Obtengo a los que respondieron pero filtrando aquellos que tienen nota
    students_answered_without_mark = []
    students_query = session.query(UserResponse).filter(UserResponse.exam_id == exam_id)
    if not students_query.first():
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "No users have answered this exam yet.")
    for student in students_query:
        if not check_student_in_list_user_response(student, students_answered_without_mark) and student.user_id not in students_with_mark:
            students_answered_without_mark.append({'student_id': student.user_id, 'date_answered': student.date_answered.isoformat()})
    return JSONResponse(status_code = 200, content = students_answered_without_mark)


@router.get('/{course_id}/student_state/{user_id}')
async def get_student_state_in_course(course_id:str, user_id:str):
    courseExams = session.query(Exam.exam_id).filter(Exam.course_id == course_id).filter(Exam.status == "PUBLISHED")
    exams_quantity = courseExams.count()
    if exams_quantity == 0:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content="Course has no exams in it")
    exam_marks = session.query(ExamMark).filter(ExamMark.student_id == user_id).filter(ExamMark.exam_id.in_(courseExams))
    quantity_marked = exam_marks.count()
    passed = True
    quantity_not_passed = 0
    average = 0
    if quantity_marked == 0:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = "User has no marks in exam yet")
    for mark in exam_marks:
        if mark.mark < 6:
            passed = False
            quantity_not_passed += 1
        average += mark.mark
    if quantity_marked > 0:
        average = average/quantity_marked
    if quantity_marked < exams_quantity or not passed:
        return JSONResponse(
            status_code = status.HTTP_200_OK, 
            content = {
                "status": "Unfinished", 
                "average_mark": average, 
                "exams_not_passed": exams_quantity - quantity_marked + quantity_not_passed # Aun no completados, o desaprobados
            }
        )
    if passed and quantity_marked == exams_quantity:
        return JSONResponse(status_code = status.HTTP_200_OK, content = {"status": "Finished", "average_mark": average, "exams_not_passed": 0})
