import type {
  AgentRequest,
  AgentResponse,
  AuthToken,
  BacktestRequest,
  BacktestResult,
  ContactSubmission,
  DashboardSummary,
  HealthResponse,
  HistoricalData,
  IndicatorResult,
  MarketQuote,
  ResearchReport,
  ResearchRequest,
  ResearchResult,
  Signal,
} from "@arrowera/types";

export class ArrowEraClient {
  constructor(
    private readonly baseUrl: string,
    private token: string | null = null
  ) {}

  setToken(token: string | null): void {
    this.token = token;
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...((init?.headers as Record<string, string>) || {}),
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    const response = await fetch(`${this.baseUrl}${path}`, { ...init, headers });
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(body.detail ?? "Request failed");
    }
    return response.json() as Promise<T>;
  }

  // Health
  health() {
    return this.request<HealthResponse>("/health");
  }

  // Dashboard
  dashboard() {
    return this.request<DashboardSummary>("/api/v1/dashboard");
  }

  // Contact
  submitContact(payload: ContactSubmission) {
    return this.request<{ id: string; status: "received" }>("/api/v1/contact", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // Market Data
  getQuote(symbol: string) {
    return this.request<MarketQuote>(`/api/v1/market/quote/${encodeURIComponent(symbol)}`);
  }

  getMarketOverview(symbols: string[]) {
    return this.request<Record<string, MarketQuote>>(
      `/api/v1/market/overview?symbols=${symbols.join(",")}`
    );
  }

  getHistorical(symbol: string, days = 365, timeframe = "1d") {
    return this.request<HistoricalData>(
      `/api/v1/market/historical/${encodeURIComponent(symbol)}?days=${days}&timeframe=${timeframe}`
    );
  }

  // Quant
  getIndicators(symbol: string, days = 365) {
    return this.request<IndicatorResult>(
      `/api/v1/quant/indicators/${encodeURIComponent(symbol)}?days=${days}`
    );
  }

  runBacktest(payload: BacktestRequest) {
    return this.request<BacktestResult>("/api/v1/quant/backtest", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // Research
  runAnalyst(agentType: string, payload: ResearchRequest) {
    return this.request<ResearchResult>(`/api/v1/research/analyst/${agentType}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  generateResearchReport(payload: ResearchRequest) {
    return this.request<ResearchReport>("/api/v1/research/report", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // Signals
  getSignals(status = "active") {
    return this.request<Signal[]>(`/api/v1/signals?status=${status}`);
  }

  // Agent (legacy)
  runMarketAnalyst(payload: AgentRequest) {
    return this.request<AgentResponse>("/api/v1/agents/market-analyst", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // Auth
  register(email: string, password: string, displayName = "") {
    return this.request<AuthToken>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, displayName }),
    });
  }

  login(email: string, password: string) {
    return this.request<AuthToken>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }
}
