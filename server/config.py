"""Runtime settings. Never ship actual credentials in source control."""
from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')

DATA_DIR = Path(os.environ.get('INTERVIEW_DATA_DIR', str(ROOT / 'data')))
DB_PATH = DATA_DIR / 'assistant.sqlite3'
TEXT_MODEL = os.environ.get('OPENAI_TEXT_MODEL', 'gpt-4.1-mini')
TRANSCRIPTION_MODEL = os.environ.get('OPENAI_TRANSCRIPTION_MODEL', 'gpt-4o-mini-transcribe')
MAX_DOCUMENT_BYTES = 8 * 1024 * 1024
MAX_AUDIO_BYTES = 20 * 1024 * 1024
MAX_DOCUMENT_CHARS = 24000
