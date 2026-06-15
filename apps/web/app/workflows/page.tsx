"use client";

import { useState, useCallback } from "react";
import { GitBranch, Plus, Play, Trash2, Save, Download, ChevronRight, GripVertical } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@arrowera/ui";
import { Button } from "@arrowera/ui";
import { Input } from "@arrowera/ui";
import { Badge } from "@arrowera/ui";

// ---- Node types ----
const NODE_TYPES = [
  { id: "market_data", label: "Market Data", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  { id: "technical", label: "Technical Analysis", color: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
  { id: "fundamental", label: "Fundamental Analysis", color: "bg-green-500/20 text-green-400 border-green-500/30" },
  { id: "macro", label: "Macro Analysis", color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" },
  { id: "sentiment", label: "Sentiment Analysis", color: "bg-pink-500/20 text-pink-400 border-pink-500/30" },
  { id: "risk", label: "Risk Engine", color: "bg-red-500/20 text-red-400 border-red-500/30" },
  { id: "signal", label: "Signal Generator", color: "bg-orange-500/20 text-orange-400 border-orange-500/30" },
  { id: "synthesis", label: "Synthesis", color: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30" },
  { id: "report", label: "Report Writer", color: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30" },
  { id: "custom", label: "Custom Code", color: "bg-gray-500/20 text-gray-400 border-gray-500/30" },
];

interface WorkflowNode {
  id: string;
  type: string;
  label: string;
  config: Record<string, string>;
}

const PRESET_WORKFLOWS = [
  { id: "full_research", name: "Full Research Report", desc: "Runs all 5 analysts and synthesizes results into an investment thesis." },
  { id: "trade_decision", name: "Trade Decision", desc: "Technical + fundamental analysis with risk check and signal generation." },
  { id: "portfolio_review", name: "Portfolio Review", desc: "Risk analysis + rebalancing suggestions for your portfolio." },
];

let nodeCounter = 0;

export default function WorkflowsPage() {
  const [nodes, setNodes] = useState<WorkflowNode[]>([
    { id: "n1", type: "market_data", label: "Market Data", config: {} },
    { id: "n2", type: "technical", label: "Technical Analysis", config: {} },
    { id: "n3", type: "synthesis", label: "Synthesis", config: {} },
  ]);
  const [workflowName, setWorkflowName] = useState("My Custom Workflow");
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [executionStatus, setExecutionStatus] = useState<string | null>(null);
  const [symbol, setSymbol] = useState("SPY");

  const addNode = useCallback((type: string) => {
    const nodeType = NODE_TYPES.find((n) => n.id === type);
    if (!nodeType) return;
    nodeCounter++;
    setNodes((prev) => [...prev, { id: `n_${Date.now()}_${nodeCounter}`, type, label: nodeType.label, config: {} }]);
  }, []);

  const removeNode = useCallback((id: string) => {
    setNodes((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const moveNode = useCallback((index: number, direction: "up" | "down") => {
    setNodes((prev) => {
      const arr = [...prev];
      const target = direction === "up" ? index - 1 : index + 1;
      if (target < 0 || target >= arr.length) return arr;
      [arr[index], arr[target]] = [arr[target], arr[index]];
      return arr;
    });
  }, []);

  const loadPreset = (presetId: string) => {
    setSelectedPreset(presetId);
    if (presetId === "full_research") {
      setNodes([
        { id: "p1", type: "market", label: "Market Analyst", config: {} },
        { id: "p2", type: "technical", label: "Technical Analyst", config: {} },
        { id: "p3", type: "fundamental", label: "Fundamental Analyst", config: {} },
        { id: "p4", type: "macro", label: "Macro Analyst", config: {} },
        { id: "p5", type: "sentiment", label: "Sentiment Analyst", config: {} },
        { id: "p6", type: "synthesis", label: "Synthesis", config: {} },
      ]);
      setWorkflowName("Full Research Report");
    } else if (presetId === "trade_decision") {
      setNodes([
        { id: "td1", type: "market_data", label: "Market Data", config: {} },
        { id: "td2", type: "technical", label: "Technical Analysis", config: {} },
        { id: "td3", type: "risk", label: "Risk Engine", config: {} },
        { id: "td4", type: "signal", label: "Signal Generator", config: {} },
      ]);
      setWorkflowName("Trade Decision");
    } else {
      setNodes([
        { id: "pr1", type: "fundamental", label: "Fundamental Review", config: {} },
        { id: "pr2", type: "macro", label: "Macro Context", config: {} },
        { id: "pr3", type: "risk", label: "Risk Review", config: {} },
        { id: "pr4", type: "synthesis", label: "Synthesis", config: {} },
      ]);
      setWorkflowName("Portfolio Review");
    }
  };

  const executeWorkflow = async () => {
    setExecutionStatus("running");
    // In production: POST /api/v1/workflows/execute
    setTimeout(() => setExecutionStatus("completed"), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Workflow Builder</h1>
          <p className="text-sm text-muted">Design and execute custom agent pipelines.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Save className="mr-2 h-4 w-4" /> Save
          </Button>
          <Button size="sm" onClick={executeWorkflow} disabled={!nodes.length || executionStatus === "running"}>
            <Play className="mr-2 h-4 w-4" /> {executionStatus === "running" ? "Running..." : "Execute"}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Node Palette */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Node Types</CardTitle>
            <CardDescription>Click to add a node to the pipeline.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-1.5">
            {NODE_TYPES.map((nt) => (
              <button
                key={nt.id}
                className={`w-full text-left rounded-md border px-3 py-2 text-xs font-medium transition-colors hover:brightness-110 ${nt.color}`}
                onClick={() => addNode(nt.id)}
              >
                <div className="flex items-center gap-2">
                  <Plus className="h-3 w-3" />
                  {nt.label}
                </div>
              </button>
            ))}
          </CardContent>
        </Card>

        {/* Pipeline Canvas */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <Input
                  value={workflowName}
                  onChange={(e) => setWorkflowName(e.target.value)}
                  className="text-base font-bold border-none shadow-none p-0 h-auto focus-visible:ring-0"
                />
                <CardDescription className="mt-1">{nodes.length} nodes in pipeline</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Input value={symbol} onChange={(e) => setSymbol(e.target.value)} className="w-20 h-8 text-xs" placeholder="Symbol" />
                <Badge variant="outline">{nodes.length} steps</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {nodes.length === 0 ? (
              <div className="flex h-64 items-center justify-center rounded-md border-2 border-dashed border-border text-sm text-muted">
                Add nodes from the palette to build your workflow
              </div>
            ) : (
              <div className="space-y-2">
                {nodes.map((node, i) => {
                  const nodeType = NODE_TYPES.find((n) => n.id === node.type);
                  return (
                    <div key={node.id} className="group">
                      <div className={`flex items-center gap-2 rounded-lg border px-3 py-2.5 transition-all hover:shadow-sm ${nodeType?.color || "border-border"}`}>
                        <GripVertical className="h-4 w-4 opacity-30" />
                        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-foreground/10 text-xs font-bold">
                          {i + 1}
                        </div>
                        <div className="flex-1">
                          <div className="text-xs font-semibold">{node.label}</div>
                          <div className="text-[10px] opacity-60">{node.type}</div>
                        </div>
                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => moveNode(i, "up")} className="rounded p-0.5 hover:bg-foreground/10 text-[10px]">↑</button>
                          <button onClick={() => moveNode(i, "down")} className="rounded p-0.5 hover:bg-foreground/10 text-[10px]">↓</button>
                          <button onClick={() => removeNode(node.id)} className="rounded p-0.5 hover:bg-red-500/20">
                            <Trash2 className="h-3 w-3 text-red-400" />
                          </button>
                        </div>
                      </div>
                      {i < nodes.length - 1 && (
                        <div className="flex justify-center py-0.5">
                          <ChevronRight className="h-3 w-3 rotate-90 text-muted" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Execution & Presets */}
        <div className="space-y-4 lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Presets</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {PRESET_WORKFLOWS.map((pw) => (
                <button
                  key={pw.id}
                  className={`w-full text-left rounded-md border px-3 py-2 text-xs transition-colors ${
                    selectedPreset === pw.id ? "border-accent bg-accent/10" : "hover:bg-secondary"
                  }`}
                  onClick={() => loadPreset(pw.id)}
                >
                  <div className="font-semibold">{pw.name}</div>
                  <div className="text-[10px] text-muted mt-0.5">{pw.desc}</div>
                </button>
              ))}
            </CardContent>
          </Card>

          {executionStatus && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Execution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Badge variant={executionStatus === "completed" ? "secondary" : "outline"}>
                    {executionStatus === "running" ? "Running..." : "Completed"}
                  </Badge>
                  <p className="text-[11px] text-muted">
                    {executionStatus === "running"
                      ? "Processing workflow nodes..."
                      : "Workflow completed. Check results in the Research Center."}
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Export</CardTitle>
            </CardHeader>
            <CardContent>
              <Button variant="outline" size="sm" className="w-full" onClick={() => {
                const dag = { name: workflowName, nodes: nodes.map((n) => ({ type: n.type, label: n.label })) };
                navigator.clipboard.writeText(JSON.stringify(dag, null, 2));
              }}>
                <Download className="mr-2 h-3 w-3" /> Copy DAG JSON
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
