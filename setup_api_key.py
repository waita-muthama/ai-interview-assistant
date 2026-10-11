"""Safely configure a local OpenAI API key without placing it in source code.

Only invoked from a local interactive terminal.  Never print or log the secret.
"""
from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / '.env'
TEMPLATE = ROOT / '.env.example'
PLACEHOLDER = 'replace_with_your_api_key'


def current_key_is_present() -> bool:
    # An OS-level variable takes precedence over .env via python-dotenv.
    environment_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if environment_key and environment_key != PLACEHOLDER:
        return True
    if not CONFIG.exists():
        return False
    for line in CONFIG.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line.startswith('OPENAI_API_KEY='):
            value = line.split('=', 1)[1].strip().strip('"\'')
            return bool(value and value != PLACEHOLDER)
    return False


def write_local_key(key: str) -> None:
    if not key.startswith('sk-') or len(key) < 12 or '\n' in key or '\r' in key:
        raise ValueError('The API key format is invalid. The key was not saved.')
    if CONFIG.exists():
        lines = CONFIG.read_text(encoding='utf-8').splitlines()
    else:
        lines = TEMPLATE.read_text(encoding='utf-8').splitlines() if TEMPLATE.exists() else []
    updated = []
    replaced = False
    for line in lines:
        if line.strip().startswith('OPENAI_API_KEY='):
            if not replaced:
                updated.append('OPENAI_API_KEY=' + key)
                replaced = True
        else:
            updated.append(line)
    if not replaced:
        updated.insert(0, 'OPENAI_API_KEY=' + key)

    # Atomic write, mode 0600 on POSIX. File stays local and .gitignored.
    fd, temporary = tempfile.mkstemp(prefix='.env-', dir=ROOT, text=True)
    try:
        if os.name != 'nt':
            os.chmod(temporary, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write('\n'.join(updated) + '\n')
        os.replace(temporary, CONFIG)
        if os.name != 'nt':
            os.chmod(CONFIG, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser(description='Store a NEW OpenAI API key in a private local .env file.')
    parser.add_argument('--replace', action='store_true', help='Replace the existing locally stored API key.')
    args = parser.parse_args()
    if current_key_is_present() and not args.replace:
        print('[OK] An API key is already configured locally.')
        return 0
    if not sys.stdin.isatty():
        print('[INFO] No interactive terminal detected. Manually set OPENAI_API_KEY in .env.')
        return 0
    print('\nOpenAI API key setup: https://platform.openai.com/api-keys')
    print('Use a newly generated key. Never share it in chat or add it to a ZIP/repository.')
    try:
        key = getpass.getpass('Paste NEW API key (input hidden; Enter to skip): ').strip()
    except (KeyboardInterrupt, EOFError):
        print('\n[INFO] API key setup canceled.')
        return 0
    if not key:
        print('[INFO] No key entered. You can configure it later in .env.')
        return 0
    try:
        write_local_key(key)
    except ValueError as error:
        print('[ERROR]', error)
        return 1
    print('[OK] API key saved in local .env. It was not added to application source files.')
    print('[INFO] Restart the application if it was already running.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
