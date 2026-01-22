"use client";

import React, { useState, useRef, useEffect } from "react";
import { 
  MessageSquare, 
  Send, 
  X, 
  Bot, 
  User, 
  Sparkles,
  Trash2,
  ChevronRight
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
  timestamp: Date;
}

export default function ChatAI() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "ai",
      content: "안녕하세요. 업로드된 명부 데이터를 기반으로 K-IFRS 기준 검토 및 맥락 분석을 도와드리는 AI 분석 비서입니다. 궁금하신 데이터 패턴이나 특정 리스트 추출 요청을 입력해주세요.",
      timestamp: new Date(),
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "ai",
        content: "현재 입력하신 요청에 대해 전체 명부 데이터를 스캐닝하고 있습니다. 분석이 완료되면 시각화된 리스트와 함께 답변을 드릴 예정입니다. (현재 UI/UX 프레임워크 단계입니다)",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiResponse]);
      setIsTyping(false);
    }, 1500);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: "1",
        role: "ai",
        content: "분석 컨텍스트가 초기화되었습니다. 새로운 질문을 입력해주세요.",
        timestamp: new Date(),
      },
    ]);
  };

  const quickActions = [
    "급여 변동성 ±20% 이상자 추출",
    "입사일/생년월일 논리 오류 분석",
    "직종별 퇴직급여 추계액 요약",
    "연령대별 평균 근속 기간"
  ];

  return (
    <>
      {/* Overlay for mobile/tablet */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/20 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Main Sidebar Panel (Drawer) */}
      <div 
        className={cn(
          "fixed top-0 right-0 h-full bg-white shadow-[-10px_0_30px_rgba(0,0,0,0.05)] z-50 flex flex-col transition-all duration-500 ease-in-out border-l border-slate-200",
          isOpen ? "w-full md:w-[450px] lg:w-[500px]" : "w-0 overflow-hidden border-none"
        )}
      >
        {/* Header */}
        <div className="p-6 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center shadow-lg shadow-primary-600/30">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-base tracking-tight">AI Data Insights</h3>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                <span className="text-[11px] text-slate-400 font-medium font-sans">K-IFRS 분석 엔진 가동 중</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={clearChat}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors text-slate-400"
              title="대화 초기화"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button 
              onClick={() => setIsOpen(false)}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors text-slate-400"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Message Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50">
          {messages.map((msg) => (
            <div 
              key={msg.id}
              className={cn(
                "flex gap-4",
                msg.role === "user" ? "flex-row-reverse" : ""
              )}
            >
              <div className={cn(
                "w-9 h-9 rounded-xl flex-shrink-0 flex items-center justify-center shadow-sm",
                msg.role === "ai" ? "bg-white text-primary-600 border border-slate-200" : "bg-primary-600 text-white"
              )}>
                {msg.role === "ai" ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
              </div>
              <div className={cn("flex flex-col", msg.role === "user" ? "items-end" : "items-start")}>
                <div className={cn(
                  "p-4 rounded-2xl text-[14px] leading-relaxed shadow-sm max-w-[90%]",
                  msg.role === "ai" 
                    ? "bg-white text-slate-800 rounded-tl-none border border-slate-200" 
                    : "bg-slate-800 text-white rounded-tr-none"
                )}>
                  {msg.content}
                </div>
                <span className="text-[10px] text-slate-400 mt-2 font-medium uppercase tracking-wider font-sans">
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex gap-4">
              <div className="w-9 h-9 rounded-xl bg-white text-primary-600 border border-slate-200 flex items-center justify-center">
                <Bot className="w-5 h-5" />
              </div>
              <div className="bg-white p-4 rounded-2xl rounded-tl-none border border-slate-200 flex gap-1.5 items-center shadow-sm">
                <span className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                <span className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce"></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Action & Input Area */}
        <div className="p-6 bg-white border-t border-slate-200 shadow-[0_-10px_20px_rgba(0,0,0,0.02)]">
          <p className="text-[11px] font-bold text-slate-400 mb-3 uppercase tracking-widest font-sans">Suggested Analysis</p>
          <div className="flex flex-wrap gap-2 mb-6">
            {quickActions.map((action, i) => (
              <button 
                key={i}
                onClick={() => setInput(action)}
                className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-[12px] text-slate-600 hover:border-primary-500 hover:text-primary-600 hover:bg-primary-50 transition-all font-medium font-sans"
              >
                {action}
              </button>
            ))}
          </div>

          <div className="relative group">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="분석이 필요한 내용을 입력하세요..."
              rows={2}
              className="w-full pl-4 pr-14 py-4 bg-slate-100 border-2 border-transparent rounded-2xl text-sm focus:bg-white focus:border-primary-500 focus:ring-0 transition-all resize-none placeholder:text-slate-400 font-medium font-sans"
            />
            <button 
              onClick={handleSend}
              disabled={!input.trim()}
              className={cn(
                "absolute right-3 bottom-3 p-3 rounded-xl transition-all",
                input.trim() 
                  ? "bg-slate-900 text-white shadow-xl hover:bg-primary-600" 
                  : "bg-slate-200 text-slate-400 cursor-not-allowed"
              )}
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <div className="mt-4 flex items-center justify-center gap-2">
            <Sparkles className="w-3 h-3 text-primary-500" />
            <p className="text-[10px] text-slate-400 font-medium font-sans">
              Powered by WikiSoft AI Analysis Engine
            </p>
          </div>
        </div>
      </div>

      {/* Floating Trigger Button (When closed) */}
      {!isOpen && (
        <button 
          onClick={() => setIsOpen(true)}
          className="fixed bottom-8 right-8 z-40 group flex items-center gap-3"
        >
          <div className="bg-slate-900 text-white px-5 py-3 rounded-2xl shadow-2xl opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-4 group-hover:translate-x-0 font-bold text-sm whitespace-nowrap">
            AI 데이터 분석 실행
          </div>
          <div className="w-16 h-16 bg-primary-600 text-white rounded-2xl shadow-[0_15px_30px_rgba(37,99,235,0.4)] flex items-center justify-center transition-all duration-300 group-hover:scale-110 group-hover:rotate-12 active:scale-95">
            <MessageSquare className="w-7 h-7" />
            <span className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white text-[11px] font-bold rounded-lg flex items-center justify-center border-2 border-white shadow-lg">
              1
            </span>
          </div>
        </button>
      )}
    </>
  );
}
