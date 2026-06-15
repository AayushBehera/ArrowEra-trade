import { create } from "zustand";

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  toolCalls?: Array<{ name: string; args: Record<string, unknown> }>;
}

interface AgentState {
  messages: ChatMessage[];
  isStreaming: boolean;
  selectedProvider: string | null;
  addMessage: (message: ChatMessage) => void;
  setStreaming: (streaming: boolean) => void;
  setProvider: (provider: string | null) => void;
  clearMessages: () => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  messages: [],
  isStreaming: false,
  selectedProvider: null,
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setStreaming: (isStreaming) => set({ isStreaming }),
  setProvider: (selectedProvider) => set({ selectedProvider }),
  clearMessages: () => set({ messages: [] }),
}));
