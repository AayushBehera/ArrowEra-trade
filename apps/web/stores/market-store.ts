import { create } from "zustand";

interface MarketQuote {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  previousClose: number;
}

interface MarketState {
  watchlist: string[];
  quotes: Record<string, MarketQuote>;
  selectedSymbol: string | null;
  addToWatchlist: (symbol: string) => void;
  removeFromWatchlist: (symbol: string) => void;
  setQuote: (symbol: string, quote: MarketQuote) => void;
  setQuotes: (quotes: Record<string, MarketQuote>) => void;
  setSelectedSymbol: (symbol: string | null) => void;
}

export const useMarketStore = create<MarketState>((set) => ({
  watchlist: ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "SPY"],
  quotes: {},
  selectedSymbol: null,
  addToWatchlist: (symbol) =>
    set((state) => ({
      watchlist: state.watchlist.includes(symbol)
        ? state.watchlist
        : [...state.watchlist, symbol],
    })),
  removeFromWatchlist: (symbol) =>
    set((state) => ({
      watchlist: state.watchlist.filter((s) => s !== symbol),
    })),
  setQuote: (symbol, quote) =>
    set((state) => ({ quotes: { ...state.quotes, [symbol]: quote } })),
  setQuotes: (quotes) => set((state) => ({ quotes: { ...state.quotes, ...quotes } })),
  setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
}));
