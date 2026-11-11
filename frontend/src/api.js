const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
let token = sessionStorage.getItem("token") || "";
export const setToken = (t) => { token = t; t ? sessionStorage.setItem("token", t) : sessionStorage.removeItem("token"); };

export async function api(path, { method = "GET", body, form } = {}) {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  let payload;
  if (form) payload = new URLSearchParams(form);
  else if (body) { headers["Content-Type"] = "application/json"; payload = JSON.stringify(body); }
  const res = await fetch(BASE + path, { method, headers, body: payload });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data.detail;
    throw new Error(Array.isArray(d) ? d.map((e) => `${e.loc.at(-1)}: ${e.msg}`).join("; ") : d || "Request failed");
  }
  return data;
}

export const gradeFor = (t) =>
  [[70, "A"], [60, "B"], [50, "C"], [45, "D"], [40, "E"], [0, "F"]].find(([f]) => t >= f)[1];
