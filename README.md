# ECG Defect Reporting Web System - Final Web Version

## Default test accounts
Boss: boss / boss123
Admin: admin / admin123
Station: kuntenase / station123

## Run locally
Open this folder in Command Prompt and run:

pip install -r requirements.txt
python app.py

Then open http://127.0.0.1:5000

## Deploy online on Render
1. Create or open your GitHub account.
2. Create a new repository.
3. Upload all files in this folder to that repository.
4. Go to Render and create a New Web Service.
5. Connect the GitHub repository.
6. Build Command: pip install -r requirements.txt
7. Start Command: gunicorn app:app
8. Add SECRET_KEY as an environment variable.
9. For serious use, add PostgreSQL and set DATABASE_URL.

Important: free hosting may lose uploaded photos/database when the server rebuilds. For real use, deploy with PostgreSQL and persistent storage.
