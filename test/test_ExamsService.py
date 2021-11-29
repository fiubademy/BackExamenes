import pytest
import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "service"))
from fastapi import status
from calls import ApiCalls
from baseService.Database import test_engine, Base
from baseService.ExamsService import app
from datetime import datetime
from fastapi.testclient import TestClient

client= TestClient(app)
Base.metadata.drop_all(test_engine)
Base.metadata.create_all(test_engine)
ApiCalls.set_engine(test_engine)

def test_create_exam():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    exam_id = content['exam_id']
    assert content['course_id'] == 'id_curso'
    assert content['exam_date'] == "02/12/22 21:33"
    client.delete('/exams/'+exam_id)
    

def test_create_various_exams_in_same_course():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == status.HTTP_200_OK
    response_two = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-14T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]'
    )
    assert response_two.status_code == status.HTTP_200_OK
    client.delete('/exams/'+response.json()['exam_id'])
    client.delete('/exams/'+response_two.json()['exam_id'])


def test_get_exam_by_id():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == 200
    content_post = response.json()
    content_get = client.get('/exams/'+content_post['exam_id'])
    assert content_get.status_code == 200
    content_get = content_get.json()
    assert content_get['CourseID'] == content_post['course_id']
    assert content_get['ExamID'] == content_post['exam_id']
    assert content_get['Date'] == content_post['exam_date']
    assert content_get['ExamTitle'] == content_post['ExamTitle']
    client.delete('/exams/'+content_get['ExamID'])


def test_get_exam_by_id_not_existent():
    response = client.get('/exams/NO_EXISTO')
    assert response.status_code == 404


def test_get_exam_by_course():
    response = client.post(
        '/exams/create_exam/id_curso_test?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == 200
    content_post = response.json()
    content_get = client.get('/exams/course/id_curso_test')
    assert content_get.status_code == 200
    content_get = content_get.json()
    assert content_get[0]['CourseID'] == content_post['course_id']
    assert content_get[0]['ExamID'] == content_post['exam_id']
    assert content_get[0]['Date'] == content_post['exam_date']
    client.delete('/exams/'+content_get[0]['ExamID'])


def test_get_exam_by_course_not_existent():
    response = client.get('/exams/course/NO_EXISTO')
    assert response.status_code == 404


def test_create_question():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = 
            '[{"question_type": "DES", "question_content": "Pregunta 1"}]'
    )
    assert response.status_code == 200 
    content_post = response.json()
    content_post_question = client.post('/exams/'+content_post['exam_id'] + '/add_question' , 
        data = '{"question_type": "DES", "question_content": "Pregunta 1"}' 
    )
    assert content_post_question.status_code == 200
    content_post_question = content_post_question.json()
    question_id = content_post_question['question_id']
    questions_got = client.get('/exams/'+content_post['exam_id']+'/questions')
    assert questions_got.status_code == 200
    questions_got = questions_got.json()
    assert questions_got[1]['QuestionID'] == question_id
    client.delete('/exams/'+content_post['exam_id'])
    

def test_get_questions():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = 
            '['+
                '{"question_type": "DES", "question_content": "Pregunta 1"},'+
                '{"question_type": "VOF", "question_content": "Verd o Fal", '+
                    '"choice_responses": ['+
                        '{"number": 0, "content": "ASD", "correct": "Y"},'+
                        '{"number": 1, "content": "Wepa", "correct": "N"}'+
                    ']'
                '}'+
            ']'
    )
    assert response.status_code == 200
    content_post = response.json()
    questions_got = client.get('/exams/'+content_post['exam_id']+'/questions')
    assert questions_got.status_code == 200
    questions_got = questions_got.json()
    assert questions_got[0]['QuestionContent'] == "Pregunta 1"
    assert questions_got[0]['QuestionType'] == "DES"
    assert questions_got[0]['ExamID'] == content_post['exam_id']
    assert questions_got[1]['QuestionContent'] == "Verd o Fal"
    assert questions_got[1]['QuestionType'] == "VOF"
    assert questions_got[1]['ExamID'] == content_post['exam_id']
    assert questions_got[1]['ChoiceOptions'][0]['Number'] == 0
    assert questions_got[1]['ChoiceOptions'][0]['Content'] == 'ASD'
    assert questions_got[1]['ChoiceOptions'][0]['Correct'] == 'Y'
    assert questions_got[1]['ChoiceOptions'][1]['Number'] == 1
    assert questions_got[1]['ChoiceOptions'][1]['Content'] == 'Wepa'
    assert questions_got[1]['ChoiceOptions'][1]['Correct'] == 'N'
    client.delete('/exams/'+content_post['exam_id'])


