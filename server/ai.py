"""OpenAI REST API gateway. All secret-bearing calls occur server-side."""
import os
import httpx
from fastapi import HTTPException
from .config import TEXT_MODEL, TRANSCRIPTION_MODEL
from .prompts import build_prompt, INSTRUCTIONS

OPENAI_URL = 'https://api.openai.com/v1'


def authentication_headers():
    key = os.getenv('OPENAI_API_KEY', '').strip()
    if not key or key == 'replace_with_your_api_key':
        raise HTTPException(503, 'Add a valid OPENAI_API_KEY to the .env file, then restart the app.')
    return {'Authorization': f'Bearer {key}'}


def handle_response(response: httpx.Response):
    if response.status_code == 401:
        raise HTTPException(502, 'OpenAI rejected your API key. Check .env and API account access.')
    if response.status_code == 429:
        raise HTTPException(429, 'OpenAI rate limit or quota reached. Review API billing or retry later.')
    if response.status_code >= 400:
        raise HTTPException(502, f'OpenAI API returned HTTP {response.status_code}. Check model access and request configuration.')
    try:
        return response.json()
    except ValueError as exc:
        raise HTTPException(502, 'OpenAI API returned an unexpected response.') from exc


async def post_openai(endpoint: str, *, json=None, data=None, files=None):
    headers = authentication_headers()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=12.0), follow_redirects=False) as http:
            result = await http.post(OPENAI_URL + endpoint, headers=headers, json=json, data=data, files=files)
    except httpx.TimeoutException as exc:
        raise HTTPException(504, 'OpenAI request timed out. Check connectivity and retry.') from exc
    except httpx.RequestError as exc:
        raise HTTPException(502, 'Cannot connect to OpenAI. Check your internet connection.') from exc
    return handle_response(result)


def extract_output_text(result: dict) -> str:
    # Responses REST API contains assistant output in output[].content[].text.
    texts = []
    for item in result.get('output', []):
        for piece in item.get('content', []):
            if piece.get('type') == 'output_text' and isinstance(piece.get('text'), str):
                texts.append(piece['text'])
    return '\n'.join(texts).strip() or (result.get('output_text') or '').strip()


async def generate_answer(question, profile, history, style, tone):
    response = await post_openai('/responses', json={
        'model': TEXT_MODEL,
        'instructions': INSTRUCTIONS,
        'input': build_prompt(question, profile, history, style, tone),
        'max_output_tokens': 650,
        'store': False,
    })
    answer = extract_output_text(response)
    if not answer:
        raise HTTPException(502, 'AI returned no answer. Try generating again.')
    return answer


async def transcribe_audio(payload: bytes, filename: str, content_type: str):
    result = await post_openai('/audio/transcriptions', data={'model': TRANSCRIPTION_MODEL},
                               files={'file': (filename, payload, content_type)})
    text = result.get('text', '')
    return text.strip() if isinstance(text, str) else ''
