from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import User, Student, Course, CourseAssignment, Result
from .grading import grade_for, gpa
from .security import hash_password, verify_password, make_token, current_user, require

Base.metadata.create_all(engine)
app = FastAPI(title="Student Results Management")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])

CA_MAX, EXAM_MAX = 30, 70  # adjust to your department's scheme


# ---------- schemas ----------
class UserIn(BaseModel):
    email: str
    full_name: str
    password: str = Field(min_length=6)
    role: str = Field(pattern="^(lecturer|admin)$")


class StudentIn(BaseModel):
    email: str
    full_name: str
    password: str = Field(min_length=6)
    matric_no: str
    level: int
    department: str


class CourseIn(BaseModel):
    code: str
    title: str
    units: int = Field(gt=0, le=6)
    semester: str = Field(pattern="^(harmattan|rain)$")


class AssignIn(BaseModel):
    course_id: int
    lecturer_id: int


class ScoreIn(BaseModel):
    student_id: int
    course_id: int
    session: str
    ca: float = Field(ge=0, le=CA_MAX)
    exam: float = Field(ge=0, le=EXAM_MAX)


class BatchIn(BaseModel):
    course_id: int
    session: str


# ---------- auth ----------
@app.post("/auth/bootstrap", status_code=201)
def bootstrap(body: UserIn, db: Session = Depends(get_db)):
    """Create the very first admin. Disabled once any user exists."""
    if db.query(User).first():
        raise HTTPException(403, "Already bootstrapped")
    u = User(email=body.email, full_name=body.full_name,
             hashed_password=hash_password(body.password), role="admin")
    db.add(u); db.commit()
    return {"id": u.id}


@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    u = db.query(User).filter_by(email=form.username).first()
    if not u or not verify_password(form.password, u.hashed_password):
        raise HTTPException(401, "Wrong email or password")
    return {"access_token": make_token(u), "token_type": "bearer", "role": u.role}