def test_get_questions_not_existent():
    questions_got = client.get('/exams/NO_EXISTO/questions')
    assert questions_got.status_code == 404


def test_delete_exam():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == 200
    content_post = response.json()
    response_delete = client.delete('/exams/'+content_post['exam_id'])
    assert response_delete.status_code == 200
    content_get = client.get('/exams/'+content_post['exam_id'])
    assert content_get.status_code == 404


def test_delete_exam_not_existent():
    response = client.delete('/exams/NO_EXISTO')
    assert response.status_code == 404

def test_delete_question():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = 
            '['+
                '{"question_type": "DES", "question_content": "Pregunta 1"},'+
                '{"question_type": "VOF", "question_content": "Verd o Fal", '+
                    '"choice_responses": ['+
                        '{"number": 0, "content": "ASD", "correct": "Y"},'+
                        '{"number": 1, "content": "Wepa", "correct": "N"}'+
                    ']'
                '}'+
            ']'
    )
    assert response.status_code == 200
    content_post = response.json()
    questions_got = client.get('/exams/'+content_post['exam_id']+'/questions')
    assert questions_got.status_code == 200
    questions_got = questions_got.json()
    taminio = len(questions_got)
    client.delete('/exams/questions/'+questions_got[1]['QuestionID'])
    content_post = response.json()
    questions_got = client.get('/exams/'+content_post['exam_id']+'/questions')
    assert questions_got.status_code == 200
    questions_got = questions_got.json()
    taminio2 = len(questions_got)
    assert taminio2 < taminio 
    client.delete('/exams/'+content_post['exam_id'])

def test_delete_question_not_existent():
    response = client.delete('/exams/questions/NO_EXIST')
    assert response.status_code == 404


def test_edit_exam():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    url = '/exams/edit_exam/'+content['exam_id']+'?exam_date=2012-12-22T21:45:33&exam_title=tituloEditado'
    response_edit = client.patch(url)
    assert response_edit.status_code == status.HTTP_202_ACCEPTED
    content_edit = client.get('/exams/'+content['exam_id']).json()
    assert content_edit['Date'] == '22/12/12 21:45'
    assert content_edit['ExamTitle'] == 'tituloEditado'
    client.delete('/exams/'+content['exam_id'])


def test_edit_exam_not_existent():
    url = '/exams/edit_exam/NO_EXISTO?exam_date=2012-12-22T21:45:33'
    response_edit = client.patch(url)
    assert response_edit.status_code == status.HTTP_404_NOT_FOUND


def test_edit_question():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    initial_questions = client.get('/exams/'+content['exam_id']+'/questions').json()
    url = '/exams/edit_question/'+initial_questions[0]['QuestionID']
    patch_response = client.patch(url,
        data =      
            '{'+
                '"question_type": "MC", '+
                '"question_content": "Mult Choice", '+
                '"choice_responses": ['+
                    '{"number": 0, "content": "Choice #1", "correct": "Y"},'+
                    '{"number": 1, "content": "Choice #2", "correct": "N"},'+
                    '{"number": 2, "content": "Choice #3", "correct": "Y"}'+
                ']'
            '}'
    )
    assert patch_response.status_code == status.HTTP_202_ACCEPTED
    next_questions = client.get('/exams/'+content['exam_id']+'/questions').json()

    assert len(initial_questions) == 1
    assert initial_questions[0]['QuestionContent'] == 'Pregunta 1'
    assert initial_questions[0]['QuestionType'] == 'DES'
    assert initial_questions[0]['ExamID'] == content['exam_id']

    assert len(next_questions) == 1
    assert next_questions[0]['QuestionContent'] == 'Mult Choice'
    assert next_questions[0]['QuestionType'] == 'MC'
    assert next_questions[0]['ExamID'] == content['exam_id']
    assert next_questions[0]['ChoiceOptions'][0]['Number'] == 0
    assert next_questions[0]['ChoiceOptions'][0]['Correct'] == 'Y'
    assert next_questions[0]['ChoiceOptions'][0]['Content'] == 'Choice #1'
    assert next_questions[0]['ChoiceOptions'][1]['Number'] == 1
    assert next_questions[0]['ChoiceOptions'][1]['Content'] == 'Choice #2'
    assert next_questions[0]['ChoiceOptions'][1]['Correct'] == 'N'
    assert next_questions[0]['ChoiceOptions'][2]['Number'] == 2
    assert next_questions[0]['ChoiceOptions'][2]['Content'] == 'Choice #3'
    assert next_questions[0]['ChoiceOptions'][2]['Correct'] ==  'Y'
    client.delete('/exams/'+content['exam_id'])



