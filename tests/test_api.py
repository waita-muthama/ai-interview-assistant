from io import BytesIO
from docx import Document


def test_health_and_static_dashboard(client):
    assert client.get('/api/health').status_code == 200
    assert client.get('/').status_code == 200
    assert 'Candidate profile' in client.get('/').text
    assert 'Capture a question' in client.get('/').text
    assert client.get('/app.js').status_code == 200
    assert client.get('/styles.css').status_code == 200


def test_profile_save_and_fetch(client):
    data = {'name': 'Alex', 'target_role': 'Network Engineer',
            'experience': 'Configured managed switches', 'job_description': 'Manage LAN infrastructure'}
    res = client.put('/api/profile', json=data)
    assert res.status_code == 200
    assert res.json()['target_role'] == 'Network Engineer'
    assert client.get('/api/profile').json()['experience'] == 'Configured managed switches'


def test_upload_txt_and_remove(client):
    reply = client.post('/api/resume', files={'file': ('my_resume.txt', b'Networking with Cisco switches.', 'text/plain')})
    assert reply.status_code == 200
    assert client.get('/api/profile').json()['resume_filename'] == 'my_resume.txt'
    assert client.delete('/api/resume').status_code == 200
    assert client.get('/api/profile').json()['resume_text'] == ''


def test_upload_docx(client):
    doc = Document()
    doc.add_paragraph('Relevant experience: Linux, cloud networking, firewall rules.')
    file = BytesIO()
    doc.save(file)
    reply = client.post('/api/resume', files={'file': ('resume.docx', file.getvalue(),
                                                       'application/vnd.openxmlformats-officedocument.wordprocessingml.document')})
    assert reply.status_code == 200
    assert 'Linux' in client.get('/api/profile').json()['resume_text']


def test_reject_bad_files(client):
    assert client.post('/api/resume', files={'file': ('code.exe', b'fake', 'application/octet-stream')}).status_code == 415
    assert client.post('/api/resume', files={'file': ('too_large.txt', b'x' * (8 * 1024 * 1024 + 1), 'text/plain')}).status_code == 413
    assert client.post('/api/resume', files={'file': ('blank.txt', b'    ', 'text/plain')}).status_code == 422
    assert client.post('/api/transcribe', files={'file': ('bad.bin', b'abc', 'application/octet-stream')}).status_code == 415


def test_answer_history_with_mocked_ai(client, monkeypatch):
    from server import main
    async def fake_answer(question, profile, history, style, tone):
        assert style == 'balanced'
        assert tone == 'professional'
        return 'I would verify the switch interfaces, VLANs, default gateway, and routing.'
    monkeypatch.setattr(main, 'generate_answer', fake_answer)
    result = client.post('/api/answer', json={'question': 'How do you diagnose a LAN problem?'})
    assert result.status_code == 200
    assert result.json()['id'] == 1
    assert 'VLANs' in result.json()['answer']
    assert len(client.get('/api/history').json()['items']) == 1
    assert client.delete('/api/history').status_code == 200
    assert client.get('/api/history').json()['items'] == []


def test_transcribe_with_mock(client, monkeypatch):
    from server import main
    async def fake_transcription(data, filename, mime):
        assert filename == 'question.webm'
        assert mime == 'audio/webm'
        return 'What are your strengths?'
    monkeypatch.setattr(main, 'transcribe_audio', fake_transcription)
    result = client.post('/api/transcribe', files={'file': ('question.webm', b'fake-webm-bytes', 'audio/webm')})
    assert result.status_code == 200
    assert result.json()['text'] == 'What are your strengths?'


def test_invalid_question(client):
    assert client.post('/api/answer', json={'question': 'x'}).status_code == 422
    assert client.post('/api/answer', json={'question': 'Why?', 'style': 'wrong'}).status_code == 422


def test_localhost_only(client):
    # TrustedHostMiddleware checks the Host header.
    result = client.get('/api/health', headers={'host': 'public.example.com'})
    assert result.status_code == 400
