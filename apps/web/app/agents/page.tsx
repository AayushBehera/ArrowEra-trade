"use client";

import { useState, FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { Bot, Loader2, Clock, Cpu } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@arrowera/ui";
import { Button } from "@arrowera/ui";
import { Input } from "@arrowera/ui";
import { Badge } from "@arrowera/ui";
import { api } from "../../lib/api";

export default function AgentsPage() {
  const [prompt, setPrompt] = useState("");
  const [provider, setProvider] = useState("");
  const [results, setResults] = useState<Array<{ id: string; content: string; provider: string; model: string; durationMs: number }>>([]);

  const mutation = useMutation({
    mutationFn: () => api.runMarketAnalyst({ prompt, provider: provider || undefined }),
    onSuccess: (data) => {
      setResults((prev) => [data, ...prev].slice(0, 10));
    },
  });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    mutation.mutate();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Agent Console</h1>
        <p className="text-sm text-muted">Run AI agents with full traceability and provider selection.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Market Analyst Agent</CardTitle>
          <CardDescription>Cautious analysis with data-backed reasoning</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-1 block">Research Question</label>
              <textarea
                className="flex min-h-[100px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Analyze the current market conditions for tech stocks..."
                minLength={10}
                required
              />
            </div>
            <div className="flex gap-3 items-end">
              <div className="w-48">
                <label className="text-sm font-medium mb-1 block">Provider (optional)</label>
                <select
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                >
                  <option value="">Auto</option>
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="gemini">Gemini</option>
                  <option value="deepseek">DeepSeek</option>
                  <option value="ollama">Ollama</option>
                </select>
              </div>
              <Button type="submit" disabled={mutation.isPending || !prompt.trim()}>
                {mutation.isPending ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Analyzing...</>
                ) : (
                  <><Bot className="mr-2 h-4 w-4" /> Run Analysis</>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Results</h2>
          {results.map((result, i) => (
            <Card key={result.id || i}>
              <CardHeader>
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge variant="outline">{result.provider}</Badge>
                  <Badge variant="secondary">{result.model}</Badge>
                  <div className="flex items-center gap-1 text-xs text-muted">
                    <Clock className="h-3 w-3" />
                    {(result.durationMs / 1000).toFixed(1)}s
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm whitespace-pre-wrap">{result.content}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
