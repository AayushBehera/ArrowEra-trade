import { create } from "zustand";

interface PortfolioPosition {
  symbol: string;
  quantity: number;
  averageCost: number;
  currentPrice: number;
  marketValue: number;
  pnl: number;
  pnlPercent: number;
}

interface PortfolioState {
  positions: PortfolioPosition[];
  totalValue: number;
  cashBalance: number;
  totalPnl: number;
  setPositions: (positions: PortfolioPosition[]) => void;
  setTotalValue: (value: number) => void;
  setCashBalance: (balance: number) => void;
}

export const usePortfolioStore = create<PortfolioState>((set) => ({
  positions: [],
  totalValue: 0,
  cashBalance: 0,
  totalPnl: 0,
  setPositions: (positions) =>
    set({
      positions,
      totalPnl: positions.reduce((acc, p) => acc + p.pnl, 0),
    }),
  setTotalValue: (totalValue) => set({ totalValue }),
  setCashBalance: (cashBalance) => set({ cashBalance }),
}));
