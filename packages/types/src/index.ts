export type HealthResponse = {
  status: "healthy" | "degraded";
  database: "up" | "down";
  version: string;
};

export type ContactSubmission = {
  name: string;
  email: string;
  company: string;
  phone?: string;
  message: string;
};

export type DashboardSummary = {
  portfolioValue: string;
  cashBalance: string;
  activeSignals: number;
  agentRuns: number;
  positions: Array<{
    symbol: string;
    quantity: string;
    marketValue: string;
    pnl: string;
  }>;
};

export type AgentRequest = {
  prompt: string;
  provider?: "openai" | "anthropic" | "gemini" | "deepseek" | "ollama";
};

export type AgentResponse = {
  runId: string;
  provider: string;
  model: string;
  content: string;
  durationMs: number;
};

export type MarketQuote = {
  symbol: string;
  price: string;
  change: string;
  changePercent: string;
  volume: string;
  high: string;
  low: string;
  open: string;
  previousClose: string;
  assetType: string;
};

export type OHLCVBar = {
  symbol: string;
  timestamp: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
  adjustedClose: string;
};

export type HistoricalData = {
  symbol: string;
  timeframe: string;
  bars: number;
  data: OHLCVBar[];
};

export type IndicatorResult = {
  symbol: string;
  bars: number;
  sma_20: number | null;
  sma_50: number | null;
  sma_200: number | null;
  ema_12: number;
  ema_26: number;
  rsi_14: number;
  macd: number;
  macd_signal: number;
  macd_histogram: number;
  bb_upper: number;
  bb_middle: number;
  bb_lower: number;
  atr_14: number;
  vwap: number;
};

export type BacktestRequest = {
  symbol: string;
  strategyName?: string;
  initialCapital?: number;
  days?: number;
  params?: Record<string, unknown>;
};

export type BacktestTrade = {
  entryDate: string;
  exitDate: string;
  direction: string;
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  pnl: number;
  pnlPercent: number;
};

export type BacktestResult = {
  runId?: string;
  initialCapital: number;
  finalCapital: number;
  totalReturn: number;
  totalReturnPercent: number;
  sharpeRatio: number;
  maxDrawdown: number;
  maxDrawdownPercent: number;
  winRate: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  avgWin: number;
  avgLoss: number;
  profitFactor: number;
  trades: BacktestTrade[];
};

export type Signal = {
  id: string;
  symbol: string;
  signalType: string;
  confidence: string;
  status: string;
  metadata: Record<string, unknown>;
  createdAt: string;
};

export type ResearchRequest = {
  symbol?: string;
  question?: string;
  provider?: string;
  context?: Record<string, unknown>;
};

export type ResearchResult = {
  agent: string;
  provider?: string;
  model?: string;
  content: string;
  durationMs?: number;
  confidence: number;
};

export type ResearchReport = {
  analyses: Record<string, ResearchResult>;
  synthesis: string;
  synthesisProvider?: string;
  synthesisModel?: string;
  totalDurationMs: number;
};

export type AuthToken = {
  accessToken: string;
  tokenType: string;
  userId: string;
  email: string;
  role: string;
};
