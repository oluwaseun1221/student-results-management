from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # student | lecturer | admin


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    matric_no = Column(String, unique=True, nullable=False)
    level = Column(Integer, nullable=False)
    department = Column(String, nullable=False)
    user = relationship("User")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    units = Column(Integer, nullable=False)
    semester = Column(String, nullable=False)  # harmattan | rain


class CourseAssignment(Base):
    __tablename__ = "course_assignments"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    lecturer_id = Column(Integer, ForeignKey("users.id"))
    __table_args__ = (UniqueConstraint("course_id", "lecturer_id"),)


class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    session = Column(String, nullable=False)  # e.g. 2026/2027
    ca = Column(Float, nullable=False)
    exam = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    grade = Column(String, nullable=False)
    points = Column(Integer, nullable=False)
    status = Column(String, default="draft")  # draft | submitted | approved
    course = relationship("Course")
    student = relationship("Student")
    __table_args__ = (UniqueConstraint("student_id", "course_id", "session"),)
