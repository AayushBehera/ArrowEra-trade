"use client";

import { useState, useRef, useEffect } from "react";
import { MessageSquare, Send, Loader2, Wrench, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@arrowera/ui";
import { Button } from "@arrowera/ui";
import { Input } from "@arrowera/ui";
import { Badge } from "@arrowera/ui";
import { useAgentStore } from "../../stores/agent-store";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolCalls?: Array<{ name: string; args: Record<string, unknown> }>;
}

export default function CopilotPage() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, addMessage, clearMessages } = useAgentStore();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };
    addMessage(userMsg);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/copilot/chat`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: input }),
        }
      );
      const data = await response.json();
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.content ?? "No response.",
        toolCalls: data.tool_calls,
      };
      addMessage(assistantMsg);
    } catch (err) {
      addMessage({
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Error: ${(err as Error).message}. Is the API running?`,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">AI Copilot</h1>
          <p className="text-sm text-muted">Your AI-powered trading assistant.</p>
        </div>
        <Button variant="ghost" size="sm" onClick={clearMessages}>
          <Trash2 className="mr-2 h-4 w-4" /> Clear
        </Button>
      </div>

      {/* Chat Area */}
      <Card className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-muted gap-3">
              <MessageSquare className="h-12 w-12 opacity-30" />
              <p className="text-sm">Ask me anything about markets, portfolio, or strategy.</p>
              <div className="flex gap-2 flex-wrap justify-center">
                {["What's the outlook for AAPL?", "Analyze my portfolio risk", "Compare SPY vs QQQ"].map((q) => (
                  <button
                    key={q}
                    className="rounded-full border border-border px-3 py-1.5 text-xs hover:bg-secondary transition-colors"
                    onClick={() => setInput(q)}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
          {(messages as unknown as ChatMessage[]).map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 text-sm ${
                  msg.role === "user"
                    ? "bg-accent text-accent-foreground"
                    : "bg-secondary text-foreground"
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="mt-2 space-y-1 border-t border-border/50 pt-2">
                    {msg.toolCalls.map((tc, i) => (
                      <div key={i} className="flex items-center gap-1 text-xs opacity-70">
                        <Wrench className="h-3 w-3" />
                        <span className="font-mono">{tc.name}</span>
                        <span>({JSON.stringify(tc.args)})</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-secondary rounded-lg px-4 py-3">
                <Loader2 className="h-4 w-4 animate-spin text-muted" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-border p-4">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about markets, portfolio, strategy..."
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              disabled={loading}
            />
            <Button onClick={sendMessage} disabled={loading || !input.trim()} size="icon">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
