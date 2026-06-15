"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Zap, RefreshCw, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@arrowera/ui";
import { Badge } from "@arrowera/ui";
import { Button } from "@arrowera/ui";
import { Input } from "@arrowera/ui";
import { Skeleton } from "@arrowera/ui";
import { api } from "../../lib/api";

export default function SignalsPage() {
  const queryClient = useQueryClient();
  const [symbol, setSymbol] = useState("AAPL");

  const { data: signals, isLoading } = useQuery({
    queryKey: ["signals", "active"],
    queryFn: () => api.getSignals("active"),
    retry: 1,
  });

  const generateMutation = useMutation({
    mutationFn: (sym: string) =>
      fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/signals/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol: sym }),
      }).then((r) => r.json()),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["signals"] }),
  });

  const signalIcon = (type: string) => {
    switch (type?.toUpperCase()) {
      case "BUY": return <TrendingUp className="h-4 w-4 text-green" />;
      case "SELL": return <TrendingDown className="h-4 w-4 text-red" />;
      default: return <Minus className="h-4 w-4 text-muted" />;
    }
  };

  const signalVariant = (type: string): "success" | "destructive" | "outline" => {
    switch (type?.toUpperCase()) {
      case "BUY": return "success";
      case "SELL": return "destructive";
      default: return "outline";
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Signals</h1>
        <p className="text-sm text-muted">AI-generated trading signals from technical and fundamental analysis.</p>
      </div>

      {/* Generate Signal */}
      <Card>
        <CardHeader>
          <CardTitle>Generate Signal</CardTitle>
          <CardDescription>Run signal analysis on any symbol</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3 items-end">
            <div className="flex-1 max-w-xs">
              <label className="text-sm font-medium mb-1 block">Symbol</label>
              <Input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} placeholder="AAPL" />
            </div>
            <Button
              onClick={() => generateMutation.mutate(symbol)}
              disabled={generateMutation.isPending || !symbol}
            >
              {generateMutation.isPending ? (
                <><RefreshCw className="mr-2 h-4 w-4 animate-spin" /> Analyzing...</>
              ) : (
                <><Zap className="mr-2 h-4 w-4" /> Generate Signal</>
              )}
            </Button>
          </div>
          {generateMutation.isSuccess && generateMutation.data && (
            <div className="mt-4 rounded-md border border-border p-4">
              <div className="flex items-center gap-3">
                {signalIcon(generateMutation.data.signalType)}
                <div>
                  <p className="font-semibold">{generateMutation.data.symbol} — {generateMutation.data.signalType}</p>
                  <p className="text-sm text-muted">
                    Confidence: {(parseFloat(generateMutation.data.confidence) * 100).toFixed(1)}%
                  </p>
                  {generateMutation.data.metadata?.reasons && (
                    <p className="text-xs text-muted mt-1">
                      {generateMutation.data.metadata.reasons.join(", ")}
                    </p>
                  )}
                </div>
                <Badge variant={signalVariant(generateMutation.data.signalType)} className="ml-auto">
                  {generateMutation.data.signalType}
                </Badge>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Active Signals */}
      <Card>
        <CardHeader>
          <CardTitle>Active Signals</CardTitle>
          <CardDescription>{signals?.length ?? 0} active signals</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : signals && signals.length > 0 ? (
            <div className="space-y-3">
              {signals.map((sig) => (
                <div key={sig.id} className="flex items-center gap-3 rounded-md border border-border p-4">
                  {signalIcon(sig.signalType)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold">{sig.symbol}</span>
                      <Badge variant={signalVariant(sig.signalType)}>{sig.signalType}</Badge>
                    </div>
                    <p className="text-sm text-muted mt-1">
                      Confidence: {(parseFloat(sig.confidence) * 100).toFixed(1)}%
                      {sig.createdAt && ` · ${new Date(sig.createdAt).toLocaleDateString()}`}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted text-center py-8">No active signals. Generate one above.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
