"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import {
  askAIAssistant,
  deleteAIConversation,
  fetchAIConversationMessages,
  fetchAIConversations,
  renameAIConversation,
} from "@/lib/api";
import type { AICitation, AIConversation, AIMessage } from "@/types/ai";
import AIAnswer from "@/components/ai/AIAnswer";
import { useDialog } from "@/components/ui/DialogProvider";
import RelativeTime from "@/components/ui/RelativeTime";

type DisplayMessage = AIMessage & { citations?: AICitation[] };
const suggestions = [
  "Chuẩn đầu ra ngoại ngữ của sinh viên là gì?",
  "Quy định học lại và cải thiện điểm như thế nào?",
  "Điều kiện xét học bổng hiện hành là gì?",
];

export default function AssistantPage() {
  const dialog = useDialog();
  const [conversations, setConversations] = useState<AIConversation[]>([]),
    [activeId, setActiveId] = useState<string | null>(null),
    [messages, setMessages] = useState<DisplayMessage[]>([]),
    [question, setQuestion] = useState(""),
    [loading, setLoading] = useState(true),
    [sending, setSending] = useState(false),
    [error, setError] = useState("");
  const endRef = useRef<HTMLDivElement | null>(null);
  const loadConversations = useCallback(async () => {
    try {
      const rows = await fetchAIConversations();
      setConversations(rows);
      setError("");
      return rows;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không tải được lịch sử AI.");
      return [];
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);
  const openConversation = async (id: string) => {
    setActiveId(id);
    setLoading(true);
    try {
      const result = await fetchAIConversationMessages(id);
      setMessages(result.messages);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không tải được hội thoại.");
    } finally {
      setLoading(false);
    }
  };
  const newConversation = () => {
    setActiveId(null);
    setMessages([]);
    setQuestion("");
    setError("");
  };
  const send = async (event?: FormEvent, override?: string) => {
    event?.preventDefault();
    const value = (override ?? question).trim();
    if (!value || sending) return;
    const optimistic: DisplayMessage = {
      id: `temp-${Date.now()}`,
      sequence_number: messages.length + 1,
      role: "USER",
      content: value,
      rewritten_question: null,
      created_at: new Date().toISOString(),
    };
    setMessages((current) => [...current, optimistic]);
    setQuestion("");
    setSending(true);
    setError("");
    try {
      const answer = await askAIAssistant(value, activeId || undefined);
      setActiveId(answer.conversation_id);
      setMessages((current) => [
        ...current,
        {
          id: answer.message_id,
          sequence_number: current.length + 1,
          role: "ASSISTANT",
          content: answer.answer,
          rewritten_question: answer.rewritten_question,
          created_at: new Date().toISOString(),
          citations: answer.citations,
        },
      ]);
      await loadConversations();
    } catch (e) {
      setMessages((current) =>
        current.filter((item) => item.id !== optimistic.id),
      );
      setQuestion(value);
      setError(e instanceof Error ? e.message : "Trợ lý AI chưa thể trả lời.");
    } finally {
      setSending(false);
    }
  };
  const rename = async (item: AIConversation) => {
    const title = await dialog.prompt({title:"Đổi tên cuộc hội thoại",message:"Đặt tên ngắn gọn để dễ tìm lại trong lịch sử.",initialValue:item.title||"",placeholder:"Tên cuộc hội thoại...",minLength:1});
    if (!title) return;
    await renameAIConversation(item.id, title);
    await loadConversations();
  };
  const remove = async (item: AIConversation) => {
    if (!await dialog.confirm({title:"Xóa cuộc hội thoại?",message:"Toàn bộ lịch sử hỏi đáp trong cuộc hội thoại này sẽ bị xóa.",confirmLabel:"Xóa hội thoại",tone:"danger"})) return;
    await deleteAIConversation(item.id);
    if (activeId === item.id) newConversation();
    await loadConversations();
  };
  return (
    <main className="assistant-page">
      <aside className="assistant-sidebar">
        <header>
          <div>
            <span className="assistant-mark">✦</span>
            <div>
              <strong>Trợ lý HVNH</strong>
              <small>Tra cứu có nguồn</small>
            </div>
          </div>
          <button onClick={newConversation}>＋ Hội thoại mới</button>
        </header>
        <div className="assistant-history-label">Lịch sử gần đây</div>
        <nav>
          {conversations.map((item) => (
            <div className={activeId === item.id ? "active" : ""} key={item.id}>
              <button
                className="assistant-history-main"
                onClick={() => void openConversation(item.id)}
              >
                <b>{item.title || "Hội thoại mới"}</b>
                <RelativeTime value={item.last_message_at || item.created_at}/>
              </button>
              <button
                className="assistant-history-more"
                onClick={() => void rename(item)}
                title="Đổi tên"
              >
                ✎
              </button>
              <button
                className="assistant-history-more danger"
                onClick={() => void remove(item)}
                title="Xóa"
              >
                ×
              </button>
            </div>
          ))}
          {!loading && !conversations.length && (
            <p>Bạn chưa có cuộc hội thoại nào.</p>
          )}
        </nav>
      </aside>
      <section className="assistant-workspace">
        <header className="assistant-topbar">
          <div>
            <span className="assistant-status-dot" />
            <div>
              <strong>Trợ lý thông tin Học viện</strong>
              <small>
                Câu trả lời dựa trên tài liệu chính thức và có trích dẫn
              </small>
            </div>
          </div>
          <span className="assistant-scope">HVNH RAG</span>
        </header>
        <div className="assistant-thread">
          {!messages.length && !loading ? (
            <section className="assistant-welcome">
              <span className="assistant-welcome-icon">✦</span>
              <h1>Bạn cần tìm thông tin gì?</h1>
              <p>
                Hỏi về quy chế, học vụ, chuẩn đầu ra hoặc thông báo của Học
                viện. Trợ lý chỉ trả lời khi tìm thấy nguồn phù hợp.
              </p>
              <div>
                {suggestions.map((item) => (
                  <button key={item} onClick={() => void send(undefined, item)}>
                    {item}
                    <span>→</span>
                  </button>
                ))}
              </div>
            </section>
          ) : (
            messages.map((message) => (
              <article
                className={`assistant-message ${message.role.toLowerCase()}`}
                key={message.id}
              >
                <div className="assistant-message-avatar">
                  {message.role === "USER" ? "Bạn" : "✦"}
                </div>
                <div className="assistant-message-content">
                  <div className="assistant-message-label">
                    {message.role === "USER" ? "Bạn" : "Trợ lý HVNH"}
                  </div>
                  <AIAnswer content={message.content} />
                  {message.citations && message.citations.length > 0 && (
                    <div className="assistant-citations">
                      <strong>Nguồn tham khảo</strong>
                      {message.citations.map((citation) => (
                        <a
                          key={`${message.id}-${citation.order}`}
                          href={citation.source_url || undefined}
                          target={citation.source_url ? "_blank" : undefined}
                          rel="noreferrer"
                        >
                          <span>{citation.order}</span>
                          <div>
                            <b>{citation.title}</b>
                            <small>
                              {[
                                citation.section_title,
                                citation.page_start
                                  ? `Trang ${citation.page_start}`
                                  : null,
                              ]
                                .filter(Boolean)
                                .join(" · ") || "Tài liệu HVNH"}
                            </small>
                          </div>
                        </a>
                      ))}
                    </div>
                  )}
                  <RelativeTime value={message.created_at}/>
                </div>
              </article>
            ))
          )}
          {sending && (
            <article className="assistant-message assistant">
              <div className="assistant-message-avatar">✦</div>
              <div className="assistant-thinking">
                <i />
                <i />
                <i />
                <span>Đang tìm trong nguồn chính thức…</span>
              </div>
            </article>
          )}
          {loading && (
            <div className="assistant-loading">Đang tải hội thoại…</div>
          )}
          {error && <div className="assistant-error">{error}</div>}
          <div ref={endRef} />
        </div>
        <form
          className="assistant-composer"
          onSubmit={(event) => void send(event)}
        >
          <div>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void send();
                }
              }}
              placeholder="Nhập câu hỏi về Học viện Ngân hàng…"
              rows={1}
              maxLength={4000}
            />
            <button
              disabled={!question.trim() || sending}
              aria-label="Gửi câu hỏi"
            >
              ↑
            </button>
          </div>
          <small>
            Trợ lý có thể mắc lỗi. Hãy kiểm tra các nguồn được trích dẫn trước
            khi sử dụng thông tin.
          </small>
        </form>
      </section>
    </main>
  );
}
