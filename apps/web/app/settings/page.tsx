"use client";

import { useState } from "react";
import { Settings, Moon, Sun, Monitor, Key, User, Shield, Bell } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@arrowera/ui";
import { Button } from "@arrowera/ui";
import { Input } from "@arrowera/ui";
import { Badge } from "@arrowera/ui";
import { Separator } from "@arrowera/ui";
import { useTheme } from "next-themes";
import { useAuthStore } from "../../stores/auth-store";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [apiUrl, setApiUrl] = useState(process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-muted">Configure your ArrowEra Trade experience.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Appearance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" /> Appearance
            </CardTitle>
            <CardDescription>Customize the look and feel</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Theme</label>
              <div className="flex gap-2">
                {[
                  { id: "light", icon: Sun, label: "Light" },
                  { id: "dark", icon: Moon, label: "Dark" },
                  { id: "system", icon: Monitor, label: "System" },
                ].map(({ id, icon: Icon, label }) => (
                  <Button
                    key={id}
                    variant={theme === id ? "default" : "outline"}
                    size="sm"
                    onClick={() => setTheme(id)}
                  >
                    <Icon className="mr-2 h-4 w-4" />
                    {label}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Account */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" /> Account
            </CardTitle>
            <CardDescription>Manage your account settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isAuthenticated && user ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{user.email}</p>
                    <Badge variant="secondary" className="mt-1">{user.role}</Badge>
                  </div>
                  <Button variant="outline" size="sm" onClick={logout}>Sign Out</Button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-muted">Not signed in. Connect to the API to authenticate.</p>
                <div>
                  <label className="text-sm font-medium mb-1 block">API URL</label>
                  <Input value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} />
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* API Configuration */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" /> API Configuration
            </CardTitle>
            <CardDescription>Backend connection settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-1 block">API Base URL</label>
              <Input value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} />
            </div>
            <Separator />
            <div className="text-sm text-muted space-y-1">
              <p>WebSocket connections:</p>
              <p className="font-mono text-xs">{apiUrl.replace("http", "ws")}/ws/market</p>
              <p className="font-mono text-xs">{apiUrl.replace("http", "ws")}/ws/copilot</p>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" /> Notifications
            </CardTitle>
            <CardDescription>Alert preferences</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {["Signal alerts", "Research report ready", "Backtest completed", "Price alerts"].map((item) => (
              <div key={item} className="flex items-center justify-between">
                <span className="text-sm">{item}</span>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">Email</Badge>
                  <Badge variant="outline">In-App</Badge>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
