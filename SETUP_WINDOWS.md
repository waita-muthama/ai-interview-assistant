# Windows 10/11 — Installation and first interview

## 1. Extract the project

Right-click `ai-interview-assistant.zip` → **Extract All**. A path without special restrictions works well, e.g. `C:\InterviewAssist\ai-interview-assistant`.

## 2. Install Python

Download a supported Python 3 release from <https://www.python.org/downloads/windows/> and tick **Add Python to PATH**. Open a command prompt and run `py -3 --version`. It should display Python 3.10 or newer. (Python 3.12/3.13 also work.)

## 3. Start the local app

Double-click `launch_windows.bat`. Windows may show a publisher caution for unsigned `.bat` files downloaded from the internet. Inspect the source in Notepad; the script creates a Python environment and runs a local server. It must be run from its extracted folder and needs internet access for the first package installation.

Expected startup line: `Uvicorn running on http://127.0.0.1:8765`.

## 4. Configure the OpenAI API key

**The launcher now asks for your NEW API key automatically on first start.** When you see `Paste NEW API key (input hidden; Enter to skip):`, paste the key directly into that terminal window and press Enter. Nothing will appear while you type/paste; this is normal. The key is written only to the private local `.env` configuration file. It is **never included in the ZIP** or browser JavaScript.

**If an earlier API key was shared in a chat, screenshot or file, revoke that key and generate a different one** at <https://platform.openai.com/api-keys>. To update an already configured key, double-click `configure_api_key_windows.bat` and restart `launch_windows.bat` afterward.

You may instead open `.env` in Notepad and enter `OPENAI_API_KEY=...` manually. Do not share the `.env` file. The green **API configured** indicator confirms the backend can read a key, but does not verify its validity until a request is made. API billing is separate from ChatGPT subscriptions.

## 5. Open the professional dashboard

Open Chrome or Edge and visit <http://127.0.0.1:8765>. If your browser asks to allow microphone access, choose Allow when you start listening. No public website, account signup, or webcam is needed.

## 6. Add accurate CV / position details

Open **Candidate profile**. Enter your target job, evidence-backed skills, responsibilities and the vacancy description. Save the profile. Optionally upload a text-based PDF, Word DOCX, TXT or MD resume (max 8 MB). Uploading a new resume replaces its previously extracted text.

## 7. Answer a practice question

From **Live assistant** type `What are the steps you would take to troubleshoot a network outage?` and click **Generate suggested answer**. You should see a response appear in the right panel. If you see an authentication or quota error, check the .env key, API model availability, and billing at the OpenAI Platform account.

## 8. Use voice capture

Connect your microphone, click **Start listening**, allow browser access and speak a mock interview question. Pause for around two seconds or click **Stop & process**. The browser uploads the temporary audio segment to the local backend, which sends it to the OpenAI transcription API. The transcript fills the text box and automatically requests an answer. **Review** before speaking; you are the interviewee.

## 9. Live meeting considerations

Direct remote participant audio capture is not included. Most browsers cannot automatically record the audio that Zoom, Teams or Meet plays to your headphones. Use the appropriate audio input routing only with consent; see README for options such as Windows Stereo Mix and virtual inputs. You can always type the heard question if no routing is available.

## 10. Review and stop

Open **Interview history** to view and export your questions and drafted responses; **Clear history** removes them from SQLite. Close the terminal window or press Ctrl+C to stop. No microphone recording continues when the page is not actively recording.

## Troubleshooting

| Problem | What to do |
|---|---|
| `python is not recognized` | Install Python and add it to PATH, or reopen Command Prompt after installation. |
| Package install fails | Check your internet connection / antivirus; rerun the batch file. |
| `Address already in use` | Close another Interview Assist server, or run a free port and access the matching URL. |
| Page does not open | Keep the terminal open and use `http://127.0.0.1:8765`, not an external domain. |
| API key is missing | Edit `.env` next to `README.md`, save, restart script. |
| OpenAI authentication/quota error | Verify API billing, available credits and model permissions in your OpenAI Platform account. |
| No audio capture / access denied | In Chrome or Edge site settings allow microphone for localhost. Check Windows privacy Microphone settings. |
| Transcription misses a question | Pick correct input, reduce background noise, increase input volume, use Stop & process manually. |
| Auto-stop triggers too early | Uncheck **Automatically stop after a pause** and stop manually. |
| Can't hear remote meeting | Use authorized system-audio routing or manually type the question; the app does not tap meeting audio itself. |
| Scanned PDF uploads but no text | Convert it to a searchable PDF or upload a DOCX/TXT copy; OCR is not bundled. |

