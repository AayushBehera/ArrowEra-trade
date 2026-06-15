"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { TrendingUp, TrendingDown, Search, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@arrowera/ui";
import { Badge } from "@arrowera/ui";
import { Input } from "@arrowera/ui";
import { Button } from "@arrowera/ui";
import { Skeleton } from "@arrowera/ui";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@arrowera/ui";
import { api } from "../../lib/api";
import { formatCurrency, formatPercent } from "../../lib/utils";
import { useMarketStore } from "../../stores/market-store";

export default function MarketsPage() {
  const [search, setSearch] = useState("");
  const watchlist = useMarketStore((s) => s.watchlist);
  const addToWatchlist = useMarketStore((s) => s.addToWatchlist);

  const symbols = "AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA,SPY,QQQ,IWM";

  const { data: overview, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["market-overview", symbols],
    queryFn: () => api.getMarketOverview(symbols.split(",")),
    retry: 1,
    refetchInterval: 60000,
  });

  const filteredSymbols = symbols.split(",").filter((s) =>
    s.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Markets</h1>
          <p className="text-sm text-muted">Real-time market data and watchlist tracking.</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
        <Input
          placeholder="Filter symbols..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Market Overview Grid */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {Array.from({ length: 10 }).map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-5 w-16" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-24 mb-2" />
                <Skeleton className="h-4 w-20" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {filteredSymbols.map((sym) => {
            const quote = overview?.[sym];
            const isPositive = quote ? parseFloat(quote.changePercent) >= 0 : true;
            const isWatched = watchlist.includes(sym);
            return (
              <Card key={sym} className="relative">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <span className="font-mono text-sm font-bold">{sym}</span>
                  <Button
                    variant={isWatched ? "default" : "ghost"}
                    size="sm"
                    className="h-6 px-2 text-xs"
                    onClick={() => addToWatchlist(sym)}
                  >
                    {isWatched ? "Watching" : "Add"}
                  </Button>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {quote ? `$${parseFloat(quote.price).toFixed(2)}` : "—"}
                  </div>
                  <div className={`flex items-center gap-1 text-sm ${isPositive ? "text-green" : "text-red"}`}>
                    {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    <span>{quote ? `${parseFloat(quote.changePercent).toFixed(2)}%` : "N/A"}</span>
                  </div>
                  {quote && (
                    <p className="mt-1 text-xs text-muted">
                      Vol: {parseInt(quote.volume).toLocaleString()}
                    </p>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Detailed Table */}
      <Card>
        <CardHeader>
          <CardTitle>Market Data Table</CardTitle>
          <CardDescription>Detailed quote information</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Symbol</TableHead>
                <TableHead>Price</TableHead>
                <TableHead>Change</TableHead>
                <TableHead>% Change</TableHead>
                <TableHead>High</TableHead>
                <TableHead>Low</TableHead>
                <TableHead>Volume</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredSymbols.map((sym) => {
                const q = overview?.[sym];
                if (!q) {
                  return (
                    <TableRow key={sym}>
                      <TableCell className="font-mono font-semibold">{sym}</TableCell>
                      <TableCell colSpan={6} className="text-muted">No data</TableCell>
                    </TableRow>
                  );
                }
                const isPos = parseFloat(q.changePercent) >= 0;
                return (
                  <TableRow key={sym}>
                    <TableCell className="font-mono font-semibold">{sym}</TableCell>
                    <TableCell>${parseFloat(q.price).toFixed(2)}</TableCell>
                    <TableCell className={isPos ? "text-green" : "text-red"}>
                      {parseFloat(q.change).toFixed(2)}
                    </TableCell>
                    <TableCell className={isPos ? "text-green" : "text-red"}>
                      {parseFloat(q.changePercent).toFixed(2)}%
                    </TableCell>
                    <TableCell>${parseFloat(q.high).toFixed(2)}</TableCell>
                    <TableCell>${parseFloat(q.low).toFixed(2)}</TableCell>
                    <TableCell>{parseInt(q.volume).toLocaleString()}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
