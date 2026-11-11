import { useEffect, useState } from "react";
import { api, gradeFor } from "./api";

export default function Lecturer() {
  const [courses, setCourses] = useState([]);
  const [students, setStudents] = useState([]);
  const [courseId, setCourseId] = useState("");
  const [session, setSession] = useState("2026/2027");
  const [rows, setRows] = useState({});   // student_id -> {ca, exam, status}
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api("/lecturer/courses").then(setCourses);
    api("/lecturer/students").then(setStudents);
  }, []);

  const load = async () => {
    if (!courseId || !session) return;
    const list = await api(`/lecturer/results?course_id=${courseId}&session=${encodeURIComponent(session)}`);
    setRows(Object.fromEntries(list.map((r) => [r.student_id, { ca: r.ca, exam: r.exam, status: r.status, saved: true }])));
    setMsg("");
  };
  useEffect(() => { load().catch((e) => setMsg(e.message)); }, [courseId, session]);

  const edit = (id, k, v) =>
    setRows((r) => ({ ...r, [id]: { ca: "", exam: "", status: "draft", ...r[id], [k]: v, saved: false } }));

  const saveAll = async () => {
    setMsg("");
    const dirty = Object.entries(rows).filter(([, r]) => !r.saved && r.status === "draft" && r.ca !== "" && r.exam !== "");
    try {
      for (const [id, r] of dirty)
        await api("/lecturer/results", { method: "PUT", body: { student_id: +id, course_id: +courseId, session, ca: +r.ca, exam: +r.exam } });
      await load(); setMsg(`Saved ${dirty.length} score${dirty.length === 1 ? "" : "s"}.`);
    } catch (e) { setMsg(e.message); }
  };

  const submit = async () => {
    if (!confirm("Submit all saved scores for approval? You cannot edit them afterwards.")) return;
    try {
      const r = await api("/lecturer/results/submit", { method: "POST", body: { course_id: +courseId, session } });
      await load(); setMsg(`Submitted ${r.submitted} result${r.submitted === 1 ? "" : "s"} for approval.`);
    } catch (e) { setMsg(e.message); }
  };

  return (
    <>
      <h2>Enter scores</h2>
      <div className="row">
        <label>Course
          <select value={courseId} onChange={(e) => setCourseId(e.target.value)}>
            <option value="">Choose a course</option>
            {courses.map((c) => <option key={c.id} value={c.id}>{c.code} {c.title}</option>)}
          </select>
        </label>
        <label>Session<input value={session} onChange={(e) => setSession(e.target.value)} placeholder="2026/2027" /></label>
      </div>
      {courses.length === 0 && <p className="empty">No courses assigned to you yet. Ask the admin to assign one.</p>}
      {courseId && (
        <>
          <div className="scroll">
            <table>
              <thead><tr><th>Matric no.</th><th>Name</th><th className="n">CA (max 30)</th><th className="n">Exam (max 70)</th><th className="n">Total</th><th>Grade</th><th>Status</th></tr></thead>
              <tbody>{students.map((s) => {
                const r = rows[s.id] || { ca: "", exam: "", status: "draft" };
                const locked = r.status !== "draft";
                const total = r.ca === "" || r.exam === "" ? null : +r.ca + +r.exam;
                return (
                  <tr key={s.id}>
                    <td>{s.matric_no}</td><td>{s.full_name}</td>
                    <td className="n"><input type="number" min="0" max="30" disabled={locked} value={r.ca} onChange={(e) => edit(s.id, "ca", e.target.value)} aria-label={`CA for ${s.matric_no}`} /></td>
                    <td className="n"><input type="number" min="0" max="70" disabled={locked} value={r.exam} onChange={(e) => edit(s.id, "exam", e.target.value)} aria-label={`Exam for ${s.matric_no}`} /></td>
                    <td className="n">{total ?? ""}</td>
                    <td><b>{total === null ? "" : gradeFor(total)}</b></td>
                    <td><span className={`tag ${r.status}`}>{r.saved === false ? "unsaved" : r.status}</span></td>
                  </tr>
                );
              })}</tbody>
            </table>
          </div>
          <div className="row">
            <button className="primary" onClick={saveAll}>Save scores</button>
            <button onClick={submit}>Submit for approval</button>
          </div>
        </>
      )}
      {msg && <p role="status">{msg}</p>}
    </>
  );
}
