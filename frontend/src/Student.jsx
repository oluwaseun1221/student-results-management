import { useEffect, useState } from "react";
import { api } from "./api";

export default function Student() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => { api("/student/results").then(setD).catch((e) => setErr(e.message)); }, []);
  if (err) return <p className="err">{err}</p>;
  if (!d) return <p>Loading results...</p>;
  return (
    <>
      <section className="cgpa">
        <div className="big">{d.cgpa.toFixed(2)}</div>
        <div>Cumulative GPA out of 5.00<br /><small>{d.matric_no}</small></div>
      </section>
      {d.terms.length === 0 && <p className="empty">No approved results yet. They appear here once your department approves them.</p>}
      {d.terms.map((t) => (
        <section key={t.session + t.semester}>
          <h2>{t.session}, {t.semester} semester <small>GPA {t.gpa.toFixed(2)}</small></h2>
          <div className="scroll">
            <table>
              <thead><tr><th>Course</th><th>Title</th><th className="n">Units</th><th className="n">CA</th><th className="n">Exam</th><th className="n">Total</th><th>Grade</th></tr></thead>
              <tbody>{t.results.map((r) => (
                <tr key={r.code}><td>{r.code}</td><td>{r.title}</td><td className="n">{r.units}</td><td className="n">{r.ca}</td><td className="n">{r.exam}</td><td className="n">{r.total}</td><td><b>{r.grade}</b></td></tr>
              ))}</tbody>
            </table>
          </div>
        </section>
      ))}
      <button onClick={() => window.print()}>Print result slip</button>
    </>
  );
}
