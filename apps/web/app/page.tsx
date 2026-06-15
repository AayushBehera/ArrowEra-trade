"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { TrendingUp, TrendingDown, DollarSign, Activity, Zap, Bot } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@arrowera/ui";
import { Badge } from "@arrowera/ui";
import { Skeleton } from "@arrowera/ui";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@arrowera/ui";
import { api } from "../lib/api";
import { formatCurrency } from "../lib/utils";
import { useMarketStore } from "../stores/market-store";

const trend = [
  { t: "Jan", v: 100 }, { t: "Feb", v: 104 }, { t: "Mar", v: 102 }, { t: "Apr", v: 109 },
  { t: "May", v: 112 }, { t: "Jun", v: 110 }, { t: "Jul", v: 119 }, { t: "Aug", v: 124 },
];

function MetricCard({ icon: Icon, label, value, change }: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  change?: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardDescription>{label}</CardDescription>
        <Icon className="h-4 w-4 text-muted" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change && (
          <p className="text-xs text-muted mt-1">
            <span className={change.startsWith("+") ? "text-green" : "text-red"}>{change}</span> from last period
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.dashboard(),
    retry: 1,
  });

  const watchlist = useMarketStore((s) => s.watchlist);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted">Market intelligence at a glance.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          icon={DollarSign}
          label="Portfolio Value"
          value={data?.portfolioValue ?? "—"}
          change="+12.4%"
        />
        <MetricCard
          icon={Activity}
          label="Cash Balance"
          value={data?.cashBalance ?? "—"}
        />
        <MetricCard
          icon={Zap}
          label="Active Signals"
          value={data ? String(data.activeSignals) : "—"}
        />
        <MetricCard
          icon={Bot}
          label="Agent Runs"
          value={data ? String(data.agentRuns) : "—"}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-7">
        {/* Portfolio Chart */}
        <Card className="lg:col-span-4">
          <CardHeader>
            <CardTitle>Portfolio Trajectory</CardTitle>
            <CardDescription>Capital curve over the last 8 months</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trend}>
                  <defs>
                    <linearGradient id="colorV" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--color-signal)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="var(--color-signal)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="t" tickLine={false} axisLine={false} fontSize={12} />
                  <YAxis tickLine={false} axisLine={false} fontSize={12} />
                  <Tooltip />
                  <Area type="monotone" dataKey="v" stroke="var(--color-signal)" fill="url(#colorV)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Watchlist */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Watchlist</CardTitle>
            <CardDescription>{watchlist.length} symbols tracked</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {watchlist.slice(0, 8).map((sym) => (
                <div key={sym} className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                  <span className="font-mono text-sm font-semibold">{sym}</span>
                  <Badge variant="outline">Track</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Positions Table */}
      <Card>
        <CardHeader>
          <CardTitle>Open Positions</CardTitle>
          <CardDescription>Current portfolio holdings and P&L</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : error ? (
            <p className="text-sm text-destructive">Failed to load positions. Is the API running?</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Quantity</TableHead>
                  <TableHead>Market Value</TableHead>
                  <TableHead>P&L</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.positions && data.positions.length > 0 ? (
                  data.positions.map((pos) => (
                    <TableRow key={pos.symbol}>
                      <TableCell className="font-mono font-semibold">{pos.symbol}</TableCell>
                      <TableCell>{pos.quantity}</TableCell>
                      <TableCell>{pos.marketValue}</TableCell>
                      <TableCell className="text-green">{pos.pnl}</TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted">
                      No positions recorded yet.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
