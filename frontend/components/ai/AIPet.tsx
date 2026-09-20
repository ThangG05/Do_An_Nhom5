"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
import { askAIAssistant } from "@/lib/api";
import type { AICitation } from "@/types/ai";
import AIAnswer from "@/components/ai/AIAnswer";

type PetMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: AICitation[];
};

const prompts = [
  "Chuẩn đầu ra ngoại ngữ là gì?",
  "Điều kiện xét học bổng?",
  "Quy định học lại thế nào?",
];

function PetFace({ thinking = false }: { thinking?: boolean }) {
  return (
    <span
      className={`ai-pet-face${thinking ? " thinking" : ""}`}
      aria-hidden="true"
    >
      <i className="ai-pet-cap" />
      <i className="ai-pet-ear left" />
      <i className="ai-pet-ear right" />
      <span className="ai-pet-screen">
        <i className="ai-pet-eye left" />
        <i className="ai-pet-eye right" />
        <i className="ai-pet-smile" />
      </span>
      <i className="ai-pet-spark one">✦</i>
      <i className="ai-pet-spark two">✦</i>
    </span>
  );
}

export default function AIPet({ userName }: { userName?: string }) {
  const [open, setOpen] = useState(false),
    [question, setQuestion] = useState(""),
    [sending, setSending] = useState(false),
    [error, setError] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>(),
    [messages, setMessages] = useState<PetMessage[]>([]);
  const endRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const stored = sessionStorage.getItem("hvnh-ai-pet-conversation");
    if (stored) setConversationId(stored);
  }, []);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending, open]);
  const send = async (event?: FormEvent, valueOverride?: string) => {
    event?.preventDefault();
    const value = (valueOverride ?? question).trim();
    if (!value || sending) return;
    const userMessage: PetMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: value,
    };
    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setSending(true);
    setError("");
    try {
      const result = await askAIAssistant(value, conversationId);
      setConversationId(result.conversation_id);
      sessionStorage.setItem(
        "hvnh-ai-pet-conversation",
        result.conversation_id,
      );
      setMessages((current) => [
        ...current,
        {
          id: result.message_id,
          role: "assistant",
          content: result.answer,
          citations: result.citations,
        },
      ]);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Trợ lý đang bận, bạn thử lại sau nhé.",
      );
    } finally {
      setSending(false);
    }
  };
  return (
    <aside
      className={`ai-pet${open ? " open" : ""}`}
      aria-label="Trợ lý AI HVNH"
    >
      {open && (
        <section
          className="ai-pet-panel"
          role="dialog"
          aria-label="Hỏi nhanh trợ lý HVNH"
        >
          <header>
            <div>
              <PetFace />
              <span>
                <strong>Trợ lý HVNH</strong>
                <small>
                  <i /> Tra cứu từ nguồn chính thức
                </small>
              </span>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Thu nhỏ trợ lý"
            >
              ×
            </button>
          </header>
          <div className="ai-pet-thread">
            {!messages.length && (
              <div className="ai-pet-intro">
                <PetFace />
                <h2>Chào {userName?.split(" ").at(-1) || "bạn"}!</h2>
                <p>
                  Mình có thể giúp bạn tra cứu quy chế, học vụ và thông báo của
                  Học viện.
                </p>
                <div>
                  {prompts.map((prompt) => (
                    <button
                      type="button"
                      key={prompt}
                      onClick={() => void send(undefined, prompt)}
                    >
                      {prompt}
                      <span>›</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((message) => (
              <article key={message.id} className={message.role}>
                <span>
                  {message.role === "assistant" ? <PetFace /> : "Bạn"}
                </span>
                <div>
                    <AIAnswer content={message.content} compact />
                  {message.citations && message.citations.length > 0 && (
                    <details>
                      <summary>
                        {message.citations.length} nguồn tham khảo
                      </summary>
                      {message.citations.slice(0, 3).map((citation) => (
                        <a
                          key={`${message.id}-${citation.order}`}
                          href={citation.source_url || undefined}
                          target={citation.source_url ? "_blank" : undefined}
                          rel="noreferrer"
                        >
                          <b>{citation.order}</b>
                          <span>{citation.title}</span>
                        </a>
                      ))}
                    </details>
                  )}
                </div>
              </article>
            ))}
            {sending && (
              <article className="assistant loading">
                <span>
                  <PetFace thinking />
                </span>
                <div>
                  <p>
                    <i />
                    <i />
                    <i /> Đang tìm trong tài liệu…
                  </p>
                </div>
              </article>
            )}
            {error && <div className="ai-pet-error">{error}</div>}
            <div ref={endRef} />
          </div>
          <form onSubmit={(event) => void send(event)}>
            <textarea
              rows={1}
              maxLength={4000}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void send();
                }
              }}
              placeholder="Hỏi nhanh về HVNH…"
              aria-label="Câu hỏi cho trợ lý AI"
            />
            <button
              type="submit"
              disabled={!question.trim() || sending}
              aria-label="Gửi câu hỏi"
            >
              ↑
            </button>
          </form>
          <footer>
            <span>AI có thể mắc lỗi, hãy kiểm tra nguồn.</span>
            <Link href="/assistant">Mở trợ lý đầy đủ ↗</Link>
          </footer>
        </section>
      )}
      {!open && (
        <div className="ai-pet-hint" aria-hidden="true">
          <strong>Bạn cần tra cứu gì?</strong>
          <span>Hỏi trợ lý HVNH nhé!</span>
        </div>
      )}
      <button
        className="ai-pet-launcher"
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-label={open ? "Đóng trợ lý AI" : "Mở trợ lý AI"}
      >
        <PetFace thinking={sending} />
        <span className="ai-pet-online" />
        {!open && <b>AI</b>}
      </button>
    </aside>
  );
}
