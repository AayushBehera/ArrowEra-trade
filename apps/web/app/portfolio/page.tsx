"use client";

import { useQuery } from "@tanstack/react-query";
import { DollarSign, TrendingUp, PieChart, BarChart3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@arrowera/ui";
import { Badge } from "@arrowera/ui";
import { Skeleton } from "@arrowera/ui";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@arrowera/ui";
import { PieChart as RPie, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { api } from "../../lib/api";
import { formatCurrency } from "../../lib/utils";
import { usePortfolioStore } from "../../stores/portfolio-store";

const COLORS = ["#ff5c35", "#1b6f4a", "#2563eb", "#9333ea", "#eab308", "#ec4899"];

export default function PortfolioPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.dashboard(),
    retry: 1,
  });

  const positions = data?.positions ?? [];
  const pieData = positions.map((p) => ({
    name: p.symbol,
    value: parseFloat(p.marketValue.replace(/[$,]/g, "")) || 0,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Portfolio</h1>
        <p className="text-sm text-muted">Capital allocation, positions, and performance.</p>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardDescription>Total Value</CardDescription>
            <DollarSign className="h-4 w-4 text-muted" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.portfolioValue ?? "—"}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardDescription>Cash</CardDescription>
            <DollarSign className="h-4 w-4 text-muted" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.cashBalance ?? "—"}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardDescription>Positions</CardDescription>
            <BarChart3 className="h-4 w-4 text-muted" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{positions.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardDescription>Active Signals</CardDescription>
            <TrendingUp className="h-4 w-4 text-muted" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.activeSignals ?? 0}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        {/* Allocation Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Allocation</CardTitle>
            <CardDescription>Portfolio distribution by position</CardDescription>
          </CardHeader>
          <CardContent>
            {pieData.length > 0 ? (
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <RPie>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} dataKey="value" label={({ name }) => name}>
                      {pieData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => formatCurrency(value)} />
                  </RPie>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="flex h-[300px] items-center justify-center text-sm text-muted">
                No positions to display allocation.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Positions Table */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Positions</CardTitle>
            <CardDescription>Current holdings and unrealized P&L</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Quantity</TableHead>
                    <TableHead>Market Value</TableHead>
                    <TableHead>P&L</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {positions.length > 0 ? (
                    positions.map((pos) => {
                      const pnlVal = parseFloat(pos.pnl.replace(/[$,]/g, ""));
                      return (
                        <TableRow key={pos.symbol}>
                          <TableCell className="font-mono font-semibold">{pos.symbol}</TableCell>
                          <TableCell>{pos.quantity}</TableCell>
                          <TableCell>{pos.marketValue}</TableCell>
                          <TableCell className={pnlVal >= 0 ? "text-green" : "text-red"}>{pos.pnl}</TableCell>
                          <TableCell>
                            <Badge variant={pnlVal >= 0 ? "success" : "destructive"}>
                              {pnlVal >= 0 ? "Profit" : "Loss"}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      );
                    })
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-muted">
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
    </div>
  );
}