def test_edit_question_not_existent():
    url = '/exams/edit_question/NO_EXISTO'
    patch_response = client.patch(url,
        data =      
            '{'+
                '"question_type": "MC", '+
                '"question_content": "Mult Choice", '+
                '"choice_responses": ['+
                    '{"number": 0, "content": "Choice #1", "correct": "Y"},'+
                    '{"number": 1, "content": "Choice #2", "correct": "N"},'+
                    '{"number": 2, "content": "Choice #3", "correct": "Y"}'+
                ']'
            '}'
    )
    assert patch_response.status_code == 404


def test_hand_in_question_student():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    question_id = client.get('/exams/'+content['exam_id']+'/questions').json()
    question_id = question_id[0]['QuestionID']
    response_hand_in = client.post(
        '/exams/'+content['exam_id']+'/answer/'+question_id+'?user_id=USUARIO&response_content=desarrollo_totalmente_completo'
    )
    assert response_hand_in.status_code == 200
    response_hand_in = response_hand_in.json()
    assert response_hand_in['exam_id'] == content['exam_id']
    assert response_hand_in['question_id'] == question_id
    assert response_hand_in['response_content'] == 'desarrollo_totalmente_completo'
    assert response_hand_in['choice_number'] == None
    client.delete('/exams/responses/USUARIO/'+question_id)
    client.delete('/exams/'+content['exam_id'])


def test_get_user_response_for_question():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    question_id = client.get('/exams/'+content['exam_id']+'/questions').json()
    question_id = question_id[0]['QuestionID']
    response_hand_in = client.post(
        '/exams/'+content['exam_id']+'/answer/'+question_id+'?user_id=USUARIO&response_content=desarrollo_totalmente_completo'
    )
    assert response_hand_in.status_code == 200
    content_get = client.get('/exams/student/USUARIO/student_response/'+question_id)
    assert content_get.status_code == 200
    assert content_get.json()['exam_id'] == content['exam_id']
    assert content_get.json()['user_id'] == 'USUARIO'
    assert content_get.json()['question_id'] == question_id
    assert content_get.json()['response_content'] == 'desarrollo_totalmente_completo'
    assert content_get.json()['choice_number'] == None
    client.delete('/exams/responses/USUARIO/'+question_id)
    client.delete('/exams/'+content['exam_id'])


def test_get_user_response_for_question_not_existent():
    content_get = client.get('/exams/student/USUARIOINEXISTENTE/student_response/UNEXISTENT_QUESTION')
    assert content_get.status_code == 404


def test_exam_qualifying():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    response_qualification = client.post('/exams/'+content['exam_id']+'/qualify/CALIFICADO?mark=10&comments=muy buena resolucion')
    assert response_qualification.status_code == 201
    client.delete('/exams/marks/CALIFICADO/'+content['exam_id'])
    client.delete('/exams/'+content['exam_id'])


def test_exam_qualifying_not_existent():
    response_qualification = client.post('/exams/EXAMEN_INEXISTENTE/qualify/CALIFICADO?mark=10&comments=muy buena resolucion')
    assert response_qualification.status_code == 404


def test_exam_already_qualified():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    response_qualification = client.post('/exams/'+content['exam_id']+'/qualify/REPETIDO?mark=10&comments=muy buena resolucion')
    assert response_qualification.status_code == 201
    response_qualification = client.post('/exams/'+content['exam_id']+'/qualify/REPETIDO?mark=10&comments=muy buena resolucion')
    assert response_qualification.status_code == 400
    client.delete('/exams/marks/REPETIDO/'+content['exam_id'])
    client.delete('/exams/'+content['exam_id'])


def test_exam_qualification_with_mark_not_valid():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    response_qualification = client.post('/exams/'+content['exam_id']+'/qualify/MARKMENORCERO?mark=-1&comments=muy buena resolucion')
    assert response_qualification.status_code == 422
    response_qualification = client.post('/exams/'+content['exam_id']+'/qualify/MARKMAYORDIEZO?mark=11.33&comments=muy buena resolucion')
    assert response_qualification.status_code == 422
    client.delete('/exams/'+content['exam_id'])