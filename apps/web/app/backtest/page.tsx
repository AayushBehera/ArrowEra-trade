"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { FlaskConical, Play, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@arrowera/ui";
import { Button } from "@arrowera/ui";
import { Input } from "@arrowera/ui";
import { Badge } from "@arrowera/ui";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@arrowera/ui";
import { api } from "../../lib/api";

export default function BacktestPage() {
  const [symbol, setSymbol] = useState("AAPL");
  const [days, setDays] = useState("365");
  const [capital, setCapital] = useState("100000");
  const [fast, setFast] = useState("10");
  const [slow, setSlow] = useState("30");

  const mutation = useMutation({
    mutationFn: () =>
      api.runBacktest({
        symbol,
        days: parseInt(days),
        initialCapital: parseFloat(capital),
        params: { fast: parseInt(fast), slow: parseInt(slow) },
      }),
  });

  const result = mutation.data;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Backtesting Lab</h1>
        <p className="text-sm text-muted">Test trading strategies against historical data.</p>
      </div>

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Strategy Configuration</CardTitle>
          <CardDescription>SMA Crossover Strategy Parameters</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-5">
            <div>
              <label className="text-sm font-medium mb-1 block">Symbol</label>
              <Input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Days</label>
              <Input type="number" value={days} onChange={(e) => setDays(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Initial Capital</label>
              <Input type="number" value={capital} onChange={(e) => setCapital(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Fast SMA</label>
              <Input type="number" value={fast} onChange={(e) => setFast(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Slow SMA</label>
              <Input type="number" value={slow} onChange={(e) => setSlow(e.target.value)} />
            </div>
          </div>
          <Button
            className="mt-4"
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !symbol}
          >
            {mutation.isPending ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Running Backtest...</>
            ) : (
              <><Play className="mr-2 h-4 w-4" /> Run Backtest</>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <>
          {/* Metrics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Total Return</CardDescription>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${(result.totalReturnPercent ?? 0) >= 0 ? "text-green" : "text-red"}`}>
                  {((result.totalReturnPercent ?? 0) * 100).toFixed(2)}%
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Sharpe Ratio</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{(result.sharpeRatio ?? 0).toFixed(3)}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Max Drawdown</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red">{((result.maxDrawdownPercent ?? 0) * 100).toFixed(2)}%</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Win Rate</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{((result.winRate ?? 0) * 100).toFixed(1)}%</div>
              </CardContent>
            </Card>
          </div>

          {/* Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Backtest Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 md:grid-cols-3 text-sm">
                <div>Initial: ${result.initialCapital?.toLocaleString()}</div>
                <div>Final: ${result.finalCapital?.toLocaleString()}</div>
                <div>Total Trades: {result.totalTrades}</div>
                <div>Winning: {result.winningTrades}</div>
                <div>Losing: {result.losingTrades}</div>
                <div>Profit Factor: {result.profitFactor?.toFixed(2)}</div>
              </div>
            </CardContent>
          </Card>

          {/* Trade Log */}
          {result.trades && result.trades.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Trade Log</CardTitle>
                <CardDescription>{result.trades.length} trades executed</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Entry Date</TableHead>
                      <TableHead>Exit Date</TableHead>
                      <TableHead>Direction</TableHead>
                      <TableHead>Entry Price</TableHead>
                      <TableHead>Exit Price</TableHead>
                      <TableHead>P&L</TableHead>
                      <TableHead>P&L %</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.trades.slice(0, 20).map((trade, i) => (
                      <TableRow key={i}>
                        <TableCell className="text-xs">{trade.entryDate}</TableCell>
                        <TableCell className="text-xs">{trade.exitDate}</TableCell>
                        <TableCell>
                          <Badge variant={trade.direction === "long" ? "success" : "destructive"}>{trade.direction}</Badge>
                        </TableCell>
                        <TableCell>${trade.entryPrice?.toFixed(2)}</TableCell>
                        <TableCell>${trade.exitPrice?.toFixed(2)}</TableCell>
                        <TableCell className={trade.pnl >= 0 ? "text-green" : "text-red"}>
                          ${trade.pnl?.toFixed(2)}
                        </TableCell>
                        <TableCell className={trade.pnlPercent >= 0 ? "text-green" : "text-red"}>
                          {(trade.pnlPercent * 100)?.toFixed(2)}%
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
