import os
if os.path.exists("results.db"): os.remove("results.db")
from fastapi.testclient import TestClient
from app.main import app
c = TestClient(app)
H = lambda t: {"Authorization": f"Bearer {t}"}
def login(e, p): return c.post("/auth/login", data={"username": e, "password": p}).json()["access_token"]

assert c.post("/auth/bootstrap", json={"email":"a@x.com","full_name":"Admin","password":"secret1","role":"admin"}).status_code == 201
adm = login("a@x.com", "secret1")
lec_id = c.post("/admin/users", headers=H(adm), json={"email":"l@x.com","full_name":"Dr L","password":"secret1","role":"lecturer"}).json()["id"]
sid = c.post("/admin/students", headers=H(adm), json={"email":"s@x.com","full_name":"Stu","password":"secret1","matric_no":"CSC/2022/001","level":400,"department":"CSC"}).json()["student_id"]
c1 = c.post("/admin/courses", headers=H(adm), json={"code":"CSC401","title":"AI","units":3,"semester":"harmattan"}).json()["id"]
c2 = c.post("/admin/courses", headers=H(adm), json={"code":"CSC402","title":"Networks","units":2,"semester":"harmattan"}).json()["id"]
for cid in (c1, c2): c.post("/admin/assignments", headers=H(adm), json={"course_id":cid,"lecturer_id":lec_id})
lec = login("l@x.com", "secret1")
assert c.put("/lecturer/results", headers=H(lec), json={"student_id":sid,"course_id":c1,"session":"2026/2027","ca":25,"exam":50}).json()["grade"] == "A"
c.put("/lecturer/results", headers=H(lec), json={"student_id":sid,"course_id":c2,"session":"2026/2027","ca":20,"exam":35})  # 55 -> C
assert c.put("/lecturer/results", headers=H(lec), json={"student_id":sid,"course_id":c1,"session":"2026/2027","ca":99,"exam":1}).status_code == 422
stu = login("s@x.com", "secret1")
assert c.get("/student/results", headers=H(stu)).json()["terms"] == []          # not approved yet
for cid in (c1, c2):
    c.post("/lecturer/results/submit", headers=H(lec), json={"course_id":cid,"session":"2026/2027"})
    c.post("/admin/results/approve", headers=H(adm), json={"course_id":cid,"session":"2026/2027"})
out = c.get("/student/results", headers=H(stu)).json()
assert out["cgpa"] == 4.2, out   # (5*3 + 3*2) / 5
assert c.get("/admin/courses", headers=H(stu)).status_code == 403
assert len(c.get("/admin/courses", headers=H(adm)).json()) == 2
assert c.post("/admin/courses", headers=H(stu), json={"code":"X","title":"X","units":1,"semester":"rain"}).status_code == 403
print("ALL OK, CGPA =", out["cgpa"])
