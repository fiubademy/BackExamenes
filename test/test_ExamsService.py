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
    assert content['exam_date'] == "2022-12-02T21:33:33"
    client.delete('/exams/'+exam_id)


def test_create_exam_without_questions_initially():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen'
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    exam_id = content['exam_id']
    assert content['course_id'] == 'id_curso'
    assert content['exam_date'] == "2022-12-02T21:33:33"
    client.delete('/exams/'+exam_id)


def test_publish_exam():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]'
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    exam_id = content['exam_id']
    assert content['course_id'] == 'id_curso'
    assert content['exam_date'] == "2022-12-02T21:33:33"
    response = client.patch(
        '/exams/' + exam_id + '/publish'
    )
    assert response.status_code == 200
    response = client.get('/exams/'+exam_id)
    assert response.json()['Status'] == 'PUBLISHED'
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
    assert content_get['Status'] == 'EDITION'
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
    assert content_get[0]['Status'] == 'EDITION'
    client.delete('/exams/'+content_get[0]['ExamID'])


def test_get_exam_by_course_filtering():
    response = client.post(
        '/exams/create_exam/id_curso_test?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    response_two = client.post(
        '/exams/create_exam/id_curso_test?examDate=2022-12-02T21:33:34&examTitle=TituloExamen2',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    publish_exam_id = response_two.json()['exam_id']
    response_publish = client.patch('/exams/' + publish_exam_id + '/publish')
    assert response.status_code == 200
    assert response_two.status_code == 200
    assert response_publish.status_code == 200
    content_post = response.json()
    content_post_two = response_two.json()
    content_get_published = client.get('/exams/course/id_curso_test')
    content_get_edition = client.get('/exams/course/id_curso_test?exam_status=EDITION')
    content_get_published = client.get('/exams/course/id_curso_test?exam_status=published')
    assert content_get_edition.status_code == 200
    assert content_get_published.status_code == 200
    content_get_edition = content_get_edition.json()
    content_get_published = content_get_published.json()

    assert content_get_edition[0]['CourseID'] == content_post['course_id']
    assert content_get_edition[0]['ExamID'] == content_post['exam_id']
    assert content_get_edition[0]['Date'] == content_post['exam_date']
    assert content_get_edition[0]['Status'] == 'EDITION'
    assert len(content_get_edition) == 1

    assert content_get_published[0]['CourseID'] == content_post_two['course_id']
    assert content_get_published[0]['ExamID'] == content_post_two['exam_id']
    assert content_get_published[0]['Date'] == content_post_two['exam_date']
    assert content_get_published[0]['Status'] == 'PUBLISHED'
    assert len(content_get_published) == 1

    client.delete('/exams/'+content_get_edition[0]['ExamID'])
    client.delete('/exams/'+content_get_published[0]['ExamID'])


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
                        '{"number": 0, "content": "ASD"},'+
                        '{"number": 1, "content": "Wepa"}'+
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
    assert questions_got[1]['ChoiceOptions'][1]['Number'] == 1
    assert questions_got[1]['ChoiceOptions'][1]['Content'] == 'Wepa'
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
                        '{"number": 0, "content": "ASD"},'+
                        '{"number": 1, "content": "Wepa"}'+
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
    assert content_edit['Date'] == '2012-12-22T21:45:33'
    assert content_edit['ExamTitle'] == 'tituloEditado'
    client.delete('/exams/'+content['exam_id'])


def test_edit_exam_not_existent():
    url = '/exams/edit_exam/NO_EXISTO?exam_date=2012-12-22T21:45:33'
    response_edit = client.patch(url)
    assert response_edit.status_code == status.HTTP_404_NOT_FOUND


def test_edit_question_from_des_to_choice():
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
                    '{"number": 0, "content": "Choice #1"},'+
                    '{"number": 1, "content": "Choice #2"},'+
                    '{"number": 2, "content": "Choice #3"}'+
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
    assert next_questions[0]['ChoiceOptions'][0]['Content'] == 'Choice #1'
    assert next_questions[0]['ChoiceOptions'][1]['Number'] == 1
    assert next_questions[0]['ChoiceOptions'][1]['Content'] == 'Choice #2'
    assert next_questions[0]['ChoiceOptions'][2]['Number'] == 2
    assert next_questions[0]['ChoiceOptions'][2]['Content'] == 'Choice #3'
    client.delete('/exams/'+content['exam_id'])


def test_edit_question_from_des_to_des():
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
                '"question_type": "DES", '+
                '"question_content": "Desarrollo Edit"'+
            '}'
    )
    assert patch_response.status_code == status.HTTP_202_ACCEPTED
    next_questions = client.get('/exams/'+content['exam_id']+'/questions').json()

    assert len(initial_questions) == 1
    assert initial_questions[0]['QuestionContent'] == 'Pregunta 1'
    assert initial_questions[0]['QuestionType'] == 'DES'
    assert initial_questions[0]['ExamID'] == content['exam_id']

    assert len(next_questions) == 1
    assert next_questions[0]['QuestionContent'] == 'Desarrollo Edit'
    assert next_questions[0]['QuestionType'] == 'DES'
    assert next_questions[0]['ExamID'] == content['exam_id']
    client.delete('/exams/'+content['exam_id'])



