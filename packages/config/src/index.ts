export const appConfig = {
  name: "ArrowEra Trade",
  shortName: "AE",
  version: "0.2.0",
  navigation: [
    { href: "/", label: "Dashboard", icon: "LayoutDashboard" },
    { href: "/markets", label: "Markets", icon: "TrendingUp" },
    { href: "/portfolio", label: "Portfolio", icon: "Briefcase" },
    { href: "/signals", label: "Signals", icon: "Zap" },
    { href: "/research", label: "Research", icon: "Microscope" },
    { href: "/backtest", label: "Backtest", icon: "FlaskConical" },
    { href: "/copilot", label: "Copilot", icon: "MessageSquare" },
    { href: "/agents", label: "Agents", icon: "Bot" },
    { href: "/workflows", label: "Workflows", icon: "GitBranch" },
    { href: "/ide", label: "Strategy IDE", icon: "Code" },
    { href: "/marketplace", label: "Marketplace", icon: "Store" },
    { href: "/settings", label: "Settings", icon: "Settings" }
  ]
} as const;

export type NavItem = (typeof appConfig.navigation)[number];
