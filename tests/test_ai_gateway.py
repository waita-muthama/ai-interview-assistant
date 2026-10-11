import pytest
from fastapi import HTTPException
from server.ai import extract_output_text, handle_response, authentication_headers
import httpx


def test_parse_responses_rest_shape():
    payload = {'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': 'I would begin by confirming the impact.'}]}]}
    assert extract_output_text(payload) == 'I would begin by confirming the impact.'
    assert extract_output_text({'output': []}) == ''


def test_api_key_validation(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    with pytest.raises(HTTPException) as err:
        authentication_headers()
    assert err.value.status_code == 503
    monkeypatch.setenv('OPENAI_API_KEY', 'sample_test_key')
    assert authentication_headers()['Authorization'] == 'Bearer sample_test_key'


def test_api_errors_are_private():
    request = httpx.Request('POST', 'https://api.openai.com/v1/responses')
    response = httpx.Response(401, request=request, json={'error': {'message': 'private details'}})
    with pytest.raises(HTTPException) as err:
        handle_response(response)
    assert err.value.status_code == 502
    assert 'private details' not in err.value.detail
