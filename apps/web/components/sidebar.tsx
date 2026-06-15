"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { appConfig } from "@arrowera/config";
import {
  LayoutDashboard, TrendingUp, Briefcase, Zap, Microscope,
  FlaskConical, MessageSquare, Bot, GitBranch, Code, Store, Settings,
  ChevronLeft, ChevronRight,
} from "lucide-react";
import { cn } from "../lib/utils";
import { Button } from "./ui/button";
import { Separator } from "./ui/separator";
import { useState } from "react";

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  LayoutDashboard, TrendingUp, Briefcase, Zap, Microscope,
  FlaskConical, MessageSquare, Bot, GitBranch, Code, Store, Settings,
};

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "sticky top-0 flex h-screen flex-col border-r border-sidebar-border bg-sidebar backdrop-blur-xl transition-all duration-300",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Brand */}
      <div className="flex items-center gap-3 px-4 py-6">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent font-mono text-xs font-medium text-white">
          AE
        </span>
        {!collapsed && (
          <div className="overflow-hidden">
            <p className="truncate text-sm font-bold tracking-tight">{appConfig.name}</p>
            <p className="font-mono text-[10px] uppercase tracking-wider text-muted">v{appConfig.version}</p>
          </div>
        )}
      </div>

      <Separator />

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-4" aria-label="Primary">
        {appConfig.navigation.map((item) => {
          const Icon = iconMap[item.icon];
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors",
                isActive
                  ? "bg-primary/10 font-semibold text-foreground"
                  : "text-muted hover:bg-primary/5 hover:text-foreground"
              )}
            >
              {Icon && <Icon className="h-4 w-4 shrink-0" />}
              {!collapsed && <span className="truncate">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      <Separator />

      {/* Footer */}
      <div className="flex items-center justify-between px-3 py-3">
        {!collapsed && (
          <div className="flex items-center gap-2 font-mono text-[10px] text-muted">
            <span className="inline-block h-2 w-2 rounded-full bg-green shadow-[0_0_0_3px_rgba(27,111,74,0.2)]" />
            API monitored
          </div>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={() => setCollapsed(!collapsed)}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>
    </aside>
  );
}