@app.get("/me")
def me(u: User = Depends(current_user)):
    return {"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role}


# ---------- admin ----------
@app.post("/admin/users", status_code=201)
def create_staff(body: UserIn, db: Session = Depends(get_db), _=Depends(require("admin"))):
    if db.query(User).filter_by(email=body.email).first():
        raise HTTPException(409, "Email already exists")
    u = User(email=body.email, full_name=body.full_name,
             hashed_password=hash_password(body.password), role=body.role)
    db.add(u); db.commit()
    return {"id": u.id}


@app.post("/admin/students", status_code=201)
def create_student(body: StudentIn, db: Session = Depends(get_db), _=Depends(require("admin"))):
    if db.query(User).filter_by(email=body.email).first() or \
       db.query(Student).filter_by(matric_no=body.matric_no).first():
        raise HTTPException(409, "Email or matric number already exists")
    u = User(email=body.email, full_name=body.full_name,
             hashed_password=hash_password(body.password), role="student")
    db.add(u); db.flush()
    s = Student(user_id=u.id, matric_no=body.matric_no, level=body.level, department=body.department)
    db.add(s); db.commit()
    return {"student_id": s.id, "user_id": u.id}


@app.post("/admin/courses", status_code=201)
def create_course(body: CourseIn, db: Session = Depends(get_db), _=Depends(require("admin"))):
    if db.query(Course).filter_by(code=body.code).first():
        raise HTTPException(409, "Course code exists")
    c = Course(**body.model_dump()); db.add(c); db.commit()
    return {"id": c.id}


@app.post("/admin/assignments", status_code=201)
def assign(body: AssignIn, db: Session = Depends(get_db), _=Depends(require("admin"))):
    lec = db.get(User, body.lecturer_id)
    if not lec or lec.role != "lecturer" or not db.get(Course, body.course_id):
        raise HTTPException(404, "Lecturer or course not found")
    db.add(CourseAssignment(course_id=body.course_id, lecturer_id=body.lecturer_id)); db.commit()
    return {"ok": True}


@app.post("/admin/results/approve")
def approve(body: BatchIn, db: Session = Depends(get_db), _=Depends(require("admin"))):
    rows = db.query(Result).filter_by(course_id=body.course_id, session=body.session,
                                      status="submitted").all()
    for r in rows:
        r.status = "approved"
    db.commit()
    return {"approved": len(rows)}


@app.post("/admin/results/reject")
def reject(body: BatchIn, db: Session = Depends(get_db), _=Depends(require("admin"))):
    rows = db.query(Result).filter_by(course_id=body.course_id, session=body.session,
                                      status="submitted").all()
    for r in rows:
        r.status = "draft"
    db.commit()
    return {"returned_to_draft": len(rows)}


# ---------- lecturer ----------
def _assigned(db, lecturer_id, course_id):
    return db.query(CourseAssignment).filter_by(lecturer_id=lecturer_id, course_id=course_id).first()


@app.get("/lecturer/courses")
def my_courses(db: Session = Depends(get_db), u: User = Depends(require("lecturer"))):
    rows = db.query(Course).join(CourseAssignment).filter(CourseAssignment.lecturer_id == u.id).all()
    return [{"id": c.id, "code": c.code, "title": c.title, "units": c.units, "semester": c.semester}
            for c in rows]


@app.put("/lecturer/results")
def enter_score(body: ScoreIn, db: Session = Depends(get_db), u: User = Depends(require("lecturer"))):
    if not _assigned(db, u.id, body.course_id):
        raise HTTPException(403, "You are not assigned to this course")
    if not db.get(Student, body.student_id):
        raise HTTPException(404, "Student not found")
    total = body.ca + body.exam
    letter, pts = grade_for(total)
    r = db.query(Result).filter_by(student_id=body.student_id, course_id=body.course_id,
                                   session=body.session).first()
    if r and r.status != "draft":
        raise HTTPException(409, f"Result is {r.status} and can no longer be edited")
    if not r:
        r = Result(student_id=body.student_id, course_id=body.course_id, session=body.session)
        db.add(r)
    r.ca, r.exam, r.total, r.grade, r.points = body.ca, body.exam, total, letter, pts
    db.commit()
    return {"id": r.id, "total": total, "grade": letter}


@app.post("/lecturer/results/submit")
def submit(body: BatchIn, db: Session = Depends(get_db), u: User = Depends(require("lecturer"))):
    if not _assigned(db, u.id, body.course_id):
        raise HTTPException(403, "You are not assigned to this course")
    rows = db.query(Result).filter_by(course_id=body.course_id, session=body.session,
                                      status="draft").all()
    for r in rows:
        r.status = "submitted"
    db.commit()
    return {"submitted": len(rows)}


# ---------- student ----------
@app.get("/student/results")
def my_results(db: Session = Depends(get_db), u: User = Depends(require("student"))):
    s = db.query(Student).filter_by(user_id=u.id).first()
    rows = db.query(Result).filter_by(student_id=s.id, status="approved").all()
    by_term = {}
    for r in rows:
        by_term.setdefault((r.session, r.course.semester), []).append(r)
    terms = [{
        "session": sess, "semester": sem,
        "gpa": gpa([(r.points, r.course.units) for r in rs]),
        "results": [{"code": r.course.code, "title": r.course.title, "units": r.course.units,
                     "ca": r.ca, "exam": r.exam, "total": r.total, "grade": r.grade} for r in rs],
    } for (sess, sem), rs in sorted(by_term.items())]
    return {"matric_no": s.matric_no, "terms": terms,
            "cgpa": gpa([(r.points, r.course.units) for r in rows])}


# ---------- list endpoints used by the frontend ----------
@app.get("/admin/courses")
def list_courses(db: Session = Depends(get_db), _=Depends(require("admin"))):
    out = []
    for c in db.query(Course).order_by(Course.code).all():
        lecs = db.query(User).join(CourseAssignment, CourseAssignment.lecturer_id == User.id)\
                 .filter(CourseAssignment.course_id == c.id).all()
        out.append({"id": c.id, "code": c.code, "title": c.title, "units": c.units,
                    "semester": c.semester, "lecturers": [l.full_name for l in lecs]})
    return out


@app.get("/admin/lecturers")
def list_lecturers(db: Session = Depends(get_db), _=Depends(require("admin"))):
    return [{"id": u.id, "full_name": u.full_name, "email": u.email}
            for u in db.query(User).filter_by(role="lecturer").order_by(User.full_name).all()]


@app.get("/admin/students")
def list_students(db: Session = Depends(get_db), _=Depends(require("admin"))):
    return [{"id": s.id, "full_name": s.user.full_name, "matric_no": s.matric_no,
             "level": s.level, "department": s.department}
            for s in db.query(Student).order_by(Student.matric_no).all()]


@app.get("/admin/submissions")
def submissions(db: Session = Depends(get_db), _=Depends(require("admin"))):
    groups = {}
    for r in db.query(Result).filter_by(status="submitted").all():
        g = groups.setdefault((r.course_id, r.session), {"course_id": r.course_id,
              "code": r.course.code, "title": r.course.title, "session": r.session, "count": 0})
        g["count"] += 1
    return list(groups.values())


@app.get("/lecturer/students")
def lecturer_students(db: Session = Depends(get_db), _=Depends(require("lecturer"))):
    return [{"id": s.id, "full_name": s.user.full_name, "matric_no": s.matric_no}
            for s in db.query(Student).order_by(Student.matric_no).all()]


@app.get("/lecturer/results")
def lecturer_results(course_id: int, session: str, db: Session = Depends(get_db),
                     u: User = Depends(require("lecturer"))):
    if not _assigned(db, u.id, course_id):
        raise HTTPException(403, "You are not assigned to this course")
    rows = db.query(Result).filter_by(course_id=course_id, session=session).all()
    return [{"student_id": r.student_id, "ca": r.ca, "exam": r.exam, "total": r.total,
             "grade": r.grade, "status": r.status} for r in rows]
