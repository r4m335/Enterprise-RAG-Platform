"use client";

import { useState, useEffect, useRef } from "react";
import { fetchClient } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { MarkdownRenderer } from "@/components/markdown-renderer";

interface Citation {
  document_id: string;
  document_name?: string;
  chunk_id: string;
  page_number?: number;
  score: number;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  timestamp: string;
}

interface Conversation {
  id: string;
  created_at: string;
}

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const { logout } = useAuth();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      const data = await fetchClient("/api/v1/chat/conversations");
      setConversations(data);
    } catch (e) {
      console.error("Failed to fetch conversations");
    }
  };

  const loadConversation = async (id: string) => {
    try {
      setActiveConversationId(id);
      const data = await fetchClient(`/api/v1/chat/conversations/${id}`);
      setMessages(data.messages || []);
    } catch (e) {
      console.error("Failed to load conversation");
    }
  };

  const startNewChat = () => {
    setActiveConversationId(null);
    setMessages([]);
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput("");
    setLoading(true);

    // Optimistically add user message
    const tempId = Date.now().toString();
    setMessages((prev) => [
      ...prev,
      { id: tempId, role: "user", content: userMsg, timestamp: new Date().toISOString() },
    ]);

    try {
      const response = await fetchClient("/api/v1/chat/", {
        method: "POST",
        body: JSON.stringify({
          query: userMsg,
          conversation_id: activeConversationId,
        }),
      });

      if (!activeConversationId) {
        setActiveConversationId(response.conversation_id);
        fetchConversations(); // refresh list
      }

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString() + "-ast",
          role: "assistant",
          content: response.answer,
          citations: response.citations,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (e: any) {
      alert("Error: " + e.message);
    } finally {
      setLoading(false);
      setTimeout(() => {
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
      }, 100);
    }
  };

  return (
    <div className="flex h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 flex flex-col">
        <div className="p-4 border-b border-zinc-200 dark:border-zinc-800">
          <Button className="w-full" onClick={startNewChat}>+ New Chat</Button>
        </div>
        <ScrollArea className="flex-1 p-2">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => loadConversation(conv.id)}
              className={`w-full text-left px-3 py-2 text-sm rounded-md truncate transition-colors ${
                activeConversationId === conv.id
                  ? "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-50"
                  : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
              }`}
            >
              {new Date(conv.created_at).toLocaleString()}
            </button>
          ))}
        </ScrollArea>
        <div className="p-4 border-t border-zinc-200 dark:border-zinc-800 flex justify-between items-center">
           <Link href="/dashboard" className="text-sm text-zinc-500 hover:underline">Dashboard</Link>
           <Button variant="ghost" size="sm" onClick={logout}>Logout</Button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col relative">
        <div className="h-14 border-b border-zinc-200 dark:border-zinc-800 flex items-center px-6 bg-white dark:bg-zinc-900 shadow-sm z-10">
          <h2 className="font-semibold text-lg">Enterprise RAG Chat</h2>
        </div>
        
        <div className="flex-1 overflow-auto p-6" ref={scrollRef}>
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.length === 0 ? (
              <div className="text-center text-zinc-500 mt-20">
                <h3 className="text-xl font-medium mb-2">Welcome to Enterprise RAG</h3>
                <p>Ask a question based on your uploaded documents.</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`rounded-xl p-5 ${
                    msg.role === "user" 
                      ? "max-w-[85%] bg-zinc-900 text-zinc-50 dark:bg-zinc-50 dark:text-zinc-900 shadow-sm" 
                      : "max-w-full w-full bg-white border border-zinc-200/80 dark:bg-zinc-900 dark:border-zinc-800 shadow-sm"
                  }`}>
                    {msg.role === "user" ? (
                      <div className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</div>
                    ) : (
                      <MarkdownRenderer content={msg.content} />
                    )}
                    
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-zinc-200/80 dark:border-zinc-800">
                        <p className="text-xs font-semibold mb-2 text-zinc-500 dark:text-zinc-400">Sources & Citations:</p>
                        <div className="flex flex-wrap gap-2">
                          {msg.citations.map((c, i) => {
                            const name = c.document_name || `Doc ${c.document_id.slice(0, 8)}`;
                            return (
                              <span key={i} className="inline-flex items-center gap-1.5 text-xs text-zinc-700 dark:text-zinc-200 bg-zinc-100 dark:bg-zinc-800/80 px-2.5 py-1 rounded-md border border-zinc-200/80 dark:border-zinc-700/70 font-medium">
                                <svg className="w-3.5 h-3.5 text-zinc-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                </svg>
                                <span>{name}</span>
                                {c.page_number ? <span className="text-zinc-400 dark:text-zinc-500">• Page {c.page_number}</span> : null}
                                <span className="text-zinc-400 dark:text-zinc-500 font-mono">• {(c.score * 100).toFixed(1)}% match</span>
                              </span>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-zinc-200 dark:bg-zinc-900 dark:border-zinc-800 shadow-sm rounded-lg p-4 text-zinc-500">
                  Thinking...
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white dark:bg-zinc-900 border-t border-zinc-200 dark:border-zinc-800">
          <form onSubmit={sendMessage} className="max-w-4xl mx-auto flex gap-4">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              className="flex-1"
              disabled={loading}
            />
            <Button type="submit" disabled={loading || !input.trim()}>
              Send
            </Button>
          </form>
        </div>
      </main>
    </div>
  );
}
