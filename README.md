# CareerPilot AI

AI-powered academic and career guidance web application built with Flask and SQLite.

## Main Features
- Registration and login
- Student profile
- Career assessment
- 12-career recommendation engine
- Skill-gap analysis
- Personalized learning roadmap
- Career insights
- Courses and resources
- Progress tracking
- Jobs and internships section
- Resume builder and preview
- Resume analyzer
- Mock interview and evaluation
- Career chatbot
- English coach
- Job preparation

## Run locally
```bash
pip install -r requirements.txt
python app.py
```
Then open `http://127.0.0.1:5000`.

## Render
Build command: `pip install -r requirements.txt`
Start command: `gunicorn app:app`

## Notes
The recommendation, chatbot, English coach, interview scoring and resume analyzer are rule-based implementations in this version. They do not call an external LLM/API.


## Button and interaction notes
- Dashboard navigation cards open their linked feature pages.
- Career assessment, profile, login/register, resume, interview and English-coach forms submit to Flask routes.
- Roadmap career cards open the roadmap; course checkboxes update the progress bar; “Choose Another Career” returns to career selection.
- Learning-resource filter buttons and search filter the resource cards.
- Chatbot suggestion buttons send the suggested question; Send and Enter submit typed questions. While a reply is loading, Send is disabled to prevent duplicate requests.
- Print buttons open the browser print dialog. Voice controls require browser speech-recognition/speech-synthesis support and microphone permission.

If a page appears not to respond, sign in first where required, then refresh the page. Run from this project directory so SQLite uses the included database file.
