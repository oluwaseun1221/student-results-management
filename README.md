# Student Results Management
React + FastAPI. Roles: admin, lecturer, student.

## Run backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload      # docs at http://127.0.0.1:8000/docs
python test_smoke.py               # end-to-end check

First run: POST /auth/bootstrap once to create the admin.
Set SECRET_KEY in your environment before deploying.

## Workflow
admin creates courses/students/lecturers and assigns courses
-> lecturer enters scores (draft) and submits
-> admin approves (or rejects back to draft)
-> student sees approved results, GPA per semester, and CGPA

## Run frontend
cd frontend
npm install
npm run dev                        # http://localhost:5173
Set VITE_API_URL if the backend is not at http://127.0.0.1:8000.
# student-results-management
