import { useEffect, useState } from "react";
import { api, setToken } from "./api";
import Admin from "./Admin.jsx";
import Lecturer from "./Lecturer.jsx";
import Student from "./Student.jsx";

function Login({ onDone }) {
  const [f, setF] = useState({ username: "", password: "" });
  const [err, setErr] = useState("");
  const submit = async (e) => {
    e.preventDefault(); setErr("");
    try {
      const r = await api("/auth/login", { method: "POST", form: f });
      setToken(r.access_token); onDone();
    } catch (x) { setErr(x.message); }
  };
  return (
    <main className="login">
      <h1>Student Results</h1>
      <p>Sign in with your school email.</p>
      <form onSubmit={submit}>
        <label>Email<input type="email" required value={f.username} onChange={(e) => setF({ ...f, username: e.target.value })} /></label>
        <label>Password<input type="password" required value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} /></label>
        {err && <p className="err" role="alert">{err}</p>}
        <button className="primary">Sign in</button>
      </form>
    </main>
  );
}

export default function App() {
  const [me, setMe] = useState(null);
  const [ready, setReady] = useState(false);
  const load = () => api("/me").then(setMe).catch(() => setMe(null)).finally(() => setReady(true));
  useEffect(() => { load(); }, []);
  if (!ready) return null;
  if (!me) return <Login onDone={load} />;
  const View = { admin: Admin, lecturer: Lecturer, student: Student }[me.role];
  return (
    <>
      <header className="bar">
        <strong>Student Results</strong>
        <span>{me.full_name} ({me.role})</span>
        <button onClick={() => { setToken(""); setMe(null); }}>Sign out</button>
      </header>
      <main className="page"><View me={me} /></main>
    </>
  );
}
