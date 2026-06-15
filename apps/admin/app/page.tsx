export default async function Admin() {
  let state = "unreachable";
  try {
    const response = await fetch(`${process.env.API_URL ?? "http://localhost:8000"}/health`, { cache: "no-store" });
    if (response.ok) state = "healthy";
  } catch {}
  return <main><p>ARROWERA / ADMIN</p><h1>Foundation status</h1><p>API: {state}</p><p>This surface is intentionally limited to operational status.</p></main>;
}
