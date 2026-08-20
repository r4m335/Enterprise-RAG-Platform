"use client";

import { useState, useEffect, useRef } from "react";
import { fetchClient } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

interface Citation {
  document_id: string;
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
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.length === 0 ? (
              <div className="text-center text-zinc-500 mt-20">
                <h3 className="text-xl font-medium mb-2">Welcome to Enterprise RAG</h3>
                <p>Ask a question based on your uploaded documents.</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[80%] rounded-lg p-4 ${msg.role === "user" ? "bg-zinc-900 text-zinc-50 dark:bg-zinc-50 dark:text-zinc-900" : "bg-white border border-zinc-200 dark:bg-zinc-900 dark:border-zinc-800 shadow-sm"}`}>
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                    
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-700">
                        <p className="text-xs font-semibold mb-2 text-zinc-500">Sources:</p>
                        <ul className="space-y-1">
                          {msg.citations.map((c, i) => (
                            <li key={i} className="text-xs text-zinc-500 bg-zinc-100 dark:bg-zinc-800 px-2 py-1 rounded inline-block mr-2 mb-2">
                              {c.document_id.slice(0,8)} {c.page_number ? `(Page ${c.page_number})` : ''} - {(c.score * 100).toFixed(1)}% match
                            </li>
                          ))}
                        </ul>
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
          <form onSubmit={sendMessage} className="max-w-3xl mx-auto flex gap-4">
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
