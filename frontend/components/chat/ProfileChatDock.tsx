"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { createDirectConversation, fetchMessages, sendChatMessage } from "@/lib/api";
import { getAuthUser } from "@/lib/auth";
import { safeImageSrc } from "@/lib/media";
import type { Message } from "@/types/message";

interface Props { userId: string; name: string; avatar: string; onClose: () => void }

export default function ProfileChatDock({ userId, name, avatar, onClose }: Props) {
  const [conversationId, setConversationId] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [minimized, setMinimized] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const currentUserId = getAuthUser()?.id;

  useEffect(() => {
    let mounted = true;
    void createDirectConversation(userId).then(async conversation => {
      const rows = await fetchMessages(conversation.id);
      if (!mounted) return;
      setConversationId(conversation.id);
      setMessages(rows);
    }).catch(reason => { if (mounted) setError(reason instanceof Error ? reason.message : "Không thể mở cuộc trò chuyện."); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [userId]);

  useEffect(() => {
    if (!conversationId) return;
    const receive = (event: Event) => {
      const data = (event as CustomEvent<Record<string, unknown>>).detail;
      if (data?.event !== "message.created") return;
      const incoming = data.message as Message | undefined;
      if (incoming?.conversationId !== conversationId) return;
      setMessages(previous => previous.some(item => item.id === incoming.id) ? previous : [...previous, incoming]);
    };
    window.addEventListener("hvnh-realtime", receive);
    return () => window.removeEventListener("hvnh-realtime", receive);
  }, [conversationId]);

  useEffect(() => { if (!minimized) bottomRef.current?.scrollIntoView({ block: "end" }); }, [messages, minimized]);

  const send = async () => {
    const content = draft.trim();
    if (!content || !conversationId || sending) return;
    setDraft("");
    setError("");
    setSending(true);
    try {
      const created = await sendChatMessage(conversationId, content);
      setMessages(previous => previous.some(item => item.id === created.id) ? previous : [...previous, created]);
      window.dispatchEvent(new Event("messages-changed"));
    } catch (reason) {
      setDraft(previous => previous || content);
      setError(reason instanceof Error ? reason.message : "Không thể gửi tin nhắn.");
    } finally { setSending(false); }
  };

  return <aside className={`profile-chat-dock ${minimized ? "minimized" : ""}`} aria-label={`Trò chuyện với ${name}`}>
    <header><img src={safeImageSrc(avatar)} alt="" /><strong>{name}</strong><div><button type="button" onClick={() => setMinimized(value => !value)} aria-label={minimized ? "Mở rộng trò chuyện" : "Thu nhỏ trò chuyện"}>{minimized ? "▢" : "−"}</button><button type="button" onClick={onClose} aria-label="Đóng trò chuyện">×</button></div></header>
    {!minimized && <><div className="profile-chat-messages" aria-live="polite">
      {loading ? <p>Đang mở trò chuyện...</p> : messages.length ? messages.map(message => <div key={message.id} className={`profile-chat-message ${message.senderId === currentUserId ? "mine" : ""}`}><span>{message.content || message.attachments?.map(item => item.name).join(", ") || "Tệp đính kèm"}</span></div>) : !error && <p>Hãy gửi lời chào cho {name}.</p>}
      <div ref={bottomRef} />
    </div><form className="profile-chat-composer" onSubmit={event => { event.preventDefault(); void send(); }}><input value={draft} onChange={event => setDraft(event.target.value)} placeholder="Viết tin nhắn..." aria-label="Viết tin nhắn" disabled={!conversationId || sending}/><button type="submit" disabled={!conversationId || !draft.trim() || sending} aria-label="Gửi tin nhắn">➤</button></form>{error && <p className="profile-chat-error" role="alert">{error}</p>}{conversationId && <Link className="profile-chat-open-all" href={`/messages?conversationId=${encodeURIComponent(conversationId)}`}>Mở toàn bộ cuộc trò chuyện</Link>}</>}
  </aside>;
}
