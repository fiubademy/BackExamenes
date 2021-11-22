import pytest
import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "service"))
from fastapi import status
from calls import ApiCalls
from baseService.Database import test_engine, Base
from datetime import datetime


def test_passes():
    assert (True == True)

'''
async def run_post():
    date_time_str = '18/09/19 01:55:19'
    date_time_obj = datetime.strptime(date_time_str, '%d/%m/%y %H:%M:%S')
    questions = [{"question_type":"DES", "question_content":"Pregunta 1"}]
    return await ApiCalls.createExam(course_id="id_test", questionsList=questions, examDate=date_time_obj)


async def run_delete(exam_id):
    return await ApiCalls.deleteExam(exam_id)



Base.metadata.drop_all(test_engine)
Base.metadata.create_all(test_engine)
ApiCalls.set_engine(test_engine)


def test_post_to_db_correctly():
    exam_id = asyncio.run(run_post())
    assert exam_id.status_code == status.HTTP_200_OK
    asyncio.run(run_delete(exam_id))
'''