def test_edit_question_not_existent():
    url = '/exams/edit_question/NO_EXISTO'
    patch_response = client.patch(url,
        data =      
            '{'+
                '"question_type": "MC", '+
                '"question_content": "Mult Choice", '+
                '"choice_responses": ['+
                    '{"number": 0, "content": "Choice #1"},'+
                    '{"number": 1, "content": "Choice #2"},'+
                    '{"number": 2, "content": "Choice #3"}'+
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
    client.delete('/exams/responses/USUARIO/'+question_id)
    client.delete('/exams/'+content['exam_id'])

def test_redo_exam_student():
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
    response_mark = client.post(
        '/exams/'+response_hand_in['exam_id']+'/qualify/USUARIO?mark=2&comments=Desaprobado. Todo mal.');
    assert response_mark.status_code == 201
    response_hand_in = client.post(
        '/exams/'+content['exam_id']+'/answer/'+question_id+'?user_id=USUARIO&response_content=Un desarrollo distinto'
    )
    assert response_hand_in.status_code == 200
    response_hand_in = response_hand_in.json()
    assert response_hand_in['exam_id'] == content['exam_id']
    assert response_hand_in['question_id'] == question_id
    assert response_hand_in['response_content'] == 'Un desarrollo distinto'
    response_mark = client.post(
        '/exams/'+response_hand_in['exam_id']+'/qualify/USUARIO?mark=10&comments=Muy buen desarrollo.');
    assert response_mark.status_code == 201
    client.delete('/exams/responses/USUARIO/'+question_id)
    client.delete('/exams/marks/USUARIO/'+response_hand_in['exam_id'])
    client.delete('/exams/'+content['exam_id'])


def test_redo_exam_student_without_being_graded_previously_should_fail():
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
    response_hand_in = client.post(
        '/exams/'+content['exam_id']+'/answer/'+question_id+'?user_id=USUARIO&response_content=Un desarrollo distinto'
    )
    assert response_hand_in.status_code == 403
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


def test_user_is_able_to_do_exam():
    response = client.get('/exams/idexamen/is_able_to_do_exam/USUARIO')
    assert response.status_code == 200
    assert response.json() == True

def test_user_is_able_to_redo_exam():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == status.HTTP_200_OK
    content = response.json()

    response = client.get('/exams/'+content['exam_id']+'/is_able_to_do_exam/USUARIO')
    assert response.status_code == 200
    assert response.json() == True

    question_id = client.get('/exams/'+content['exam_id']+'/questions').json()
    question_id = question_id[0]['QuestionID']
    response_hand_in = client.post(
        '/exams/'+content['exam_id']+'/answer/'+question_id+'?user_id=USUARIO&response_content=desarrollo_totalmente_completo'
    ).json()
    response_mark = client.post(
        '/exams/'+response_hand_in['exam_id']+'/qualify/USUARIO?mark=2&comments=Desaprobado. Todo mal.');
    assert response_mark.status_code == 201

    response = client.get('/exams/'+content['exam_id']+'/is_able_to_do_exam/USUARIO')
    assert response.status_code == 200
    assert response.json() == True

    client.delete('/exams/responses/USUARIO/'+question_id)
    client.delete('/exams/marks/USUARIO/'+response_hand_in['exam_id'])
    client.delete('/exams/'+content['exam_id'])


def test_user_is_not_able_to_redo_exam():

    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == status.HTTP_200_OK
    content = response.json()

    response = client.get('/exams/'+content['exam_id']+'/is_able_to_do_exam/USUARIO')
    assert response.status_code == 200
    assert response.json() == True

    question_id = client.get('/exams/'+content['exam_id']+'/questions').json()
    question_id = question_id[0]['QuestionID']
    response_hand_in = client.post(
        '/exams/'+content['exam_id']+'/answer/'+question_id+'?user_id=USUARIO&response_content=desarrollo_totalmente_completo'
    )

    response = client.get('/exams/'+content['exam_id']+'/is_able_to_do_exam/USUARIO')
    assert response.status_code == 406
    assert response.json() == False

    client.delete('/exams/responses/USUARIO/'+question_id)
    client.delete('/exams/'+content['exam_id'])


def test_get_students_who_answered_an_exam():
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
    get_students = client.get('/exams/' + content['exam_id'] + '/students_who_answered')
    assert get_students.status_code == 200
    get_students = get_students.json()
    assert len(get_students) == 1
    assert get_students[0] == 'USUARIO'
    client.delete('/exams/'+content['exam_id'])


def test_get_students_already_marked():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    response_qualification = client.post('/exams/'+content['exam_id']+'/qualify/CALIFICADO?mark=10&comments=muy buena resolucion')
    assert response_qualification.status_code == 201
    get_marked_students = client.get('/exams/' + content['exam_id'] + '/students_with_qualification')
    assert get_marked_students.status_code == 200
    get_marked_students = get_marked_students.json()
    assert len(get_marked_students) == 1
    assert get_marked_students[0]['mark'] == 10
    assert get_marked_students[0]['student_id'] == 'CALIFICADO'
    assert get_marked_students[0]['comments'] == "muy buena resolucion"
    client.delete('/exams/'+content['exam_id'])


def test_get_students_who_answered_an_exam_without_mark():
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
    response_hand_in_two = client.post(
        '/exams/'+content['exam_id']+'/answer/'+question_id+'?user_id=USUARIO2&response_content=desarrollo_totalmente_completo'
    )
    response_qualification = client.post('/exams/'+content['exam_id']+'/qualify/USUARIO2?mark=10&comments=muy buena resolucion')
    assert response_qualification.status_code == 201
    get_students = client.get('/exams/' + content['exam_id'] + '/students_without_qualification')
    assert get_students.status_code == 200
    get_students = get_students.json()
    assert len(get_students) == 1
    assert get_students[0]['student_id'] == 'USUARIO'
    client.delete('/exams/'+content['exam_id'])


def test_get_students_already_marked_filtering_by_id():
    response = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    response_qualification = client.post('/exams/'+content['exam_id']+'/qualify/CALIFICADO?mark=10&comments=muy buena resolucion')
    assert response_qualification.status_code == 201
    get_marked_students = client.get('/exams/' + content['exam_id'] + '/students_with_qualification?student_id=CALIFICADO')
    assert get_marked_students.status_code == 200
    get_marked_students = get_marked_students.json()
    assert len(get_marked_students) == 1
    assert get_marked_students[0]['mark'] == 10
    assert get_marked_students[0]['student_id'] == 'CALIFICADO'
    assert get_marked_students[0]['comments'] == "muy buena resolucion"
    get_marked_students_not_found = client.get('/exams/' + content['exam_id'] + '/students_with_qualification?student_id=NO_EXISTO')
    assert get_marked_students_not_found.status_code == 404
    client.delete('/exams/'+content['exam_id'])


def test_ask_state_in_course_without_exams():
    response = client.get('/exams/id_curso/student_state/USUARIO')
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_state_user_not_finished_exams():
    response_create = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    response_create_two = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    client.patch('/exams/'+response_create.json()['exam_id']+'/publish')
    client.patch('/exams/'+response_create_two.json()['exam_id']+'/publish')
    response_qualification_one = client.post('/exams/'+response_create.json()['exam_id']+'/qualify/USUARIO?mark=10&comments=muy buena resolucion')
    response_state = client.get('/exams/id_curso/student_state/USUARIO')
    assert response_state.status_code == status.HTTP_200_OK
    assert response_state.json()['status'] == 'Unfinished'
    assert response_state.json()['average_mark'] == 10
    assert response_state.json()['exams_not_passed'] == 1
    client.delete('/exams/'+response_create.json()['exam_id'])
    client.delete('/exams/'+response_create_two.json()['exam_id'])


def test_state_user_failed_exams():
    response_create = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    response_create_two = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    client.patch('/exams/'+response_create.json()['exam_id']+'/publish')
    client.patch('/exams/'+response_create_two.json()['exam_id']+'/publish')
    response_qualification_one = client.post('/exams/'+response_create.json()['exam_id']+'/qualify/USUARIO?mark=2&comments=re mala res')
    response_qualification_two = client.post('/exams/'+response_create_two.json()['exam_id']+'/qualify/USUARIO?mark=4&comments=re mala res')
    response_state = client.get('/exams/id_curso/student_state/USUARIO')
    assert response_state.status_code == status.HTTP_200_OK
    assert response_state.json()['status'] == 'Unfinished'
    assert response_state.json()['average_mark'] == 3
    assert response_state.json()['exams_not_passed'] == 2
    client.delete('/exams/'+response_create.json()['exam_id'])
    client.delete('/exams/'+response_create_two.json()['exam_id'])


def test_state_user_passed():
    response_create = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    client.patch('/exams/'+response_create.json()['exam_id']+'/publish')
    response_create_two = client.post(
        '/exams/create_exam/id_curso?examDate=2022-12-02T21:33:33&examTitle=TituloExamen',
        data = '[{"question_type": "DES", "question_content": "Pregunta 1"}]')
    client.patch('/exams/'+response_create_two.json()['exam_id']+'/publish')
    response_qualification_one = client.post('/exams/'+response_create.json()['exam_id']+'/qualify/USUARIO?mark=6&comments=zafarelli')
    response_qualification_two = client.post('/exams/'+response_create_two.json()['exam_id']+'/qualify/USUARIO?mark=8&comments=no tan mal')
    response_state = client.get('/exams/id_curso/student_state/USUARIO')
    assert response_state.status_code == status.HTTP_200_OK
    assert response_state.json()['status'] == 'Finished'
    assert response_state.json()['average_mark'] == 7
    assert response_state.json()['exams_not_passed'] == 0
    client.delete('/exams/'+response_create.json()['exam_id'])
    client.delete('/exams/'+response_create_two.json()['exam_id'])
