import { useEffect, useState } from "react";
import { api } from "./api";

function Form({ fields, onSubmit, label }) {
  const init = Object.fromEntries(fields.map((f) => [f.name, f.options ? f.options[0] : ""]));
  const [v, setV] = useState(init);
  const [err, setErr] = useState("");
  const go = async (e) => {
    e.preventDefault(); setErr("");
    try { await onSubmit(v); setV(init); } catch (x) { setErr(x.message); }
  };
  return (
    <form className="row" onSubmit={go}>
      {fields.map((f) => (
        <label key={f.name}>{f.label}
          {f.options
            ? <select value={v[f.name]} onChange={(e) => setV({ ...v, [f.name]: e.target.value })}>{f.options.map((o) => <option key={o}>{o}</option>)}</select>
            : <input required type={f.type || "text"} value={v[f.name]} onChange={(e) => setV({ ...v, [f.name]: e.target.value })} />}
        </label>
      ))}
      <button className="primary">{label}</button>
      {err && <p className="err" role="alert">{err}</p>}
    </form>
  );
}

export default function Admin() {
  const [tab, setTab] = useState("approvals");
  const [d, setD] = useState({ submissions: [], courses: [], lecturers: [], students: [] });
  const [assign, setAssign] = useState({ course_id: "", lecturer_id: "" });
  const refresh = async () => {
    const [submissions, courses, lecturers, students] = await Promise.all(
      ["submissions", "courses", "lecturers", "students"].map((p) => api(`/admin/${p}`)));
    setD({ submissions, courses, lecturers, students });
  };
  useEffect(() => { refresh(); }, []);
  const post = (path, body) => api(path, { method: "POST", body }).then(refresh);

  return (
    <>
      <nav className="tabs">
        {[["approvals", "Approvals"], ["courses", "Courses"], ["people", "People"]].map(([k, l]) => (
          <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{l}{k === "approvals" && d.submissions.length ? ` (${d.submissions.length})` : ""}</button>
        ))}
      </nav>

      {tab === "approvals" && (
        d.submissions.length === 0 ? <p className="empty">Nothing waiting for approval.</p> :
        <table>
          <thead><tr><th>Course</th><th>Session</th><th className="n">Results</th><th></th></tr></thead>
          <tbody>{d.submissions.map((s) => (
            <tr key={s.course_id + s.session}>
              <td>{s.code} {s.title}</td><td>{s.session}</td><td className="n">{s.count}</td>
              <td className="row">
                <button className="primary" onClick={() => post("/admin/results/approve", { course_id: s.course_id, session: s.session })}>Approve</button>
                <button onClick={() => post("/admin/results/reject", { course_id: s.course_id, session: s.session })}>Return to lecturer</button>
              </td>
            </tr>))}</tbody>
        </table>
      )}

      {tab === "courses" && (
        <>
          <h2>Add a course</h2>
          <Form label="Add course" onSubmit={(v) => post("/admin/courses", { ...v, units: +v.units })}
            fields={[{ name: "code", label: "Code" }, { name: "title", label: "Title" }, { name: "units", label: "Units", type: "number" }, { name: "semester", label: "Semester", options: ["harmattan", "rain"] }]} />
          <h2>Assign a lecturer</h2>
          <div className="row">
            <label>Course<select value={assign.course_id} onChange={(e) => setAssign({ ...assign, course_id: e.target.value })}><option value="">Choose</option>{d.courses.map((c) => <option key={c.id} value={c.id}>{c.code}</option>)}</select></label>
            <label>Lecturer<select value={assign.lecturer_id} onChange={(e) => setAssign({ ...assign, lecturer_id: e.target.value })}><option value="">Choose</option>{d.lecturers.map((l) => <option key={l.id} value={l.id}>{l.full_name}</option>)}</select></label>
            <button className="primary" disabled={!assign.course_id || !assign.lecturer_id}
              onClick={() => post("/admin/assignments", { course_id: +assign.course_id, lecturer_id: +assign.lecturer_id }).catch((e) => alert(e.message))}>Assign</button>
          </div>
          <table>
            <thead><tr><th>Code</th><th>Title</th><th className="n">Units</th><th>Semester</th><th>Lecturers</th></tr></thead>
            <tbody>{d.courses.map((c) => <tr key={c.id}><td>{c.code}</td><td>{c.title}</td><td className="n">{c.units}</td><td>{c.semester}</td><td>{c.lecturers.join(", ") || "none yet"}</td></tr>)}</tbody>
          </table>
        </>
      )}

      {tab === "people" && (
        <>
          <h2>Add a lecturer</h2>
          <Form label="Add lecturer" onSubmit={(v) => post("/admin/users", { ...v, role: "lecturer" })}
            fields={[{ name: "full_name", label: "Full name" }, { name: "email", label: "Email", type: "email" }, { name: "password", label: "Temporary password", type: "password" }]} />
          <h2>Add a student</h2>
          <Form label="Add student" onSubmit={(v) => post("/admin/students", { ...v, level: +v.level })}
            fields={[{ name: "full_name", label: "Full name" }, { name: "matric_no", label: "Matric no." }, { name: "level", label: "Level", type: "number" }, { name: "department", label: "Department" }, { name: "email", label: "Email", type: "email" }, { name: "password", label: "Temporary password", type: "password" }]} />
          <h2>Students ({d.students.length})</h2>
          <div className="scroll"><table>
            <thead><tr><th>Matric no.</th><th>Name</th><th className="n">Level</th><th>Department</th></tr></thead>
            <tbody>{d.students.map((s) => <tr key={s.id}><td>{s.matric_no}</td><td>{s.full_name}</td><td className="n">{s.level}</td><td>{s.department}</td></tr>)}</tbody>
          </table></div>
          <h2>Lecturers ({d.lecturers.length})</h2>
          <ul>{d.lecturers.map((l) => <li key={l.id}>{l.full_name}, {l.email}</li>)}</ul>
        </>
      )}
    </>
  );
}
