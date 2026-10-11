"""Single-user web app. Localhost only; intentionally no public server deployment config."""
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware
from . import db
from .ai import generate_answer, transcribe_audio
from .config import ROOT, MAX_DOCUMENT_BYTES, MAX_AUDIO_BYTES, TEXT_MODEL, TRANSCRIPTION_MODEL
from .documents import extract_document

WEB = ROOT / 'web'


@asynccontextmanager
async def lifespan(_app):
    db.initialize()
    yield


app = FastAPI(title='Interview Assist', version='1.0.0', lifespan=lifespan,
              docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost', '127.0.0.1', 'testserver'])
app.mount('/assets', StaticFiles(directory=WEB / 'assets'), name='assets')


class ProfileData(BaseModel):
    name: str = Field(default='', max_length=160)
    target_role: str = Field(default='', max_length=240)
    experience: str = Field(default='', max_length=6000)
    job_description: str = Field(default='', max_length=14000)


class QuestionData(BaseModel):
    question: str = Field(min_length=3, max_length=3500)
    style: str = Field(default='balanced', pattern='^(brief|balanced|detailed)$')
    tone: str = Field(default='professional', pattern='^(professional|confident|technical)$')


@app.get('/')
async def home():
    return FileResponse(WEB / 'index.html')


@app.get('/styles.css')
async def styles():
    return FileResponse(WEB / 'styles.css', media_type='text/css')


@app.get('/app.js')
async def script():
    return FileResponse(WEB / 'app.js', media_type='text/javascript')


@app.get('/api/health')
async def health():
    key = os.getenv('OPENAI_API_KEY', '').strip()
    return {'ok': True, 'configured': bool(key and key != 'replace_with_your_api_key'),
            'text_model': TEXT_MODEL, 'transcription_model': TRANSCRIPTION_MODEL,
            'local_only': True}


@app.get('/api/profile')
async def get_profile():
    return db.get_profile()


@app.put('/api/profile')
async def update_profile(payload: ProfileData):
    return db.save_profile(payload.model_dump())


@app.post('/api/resume')
async def resume(file: UploadFile = File(...)):
    filename = Path(file.filename or '').name
    if not filename:
        raise HTTPException(400, 'No document selected.')
    content = await file.read(MAX_DOCUMENT_BYTES + 1)
    await file.close()
    if len(content) > MAX_DOCUMENT_BYTES:
        raise HTTPException(413, 'Resume exceeds 8 MB. Please upload a smaller document.')
    text = extract_document(filename, content)
    result = db.set_resume(filename, text)
    return {'filename': result['resume_filename'], 'characters': len(result['resume_text'])}


@app.delete('/api/resume')
async def remove_resume():
    db.set_resume('', '')
    return {'deleted': True}


@app.post('/api/transcribe')
async def transcribe(file: UploadFile = File(...)):
    filename = file.filename or 'question.webm'
    extension = Path(filename).suffix.lower()
    types = {'.webm':'audio/webm','.ogg':'audio/ogg','.mp4':'audio/mp4',
             '.m4a':'audio/mp4','.wav':'audio/wav','.mp3':'audio/mpeg'}
    if extension not in types:
        raise HTTPException(415, 'Unsupported audio. Use WebM, OGG, MP4, M4A, WAV or MP3.')
    payload = await file.read(MAX_AUDIO_BYTES + 1)
    await file.close()
    if not payload or len(payload) > MAX_AUDIO_BYTES:
        raise HTTPException(413, 'Audio must be non-empty and no more than 20 MB.')
    text = await transcribe_audio(payload, filename, types[extension])
    return {'text': text}


@app.post('/api/answer')
async def answer(payload: QuestionData):
    question = payload.question.strip()
    if len(question) < 3:
        raise HTTPException(422, 'Please enter a valid interview question.')
    text = await generate_answer(question, db.get_profile(), db.recent_answers(), payload.style, payload.tone)
    item = db.add_answer(question, text, payload.style)
    return item


@app.get('/api/history')
async def history():
    return {'items': db.list_history()}


@app.delete('/api/history')
async def delete_history():
    db.clear_history()
    return {'deleted': True}
