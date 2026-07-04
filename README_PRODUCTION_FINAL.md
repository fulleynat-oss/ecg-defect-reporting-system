# ECG Defect Reporting Web System - PRODUCTION FINAL

This is the final deployment-ready package.

## Included
- Login system
- Station attendant defect submission form
- Boss dashboard
- Records/search page
- CSV export
- Photo upload support
- PostgreSQL support through DATABASE_URL
- Render deployment files: Procfile, render.yaml, requirements.txt

## Default test accounts
Boss: boss / boss123
Admin: admin / admin123
Station: kuntenase / station123

Change these passwords before official use.

## Production database
For live use, use Render PostgreSQL.

The application already supports this:
- If DATABASE_URL exists, it uses PostgreSQL.
- If DATABASE_URL is absent, it uses local SQLite for laptop testing only.

## Render deployment steps
1. Upload this full folder to GitHub.
2. Go to Render.
3. Create a PostgreSQL database first.
4. Copy the PostgreSQL Internal Database URL.
5. Create a Web Service from the GitHub repository.
6. Use these settings:

Build Command:
pip install -r requirements.txt

Start Command:
gunicorn app:app

7. Add environment variables:
SECRET_KEY = any long random text
DATABASE_URL = paste the Render PostgreSQL Internal Database URL

8. Deploy.

## How attendants use it
They open the Render website link, login with their station account, fill the form, and submit.

## How your boss uses it
He opens the same link, logs in as boss, and sees all submitted defects.

## Important note about photos
Database records will be permanent with PostgreSQL. Uploaded photos may need persistent disk or external storage for official long-term use on Render. The report records and dashboard will still work.
