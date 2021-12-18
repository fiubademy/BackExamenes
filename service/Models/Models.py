from typing import List, Optional
from pydantic import EmailStr
from pydantic.main import BaseModel
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float, CheckConstraint
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from baseService.Database import Base


class ExamReturn(BaseModel):
    ExamID: str
    CourseID: str
    Date: datetime


class QuestionReturn(BaseModel):
    QuestionID: str
    ExamID: str
    Question: str


class QuestionResponseReturn(BaseModel):
    ExamID: str
    QuestionID: str
    StudentID: str
    Response: str


class OptionForQuestionReturn(BaseModel):
    number: int
    content: str
    #correct: str


class questionsContent(BaseModel):
    question_type: str
    question_content: str
    choice_responses: Optional[List[OptionForQuestionReturn]]


class Exam(Base):
    __tablename__ = "exams"
    exam_id = Column(String, primary_key = True, nullable = False)
    exam_title = Column(String, nullable = False)
    course_id = Column(String, nullable = False)
    exam_date = Column(DateTime, nullable = False)
    status = Column(String, nullable = False)


class ExamQuestion(Base):
    __tablename__ = "exams_questions"
    question_id = Column(String, primary_key = True, nullable = False)
    exam_id = Column(String, ForeignKey('exams.exam_id') ,nullable = False)
    question_type = Column(String, nullable = False)
    question_content = Column(String, nullable = False)


class ChoiceResponse(Base):
    __tablename__ = "choice_responses"
    question_id = Column(String, ForeignKey('exams_questions.question_id'), primary_key = True)
    choice_number = Column(Integer, primary_key = True, nullable = False)
    choice_content = Column(String, nullable = False)
    

class UserResponse(Base):
    __tablename__ = "user_responses"
    exam_id = Column(String, ForeignKey('exams.exam_id'), nullable = False)
    user_id = Column(String, primary_key = True, nullable = False)
    question_id = Column(String, ForeignKey('exams_questions.question_id'), primary_key = True, nullable = False)
    response_content = Column(String, nullable = False)
    date_answered = Column(DateTime, nullable = False)


class ExamMark(Base):
    __tablename__ = "exams_marks"
    exam_id = Column(String, ForeignKey('exams.exam_id'), primary_key = True, nullable = False)
    student_id = Column(String, primary_key = True, nullable = False)
    mark = Column(Float, nullable = False)
    comments = Column(String)
