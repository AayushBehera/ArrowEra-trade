"use client";

import { useState } from "react";
import { Code, Play, Copy, FileCode, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@arrowera/ui";
import { Button } from "@arrowera/ui";
import { Badge } from "@arrowera/ui";

const TEMPLATES = [
  {
    name: "SMA Crossover",
    code: `def sma_crossover_strategy(data):\n    """SMA crossover strategy.\n    Buy when fast SMA crosses above slow SMA.\n    Sell when fast SMA crosses below slow SMA.\n    """\n    fast_period = 10\n    slow_period = 30\n    \n    closes = [bar['close'] for bar in data]\n    \n    fast_sma = sum(closes[-fast_period:]) / fast_period\n    slow_sma = sum(closes[-slow_period:]) / slow_period\n    \n    if fast_sma > slow_sma:\n        return "BUY"\n    elif fast_sma < slow_sma:\n        return "SELL"\n    return "HOLD"`,
  },
  {
    name: "RSI Mean Reversion",
    code: `def rsi_mean_reversion(data):\n    """Buy when RSI is oversold, sell when overbought."""\n    period = 14\n    closes = [bar['close'] for bar in data]\n    \n    gains = []\n    losses = []\n    for i in range(1, min(period + 1, len(closes))):\n        change = closes[-i] - closes[-i-1]\n        if change > 0:\n            gains.append(change)\n        else:\n            losses.append(abs(change))\n    \n    avg_gain = sum(gains) / period if gains else 0\n    avg_loss = sum(losses) / period if losses else 0.001\n    \n    rs = avg_gain / avg_loss\n    rsi = 100 - (100 / (1 + rs))\n    \n    if rsi < 30:\n        return "BUY"\n    elif rsi > 70:\n        return "SELL"\n    return "HOLD"`,
  },
  {
    name: "Bollinger Band Squeeze",
    code: `def bollinger_squeeze(data):\n    """Trade Bollinger Band squeeze breakouts."""\n    period = 20\n    closes = [bar['close'] for bar in data][-period:]\n    \n    mean = sum(closes) / len(closes)\n    std = (sum((c - mean) ** 2 for c in closes) / len(closes)) ** 0.5\n    \n    upper = mean + 2 * std\n    lower = mean - 2 * std\n    current = closes[-1]\n    \n    bandwidth = (upper - lower) / mean\n    \n    if bandwidth < 0.05 and current > mean:\n        return "BUY"\n    elif bandwidth < 0.05 and current < mean:\n        return "SELL"\n    return "HOLD"`,
  },
];

export default function IDEPage() {
  const [code, setCode] = useState(TEMPLATES[0].code);
  const [output, setOutput] = useState("");
  const [running, setRunning] = useState(false);

  const runCode = () => {
    setRunning(true);
    setOutput("Executing strategy...\n");
    // Simulate execution (in production, sends to backend sandbox)
    setTimeout(() => {
      setOutput((prev) =>
        prev +
        "Strategy loaded successfully.\n" +
        "Fetching historical data for AAPL (365 days)...\n" +
        "Running backtest...\n" +
        "Completed: 12 trades, 66.7% win rate, +14.2% return\n" +
        "Sharpe Ratio: 1.24, Max Drawdown: -8.3%"
      );
      setRunning(false);
    }, 1500);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Strategy IDE</h1>
          <p className="text-sm text-muted">Write, test, and deploy trading strategies.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => navigator.clipboard.writeText(code)}>
            <Copy className="mr-2 h-4 w-4" /> Copy
          </Button>
          <Button size="sm" onClick={runCode} disabled={running}>
            {running ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Running...</>
            ) : (
              <><Play className="mr-2 h-4 w-4" /> Run</>
            )}
          </Button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-4">
        {/* Templates Sidebar */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Templates</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {TEMPLATES.map((t) => (
              <button
                key={t.name}
                className="w-full text-left rounded-md border border-border px-3 py-2 text-sm hover:bg-secondary transition-colors"
                onClick={() => setCode(t.code)}
              >
                <div className="flex items-center gap-2">
                  <FileCode className="h-3 w-3 text-muted" />
                  <span className="font-medium">{t.name}</span>
                </div>
              </button>
            ))}
          </CardContent>
        </Card>

        {/* Editor */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Editor</CardTitle>
              <Badge variant="outline">Python</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <textarea
              className="w-full h-[400px] rounded-md border border-input bg-card font-mono text-xs p-4 focus:outline-none focus:ring-1 focus:ring-ring resize-none"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              spellCheck={false}
            />
          </CardContent>
        </Card>

        {/* Output */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Output</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[400px] overflow-y-auto rounded-md border border-input bg-card font-mono text-xs p-4">
              {output ? (
                <pre className="whitespace-pre-wrap text-green">{output}</pre>
              ) : (
                <p className="text-muted">Run your strategy to see output here.</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
