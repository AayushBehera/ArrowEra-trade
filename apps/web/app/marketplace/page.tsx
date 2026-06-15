"use client";

import { useState } from "react";
import { Store, Search, Star, Download, Upload } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@arrowera/ui";
import { Button } from "@arrowera/ui";
import { Input } from "@arrowera/ui";
import { Badge } from "@arrowera/ui";

const SAMPLE_STRATEGIES = [
  { id: "1", name: "SMA Crossover Pro", author: "ArrowEra", category: "Trend", rating: 4.5, downloads: 1234, desc: "Enhanced SMA crossover with volume confirmation and risk management." },
  { id: "2", name: "RSI Divergence Scanner", author: "QuantLab", category: "Mean Reversion", rating: 4.2, downloads: 876, desc: "Detects RSI divergence patterns for early trend reversal signals." },
  { id: "3", name: "Bollinger Squeeze Breakout", author: "AlphaTrader", category: "Volatility", rating: 4.8, downloads: 2345, desc: "Trades volatility squeeze breakouts using Bollinger Bands width." },
  { id: "4", name: "MACD Histogram Reversal", author: "SignalPro", category: "Momentum", rating: 3.9, downloads: 567, desc: "Catches momentum shifts using MACD histogram direction changes." },
  { id: "5", name: "Multi-Timeframe Trend", author: "ArrowEra", category: "Trend", rating: 4.6, downloads: 1890, desc: "Confirms trends across daily, weekly, and monthly timeframes." },
  { id: "6", name: "VWAP Mean Reversion", author: "DayTradeAI", category: "Intraday", rating: 4.1, downloads: 743, desc: "Intraday mean reversion around VWAP for liquid equities." },
];

export default function MarketplacePage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");

  const categories = ["All", "Trend", "Mean Reversion", "Volatility", "Momentum", "Intraday"];

  const filtered = SAMPLE_STRATEGIES.filter((s) => {
    const matchSearch = s.name.toLowerCase().includes(search.toLowerCase()) || s.desc.toLowerCase().includes(search.toLowerCase());
    const matchCategory = category === "All" || s.category === category;
    return matchSearch && matchCategory;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Marketplace</h1>
          <p className="text-sm text-muted">Browse and share trading strategies and workflows.</p>
        </div>
        <Button size="sm">
          <Upload className="mr-2 h-4 w-4" /> Publish Strategy
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 items-center flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <Input placeholder="Search strategies..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        <div className="flex gap-1 flex-wrap">
          {categories.map((cat) => (
            <Button
              key={cat}
              variant={category === cat ? "default" : "outline"}
              size="sm"
              onClick={() => setCategory(cat)}
            >
              {cat}
            </Button>
          ))}
        </div>
      </div>

      {/* Strategies Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((strategy) => (
          <Card key={strategy.id} className="flex flex-col">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{strategy.name}</CardTitle>
                <Badge variant="outline">{strategy.category}</Badge>
              </div>
              <CardDescription>by {strategy.author}</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <p className="text-sm text-muted flex-1 mb-4">{strategy.desc}</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 text-xs text-muted">
                  <span className="flex items-center gap-1">
                    <Star className="h-3 w-3 text-signal fill-signal" />
                    {strategy.rating}
                  </span>
                  <span className="flex items-center gap-1">
                    <Download className="h-3 w-3" />
                    {strategy.downloads.toLocaleString()}
                  </span>
                </div>
                <Button variant="outline" size="sm">Use</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12 text-muted">
          <Store className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>No strategies found matching your criteria.</p>
        </div>
      )}
    </div>
  );
}
