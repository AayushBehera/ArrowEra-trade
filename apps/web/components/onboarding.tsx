"use client";

import { useState } from "react";
import { Check, ArrowRight, Sparkles, BarChart3, Bot, Shield } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@arrowera/ui";
import { Button } from "@arrowera/ui";
import { Badge } from "@arrowera/ui";

const STEPS = [
  {
    id: "welcome",
    title: "Welcome to ArrowEra Trade",
    description: "Your AI-powered trading intelligence platform. Let's get you set up.",
    icon: Sparkles,
  },
  {
    id: "markets",
    title: "Explore Markets",
    description: "Get real-time quotes, historical data, and market overview from multiple sources.",
    icon: BarChart3,
  },
  {
    id: "agents",
    title: "Meet Your AI Agents",
    description: "5 specialist analysts: Market, Technical, Fundamental, Macro, and Sentiment.",
    icon: Bot,
  },
  {
    id: "security",
    title: "Configure Security",
    description: "Set up API keys, configure providers, and customize your experience.",
    icon: Shield,
  },
];

export function OnboardingFlow({ onComplete }: { onComplete: () => void }) {
  const [step, setStep] = useState(0);
  const current = STEPS[Math.min(step, STEPS.length - 1)]!;
  const Icon = current.icon;

  return (
    <div className="flex min-h-[400px] items-center justify-center p-8">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-accent/10">
            <Icon className="h-7 w-7 text-accent" />
          </div>
          <CardTitle className="text-xl">{current.title}</CardTitle>
          <p className="text-sm text-muted mt-2">{current.description}</p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Step indicators */}
          <div className="flex justify-center gap-2">
            {STEPS.map((s, i) => (
              <div
                key={s.id}
                className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold transition-all ${
                  i < step ? "bg-green text-white" : i === step ? "bg-accent text-white" : "bg-secondary text-muted"
                }`}
              >
                {i < step ? <Check className="h-4 w-4" /> : i + 1}
              </div>
            ))}
          </div>

          {/* Navigation */}
          <div className="flex justify-between">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setStep(Math.max(0, step - 1))}
              disabled={step === 0}
            >
              Back
            </Button>
            {step < STEPS.length - 1 ? (
              <Button size="sm" onClick={() => setStep(step + 1)}>
                Next <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            ) : (
              <Button size="sm" onClick={onComplete}>
                Get Started <Sparkles className="ml-2 h-4 w-4" />
              </Button>
            )}
          </div>

          {/* Skip */}
          <div className="text-center">
            <button className="text-xs text-muted hover:text-foreground transition-colors" onClick={onComplete}>
              Skip onboarding
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
