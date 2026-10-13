# InterviewIQ — AI Mock Interview Platform

Flask website for Python Developer, Data Analyst, and Machine Learning Engineer interview practice.

## Features
- Responsive professional interface
- Fresh Gemini-generated role-specific questions for each session, one at a time
- Difficulty-aware question generation with recent-question repetition avoidance
- Choose 5 or 10 questions
- Beginner, Intermediate, and Advanced levels
- Gemini feedback: score, strengths, improvements, sample answer, review topics
- End-of-session report
- `/health` endpoint

## Windows PowerShell setup
From this folder run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and add your Gemini API key. Keep `.env` private and do not upload it to GitHub. Confirm `GEMINI_MODEL` is available for your API account.

```powershell
.\.venv\Scripts\python.exe app.py
```

Open http://127.0.0.1:5000. In another PowerShell window, test with `Invoke-RestMethod http://127.0.0.1:5000/health`.

Never put the API key in HTML or JavaScript. Change `FLASK_SECRET_KEY` before deployment and disable Flask debug mode in production. AI feedback is practice guidance, not a hiring decision.
