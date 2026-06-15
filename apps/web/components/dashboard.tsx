"use client";

import { useEffect, useState } from "react";
import { Area, AreaChart, ResponsiveContainer, Tooltip } from "recharts";
import type { DashboardSummary } from "@arrowera/types";
import { Card } from "@arrowera/ui";
import { api } from "../lib/api";

const trend = [
  { value: 100 }, { value: 104 }, { value: 102 }, { value: 109 },
  { value: 112 }, { value: 110 }, { value: 119 }, { value: 124 }
];

export function Dashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.dashboard().then(setData).catch((reason: Error) => setError(reason.message));
  }, []);

  const metrics: Array<[string, string | number]> = [
    ["Portfolio value", data?.portfolioValue ?? "Loading"],
    ["Cash balance", data?.cashBalance ?? "Loading"],
    ["Active signals", data?.activeSignals ?? "Loading"],
    ["Agent runs", data?.agentRuns ?? "Loading"]
  ];

  return (
    <>
      <div className="grid metrics">
        {metrics.map(([label, value]) => <Card key={label}><div className="metric-label">{label}</div><div className="metric-value">{value}</div></Card>)}
      </div>
      {error && <p className="status error">API unavailable: {error}</p>}
      <div className="grid content-grid">
        <Card>
          <div className="eyebrow">Portfolio trajectory</div>
          <h2>Capital curve</h2>
          <div className="chart">
            <ResponsiveContainer>
              <AreaChart data={trend}>
                <defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#ff5c35" stopOpacity=".4"/><stop offset="1" stopColor="#ff5c35" stopOpacity="0"/></linearGradient></defs>
                <Tooltip />
                <Area dataKey="value" stroke="#ff5c35" fill="url(#fill)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card>
          <div className="eyebrow">Open book</div>
          <h2>Positions</h2>
          <table>
            <thead><tr><th>Symbol</th><th>Qty</th><th>Value</th><th>P&amp;L</th></tr></thead>
            <tbody>
              {data?.positions.length ? data.positions.map((position) => (
                <tr key={position.symbol}><td>{position.symbol}</td><td>{position.quantity}</td><td>{position.marketValue}</td><td className="positive">{position.pnl}</td></tr>
              )) : <tr><td colSpan={4}>No positions recorded.</td></tr>}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  );
}
