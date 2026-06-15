"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Microscope, Loader2, FlaskConical } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@arrowera/ui";
import { Button } from "@arrowera/ui";
import { Input } from "@arrowera/ui";
import { Badge } from "@arrowera/ui";
import { api } from "../../lib/api";

const AGENT_TYPES = [
  { id: "market", label: "Market Analyst", desc: "Trend analysis and index performance" },
  { id: "technical", label: "Technical Analyst", desc: "Chart patterns and indicator signals" },
  { id: "fundamental", label: "Fundamental Analyst", desc: "Financial ratios and valuation" },
  { id: "macro", label: "Macro Analyst", desc: "Economic indicators and sector rotation" },
  { id: "sentiment", label: "Sentiment Analyst", desc: "News sentiment and social signals" },
];

export default function ResearchPage() {
  const [symbol, setSymbol] = useState("AAPL");
  const [question, setQuestion] = useState("");
  const [activeAgent, setActiveAgent] = useState<string | null>(null);

  const analystMutation = useMutation({
    mutationFn: ({ agentType, payload }: { agentType: string; payload: { symbol: string; question: string } }) =>
      api.runAnalyst(agentType, payload),
  });

  const reportMutation = useMutation({
    mutationFn: (payload: { symbol: string; question: string }) =>
      api.generateResearchReport(payload),
  });

  const runAnalyst = (agentType: string) => {
    setActiveAgent(agentType);
    analystMutation.mutate({ agentType, payload: { symbol, question: question || `Analyze ${symbol}` } });
  };

  const runFullReport = () => {
    reportMutation.mutate({ symbol, question: question || `Full research report on ${symbol}` });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Research Center</h1>
        <p className="text-sm text-muted">AI-powered research from five specialist analysts.</p>
      </div>

      {/* Research Input */}
      <Card>
        <CardHeader>
          <CardTitle>Research Query</CardTitle>
          <CardDescription>Enter a symbol and optional question</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3 items-end flex-wrap">
            <div className="w-32">
              <label className="text-sm font-medium mb-1 block">Symbol</label>
              <Input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} placeholder="AAPL" />
            </div>
            <div className="flex-1 min-w-[200px]">
              <label className="text-sm font-medium mb-1 block">Question (optional)</label>
              <Input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="What are the key risks?" />
            </div>
            <Button onClick={runFullReport} disabled={reportMutation.isPending || !symbol}>
              {reportMutation.isPending ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Generating...</>
              ) : (
                <><Microscope className="mr-2 h-4 w-4" /> Full Report</>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Agent Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {AGENT_TYPES.map((agent) => (
          <Card key={agent.id} className="flex flex-col">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{agent.label}</CardTitle>
                <FlaskConical className="h-4 w-4 text-muted" />
              </div>
              <CardDescription>{agent.desc}</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <Button
                variant="outline"
                size="sm"
                className="mt-auto"
                onClick={() => runAnalyst(agent.id)}
                disabled={analystMutation.isPending && activeAgent === agent.id}
              >
                {analystMutation.isPending && activeAgent === agent.id ? (
                  <><Loader2 className="mr-2 h-3 w-3 animate-spin" /> Running...</>
                ) : (
                  "Run Analysis"
                )}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Results */}
      {analystMutation.isSuccess && analystMutation.data && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <CardTitle>Analysis Result</CardTitle>
              <Badge variant="outline">{analystMutation.data.agent ?? activeAgent}</Badge>
              {analystMutation.data.provider && (
                <Badge variant="secondary">{analystMutation.data.provider}</Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none whitespace-pre-wrap">{analystMutation.data.content}</div>
          </CardContent>
        </Card>
      )}

      {/* Full Report */}
      {reportMutation.isSuccess && reportMutation.data && (
        <Card>
          <CardHeader>
            <CardTitle>Research Report</CardTitle>
            <CardDescription>
              Synthesized from {Object.keys(reportMutation.data.analyses ?? {}).length} analysts
              {reportMutation.data.totalDurationMs && ` in ${(reportMutation.data.totalDurationMs / 1000).toFixed(1)}s`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-md border border-border p-4">
              <h3 className="font-semibold mb-2">Synthesis</h3>
              <p className="text-sm whitespace-pre-wrap">{reportMutation.data.synthesis}</p>
            </div>
            {Object.entries(reportMutation.data.analyses ?? {}).map(([key, analysis]) => (
              <div key={key} className="rounded-md border border-border p-4">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="font-semibold capitalize">{key.replace("_", " ")}</h3>
                  {analysis.provider && <Badge variant="secondary" className="text-xs">{analysis.provider}</Badge>}
                </div>
                <p className="text-sm whitespace-pre-wrap">{analysis.content}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
