import React, { useState, useRef, useEffect, useCallback } from "react";
import { MessageCircle, Send, Loader2, Bot, User, Sparkles, X, RotateCcw, Minimize2, Maximize2 } from "lucide-react";
import { authFetch } from "@/lib/api";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const YugasChatPanel: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const historyLoaded = useRef(false);

  // Load saved chat history from MongoDB when panel opens
  useEffect(() => {
    if (isOpen && !historyLoaded.current) {
      historyLoaded.current = true;
      setHistoryLoading(true);
      authFetch("/api/yugas/chat/history")
        .then((res) => res.json())
        .then((data) => {
          if (data?.data?.messages && data.data.messages.length > 0) {
            const saved: ChatMessage[] = data.data.messages.map((m: any) => ({
              role: m.role as "user" | "assistant",
              content: m.content,
              timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
            }));
            setMessages(saved);
          }
        })
        .catch((err) => console.error("Failed to load Yugas chat history:", err))
        .finally(() => setHistoryLoading(false));
    }
  }, [isOpen]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && !isMinimized && !historyLoading) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen, isMinimized, historyLoading]);

  const sendMessage = useCallback(async () => {
    const trimmed = inputValue.trim();
    if (!trimmed || isLoading) return;

    const userMsg: ChatMessage = {
      role: "user",
      content: trimmed,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsLoading(true);

    try {
      const history = [...messages, userMsg].map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await authFetch("/api/yugas/chat", {
        method: "POST",
        body: JSON.stringify({
          message: trimmed,
          history: history.slice(0, -1),
        }),
      });

      const data = await res.json();

      if (data?.data?.reply) {
        const aiMsg: ChatMessage = {
          role: "assistant",
          content: data.data.reply,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, aiMsg]);
      } else if (data?.message) {
        const aiMsg: ChatMessage = {
          role: "assistant",
          content: data.message || "I couldn't generate a response. Please try again.",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, aiMsg]);
      }
    } catch (err) {
      console.error("Yugas chat error:", err);
      const errMsg: ChatMessage = {
        role: "assistant",
        content: "Sorry, I encountered an error connecting to the AI service. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isLoading, messages]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = async () => {
    setMessages([]);
    setInputValue("");
    try {
      await authFetch("/api/yugas/chat/history", { method: "DELETE" });
    } catch (err) {
      console.error("Failed to clear Yugas chat history:", err);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  // Floating button when closed
  if (!isOpen) {
    return (
      <button
        id="yugas-chat-fab"
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-500 via-orange-500 to-red-500 text-white shadow-2xl shadow-orange-300/50 flex items-center justify-center hover:scale-110 hover:shadow-orange-400/60 active:scale-95 transition-all duration-300 group"
        title="Chat about Yugas"
      >
        <MessageCircle className="h-6 w-6 group-hover:rotate-12 transition-transform" />
        {messages.length > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-white text-orange-600 text-[10px] font-bold flex items-center justify-center shadow-sm">
            {messages.length}
          </span>
        )}
        {/* Pulse ring */}
        <span className="absolute inset-0 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 animate-ping opacity-20" />
      </button>
    );
  }

  // Minimized bar
  if (isMinimized) {
    return (
      <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 bg-gradient-to-r from-amber-500 via-orange-500 to-red-500 text-white rounded-2xl px-4 py-2.5 shadow-2xl shadow-orange-300/40 cursor-pointer hover:shadow-orange-400/50 transition-all"
        onClick={() => setIsMinimized(false)}
      >
        <Bot className="h-4 w-4" />
        <span className="text-sm font-semibold">Yugas AI Chat</span>
        {messages.length > 0 && (
          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-white/20">{messages.length}</span>
        )}
        <Maximize2 className="h-3.5 w-3.5 ml-1 opacity-70" />
      </div>
    );
  }

  // Full chat panel
  return (
    <div className="fixed bottom-6 right-6 z-50 w-[380px] max-h-[520px] flex flex-col rounded-2xl overflow-hidden shadow-2xl shadow-orange-200/40 border border-orange-200/30"
      style={{
        background: "linear-gradient(160deg, rgba(255,251,235,0.97) 0%, rgba(255,247,237,0.97) 50%, rgba(254,243,199,0.97) 100%)",
        backdropFilter: "blur(20px)",
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-amber-500 via-orange-500 to-red-500 text-white">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <div className="text-sm font-bold leading-tight">Yugas AI Assistant</div>
            <div className="text-[10px] opacity-80 font-medium">Cosmic Evolution Explorer</div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="p-1.5 rounded-lg hover:bg-white/15 transition-colors"
              title="Clear chat"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          )}
          <button
            onClick={() => setIsMinimized(true)}
            className="p-1.5 rounded-lg hover:bg-white/15 transition-colors"
            title="Minimize"
          >
            <Minimize2 className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 rounded-lg hover:bg-white/15 transition-colors"
            title="Close chat"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div
        className="flex-1 overflow-y-auto px-4 py-3 space-y-3"
        style={{ maxHeight: "340px", minHeight: "180px" }}
      >
        {/* Loading history indicator */}
        {historyLoading && (
          <div className="flex items-center justify-center py-6">
            <Loader2 className="h-5 w-5 animate-spin text-amber-500" />
            <span className="text-xs text-slate-500 ml-2">Loading conversation history...</span>
          </div>
        )}

        {/* Welcome message */}
        {messages.length === 0 && !isLoading && !historyLoading && (
          <div className="flex flex-col items-center justify-center py-5 text-center">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-400 via-orange-500 to-red-500 flex items-center justify-center shadow-lg shadow-orange-200/50 mb-4">
              <Sparkles className="h-7 w-7 text-white" />
            </div>
            <p className="text-sm font-bold text-slate-800 mb-1">
              Yugas Cosmic Explorer
            </p>
            <p className="text-xs text-slate-500 max-w-[280px] leading-relaxed">
              Ask me anything about the four Yugas, cosmic evolution, or how any idea transforms across the ages.
            </p>
            <div className="flex flex-wrap gap-1.5 mt-4 justify-center">
              {[
                "What are the four Yugas?",
                "How do ideas evolve across eras?",
                "Tell me about Satya Yuga",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => {
                    setInputValue(suggestion);
                    setTimeout(() => inputRef.current?.focus(), 50);
                  }}
                  className="text-[10px] px-2.5 py-1.5 rounded-lg border border-amber-200/60 bg-white/80 text-amber-700 hover:bg-amber-50 hover:border-amber-300 transition-all cursor-pointer font-medium"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message Bubbles */}
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
          >
            {/* Avatar */}
            <div
              className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${
                msg.role === "user"
                  ? "bg-gradient-to-br from-amber-500 to-orange-600 shadow-sm"
                  : "bg-gradient-to-br from-orange-400 to-red-500 shadow-sm"
              }`}
            >
              {msg.role === "user" ? (
                <User className="h-3.5 w-3.5 text-white" />
              ) : (
                <Bot className="h-3.5 w-3.5 text-white" />
              )}
            </div>

            {/* Bubble */}
            <div
              className={`max-w-[82%] rounded-xl px-3.5 py-2.5 text-[13px] leading-relaxed shadow-sm ${
                msg.role === "user"
                  ? "bg-gradient-to-br from-amber-500 to-orange-600 text-white rounded-tr-sm"
                  : "bg-white/90 text-slate-700 border border-amber-100/50 rounded-tl-sm"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              <div
                className={`text-[10px] mt-1.5 ${
                  msg.role === "user" ? "text-amber-200" : "text-slate-400"
                }`}
              >
                {formatTime(msg.timestamp)}
              </div>
            </div>
          </div>
        ))}

        {/* Typing Indicator */}
        {isLoading && (
          <div className="flex gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center flex-shrink-0 shadow-sm">
              <Bot className="h-3.5 w-3.5 text-white" />
            </div>
            <div className="bg-white/90 border border-amber-100/50 rounded-xl rounded-tl-sm px-4 py-3 shadow-sm">
              <div className="flex items-center gap-1.5">
                <div className="flex gap-1">
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
                <span className="text-xs text-slate-400 ml-1">Consulting the cosmos...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="px-3 py-2.5 border-t border-amber-100/60 bg-white/40">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            id="yugas-chat-input"
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about the Yugas..."
            disabled={isLoading}
            className="flex-1 px-3.5 py-2.5 text-sm bg-white/80 border border-amber-200/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-300/50 focus:border-amber-300 placeholder:text-slate-400 disabled:opacity-50 transition-all"
          />
          <button
            id="yugas-chat-send"
            onClick={sendMessage}
            disabled={!inputValue.trim() || isLoading}
            className={`p-2.5 rounded-xl transition-all duration-200 flex items-center justify-center
              ${
                inputValue.trim() && !isLoading
                  ? "bg-gradient-to-br from-amber-500 to-orange-600 text-white shadow-md shadow-orange-200/50 hover:shadow-lg hover:shadow-orange-300/50 hover:scale-105 active:scale-95"
                  : "bg-slate-100 text-slate-400 cursor-not-allowed"
              }`}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </div>
        <div className="text-center mt-1.5">
          <span className="text-[10px] text-slate-400">
            Powered by OpenAI · Press Enter to send · Chat history saved
          </span>
        </div>
      </div>
    </div>
  );
};

export default YugasChatPanel;
