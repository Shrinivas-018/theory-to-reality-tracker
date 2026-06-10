import React, { useState, useRef, useEffect, useCallback } from "react";
import { MessageCircle, Send, Loader2, Bot, User, Sparkles, X, RotateCcw } from "lucide-react";
import { authFetch } from "@/lib/api";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface IdeaChatPanelProps {
  ideaId: string;
  ideaTitle: string;
  ideaCategory?: string;
}

const IdeaChatPanel: React.FC<IdeaChatPanelProps> = ({
  ideaId,
  ideaTitle,
  ideaCategory,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const prevIdeaId = useRef(ideaId);
  const historyLoaded = useRef(false);

  // Reset chat when idea changes
  useEffect(() => {
    if (prevIdeaId.current !== ideaId) {
      setMessages([]);
      setInputValue("");
      setIsLoading(false);
      historyLoaded.current = false;
      prevIdeaId.current = ideaId;
    }
  }, [ideaId]);

  // Load saved chat history from MongoDB when panel opens
  useEffect(() => {
    if (isOpen && !historyLoaded.current) {
      historyLoaded.current = true;
      setHistoryLoading(true);
      authFetch(`/api/ideas/${ideaId}/chat/history`)
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
        .catch((err) => console.error("Failed to load chat history:", err))
        .finally(() => setHistoryLoading(false));
    }
  }, [isOpen, ideaId]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && !historyLoading) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen, historyLoading]);

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
      // Build history for API (exclude the message we just added)
      const history = [...messages, userMsg].map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await authFetch(`/api/ideas/${ideaId}/chat`, {
        method: "POST",
        body: JSON.stringify({
          message: trimmed,
          history: history.slice(0, -1), // Don't duplicate the current message
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
          content:
            data.message ||
            "I couldn't generate a response. Please try again.",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, aiMsg]);
      }
    } catch (err) {
      console.error("Chat error:", err);
      const errMsg: ChatMessage = {
        role: "assistant",
        content:
          "Sorry, I encountered an error connecting to the AI service. Please check if the backend is running and try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isLoading, messages, ideaId]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = async () => {
    setMessages([]);
    setInputValue("");
    // Clear from MongoDB too
    try {
      await authFetch(`/api/ideas/${ideaId}/chat/history`, { method: "DELETE" });
    } catch (err) {
      console.error("Failed to clear chat history:", err);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <section className="space-y-3">
      {/* Toggle Button */}
      <button
        id="idea-chat-toggle"
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full flex items-center justify-between gap-3 px-4 py-3 rounded-xl border transition-all duration-300 group
          ${
            isOpen
              ? "bg-gradient-to-r from-violet-50 to-fuchsia-50 border-violet-200 shadow-md"
              : "bg-white border-slate-200 hover:border-violet-200 hover:bg-violet-50/30 hover:shadow-sm"
          }`}
      >
        <div className="flex items-center gap-3">
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-300
            ${
              isOpen
                ? "bg-gradient-to-br from-violet-500 to-fuchsia-500 shadow-lg shadow-violet-200"
                : "bg-gradient-to-br from-violet-400 to-fuchsia-400 group-hover:shadow-md group-hover:shadow-violet-100"
            }`}
          >
            <MessageCircle className="h-4.5 w-4.5 text-white" />
          </div>
          <div className="text-left">
            <div className="font-semibold text-sm text-slate-800">
              AI Research Chat
            </div>
            <div className="text-[11px] text-slate-500">
              Ask questions & research this idea
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-violet-100 text-violet-600">
              {messages.length}
            </span>
          )}
          <Sparkles
            className={`h-4 w-4 transition-colors ${
              isOpen ? "text-violet-500" : "text-slate-300 group-hover:text-violet-400"
            }`}
          />
        </div>
      </button>

      {/* Chat Panel */}
      {isOpen && (
        <div
          className="rounded-xl border border-violet-200/60 overflow-hidden shadow-lg animate-in slide-in-from-top-2 duration-300"
          style={{
            background:
              "linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(245,243,255,0.95) 50%, rgba(253,244,255,0.95) 100%)",
            backdropFilter: "blur(12px)",
          }}
        >
          {/* Chat Header */}
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-violet-100/60 bg-white/50">
            <div className="flex items-center gap-2">
              <Bot className="h-4 w-4 text-violet-500" />
              <span className="text-xs font-semibold text-slate-700">
                Researching:
              </span>
              <span className="text-xs text-violet-600 font-medium truncate max-w-[160px]">
                {ideaTitle}
              </span>
              {ideaCategory && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-violet-100/70 text-violet-500 font-medium">
                  {ideaCategory}
                </span>
              )}
            </div>
            <div className="flex items-center gap-1">
              {messages.length > 0 && (
                <button
                  onClick={clearChat}
                  className="p-1.5 rounded-md hover:bg-violet-100/60 text-slate-400 hover:text-violet-500 transition-colors"
                  title="Clear chat"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-md hover:bg-violet-100/60 text-slate-400 hover:text-slate-600 transition-colors"
                title="Close chat"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div
            className="overflow-y-auto px-4 py-3 space-y-3"
            style={{ maxHeight: "320px", minHeight: "160px" }}
          >
            {/* Welcome message */}
            {/* Loading history indicator */}
            {historyLoading && (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="h-5 w-5 animate-spin text-violet-400" />
                <span className="text-xs text-slate-500 ml-2">Loading conversation history...</span>
              </div>
            )}

            {messages.length === 0 && !isLoading && !historyLoading && (
              <div className="flex flex-col items-center justify-center py-6 text-center">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-400 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-violet-200/50 mb-4">
                  <Sparkles className="h-7 w-7 text-white" />
                </div>
                <p className="text-sm font-semibold text-slate-700 mb-1">
                  AI Research Assistant
                </p>
                <p className="text-xs text-slate-500 max-w-[260px] leading-relaxed">
                  Ask me anything about{" "}
                  <span className="font-semibold text-violet-600">
                    {ideaTitle}
                  </span>{" "}
                  — its history, significance, applications, or connections to
                  other ideas.
                </p>
                <div className="flex flex-wrap gap-1.5 mt-4 justify-center">
                  {[
                    `What is ${ideaTitle.length > 20 ? "this idea" : ideaTitle}?`,
                    "Who were the key contributors?",
                    "How did this evolve?",
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => {
                        setInputValue(suggestion);
                        setTimeout(() => inputRef.current?.focus(), 50);
                      }}
                      className="text-[10px] px-2.5 py-1.5 rounded-lg border border-violet-200/60 bg-white/80 text-violet-600 hover:bg-violet-50 hover:border-violet-300 transition-all cursor-pointer font-medium"
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
                className={`flex gap-2.5 ${
                  msg.role === "user" ? "flex-row-reverse" : "flex-row"
                }`}
              >
                {/* Avatar */}
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${
                    msg.role === "user"
                      ? "bg-gradient-to-br from-blue-500 to-indigo-600 shadow-sm"
                      : "bg-gradient-to-br from-violet-400 to-fuchsia-500 shadow-sm"
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
                      ? "bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-tr-sm"
                      : "bg-white/90 text-slate-700 border border-violet-100/50 rounded-tl-sm"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  <div
                    className={`text-[10px] mt-1.5 ${
                      msg.role === "user"
                        ? "text-blue-200"
                        : "text-slate-400"
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
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-400 to-fuchsia-500 flex items-center justify-center flex-shrink-0 shadow-sm">
                  <Bot className="h-3.5 w-3.5 text-white" />
                </div>
                <div className="bg-white/90 border border-violet-100/50 rounded-xl rounded-tl-sm px-4 py-3 shadow-sm">
                  <div className="flex items-center gap-1.5">
                    <div className="flex gap-1">
                      <span
                        className="w-2 h-2 rounded-full bg-violet-400 animate-bounce"
                        style={{ animationDelay: "0ms" }}
                      />
                      <span
                        className="w-2 h-2 rounded-full bg-violet-400 animate-bounce"
                        style={{ animationDelay: "150ms" }}
                      />
                      <span
                        className="w-2 h-2 rounded-full bg-violet-400 animate-bounce"
                        style={{ animationDelay: "300ms" }}
                      />
                    </div>
                    <span className="text-xs text-slate-400 ml-1">
                      Researching...
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="px-3 py-2.5 border-t border-violet-100/60 bg-white/40">
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                id="idea-chat-input"
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about this idea..."
                disabled={isLoading}
                className="flex-1 px-3.5 py-2.5 text-sm bg-white/80 border border-violet-200/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-300/50 focus:border-violet-300 placeholder:text-slate-400 disabled:opacity-50 transition-all"
              />
              <button
                id="idea-chat-send"
                onClick={sendMessage}
                disabled={!inputValue.trim() || isLoading}
                className={`p-2.5 rounded-xl transition-all duration-200 flex items-center justify-center
                  ${
                    inputValue.trim() && !isLoading
                      ? "bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white shadow-md shadow-violet-200/50 hover:shadow-lg hover:shadow-violet-300/50 hover:scale-105 active:scale-95"
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
      )}
    </section>
  );
};

export default IdeaChatPanel;
