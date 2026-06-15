"use client";

import { FormEvent, useState } from "react";
import { Button, Card } from "@arrowera/ui";
import { api } from "../lib/api";

export function AgentConsole() {
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setResult("");
    try {
      const response = await api.runMarketAnalyst({ prompt });
      setResult(response.content);
    } catch (error) {
      setResult(`Request failed: ${(error as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  return <Card><form className="form" onSubmit={submit}><label htmlFor="prompt">Research question</label><textarea id="prompt" minLength={10} required value={prompt} onChange={(e) => setPrompt(e.target.value)} /><Button disabled={busy}>{busy ? "Analyzing..." : "Run market analyst"}</Button>{result && <div className="status">{result}</div>}</form></Card>;
}
