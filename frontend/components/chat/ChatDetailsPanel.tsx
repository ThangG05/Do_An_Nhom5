"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Conversation, MessageAttachment } from "@/types/message";
import { safeImageSrc } from "@/lib/media";
import { createReport, fetchConversationShared, setUserBlocked } from "@/lib/api";

interface ChatDetailsPanelProps {
  conversation: Conversation;
  onClose: () => void;
  onSearch: () => void;
  onUpdateSettings: (payload:{theme?:Conversation['theme'];nickname?:string;is_muted?:boolean}) => Promise<void>;
  onBlocked: () => void;
}

export default function ChatDetailsPanel({
  conversation,
  onClose,
  onSearch,
  onUpdateSettings,
  onBlocked,
}: ChatDetailsPanelProps) {
  const router=useRouter();
  const [openCustomization, setOpenCustomization] = useState(true);
  const [openMedia, setOpenMedia] = useState(true);
  const [openPrivacy, setOpenPrivacy] = useState(false);
  const [dialog,setDialog]=useState<'theme'|'nickname'|'block'|'report'|null>(null),[value,setValue]=useState(""),[busy,setBusy]=useState(false),[error,setError]=useState("");
  const [sharedMedia,setSharedMedia]=useState<MessageAttachment[]>([]),[sharedFiles,setSharedFiles]=useState<MessageAttachment[]>([]),[sharedLoading,setSharedLoading]=useState(true),[sharedError,setSharedError]=useState("");
  useEffect(()=>{let active=true;const load=()=>{setSharedLoading(true);setSharedError("");void fetchConversationShared(conversation.id).then(result=>{if(active){setSharedMedia(result.media);setSharedFiles(result.files);}}).catch(e=>{if(active)setSharedError(e instanceof Error?e.message:'Không thể tải tệp đã chia sẻ.');}).finally(()=>{if(active)setSharedLoading(false);});};load();window.addEventListener('messages-changed',load);return()=>{active=false;window.removeEventListener('messages-changed',load);};},[conversation.id]);
  const submit=async()=>{setBusy(true);setError("");try{if(dialog==='nickname')await onUpdateSettings({nickname:value});else if(dialog==='block'){await setUserBlocked(conversation.participantId,true);onBlocked();}else if(dialog==='report'){if(value.trim().length<5)throw new Error('Lý do cần ít nhất 5 ký tự.');await createReport('USER',conversation.participantId,value.trim());}setDialog(null);setValue("");}catch(e){setError(e instanceof Error?e.message:'Không thể thực hiện thao tác.');}finally{setBusy(false);}};

  return (
    <aside className="messenger-right-panel" aria-label="Chi tiết cuộc trò chuyện">
      {/* Panel Top Close */}
      <div className="panel-header-top">
        <h3>Thông tin hội thoại</h3>
        <button
          type="button"
          className="close-panel-btn"
          onClick={onClose}
          aria-label="Đóng bảng thông tin"
        >
          ✕
        </button>
      </div>

      <div className="details-scroll-content">
        {/* Profile Card Summary */}
        <div className="profile-summary-card">
          <div className="large-avatar-shell">
            <div className="avatar-core"><img src={safeImageSrc(conversation.participantAvatar)} alt={conversation.participantName}/></div>
            <span
              className={`status-dot ${
                conversation.isOnline ? "online" : "offline"
              }`}
            />
          </div>

          <h3 className="profile-display-name">{conversation.participantName}</h3>
          {conversation.role && (
            <span className="profile-role-chip">{conversation.role}</span>
          )}
          {conversation.bio && (
            <p className="profile-bio-text">{conversation.bio}</p>
          )}

          {/* Quick Action Circle Buttons */}
          <div className="profile-quick-actions">
            <button
              type="button"
              className="action-circle-btn"
              onClick={() => router.push(`/profile/${conversation.participantId}`)}
            >
              👤 <span>Hồ sơ</span>
            </button>
            <button
              type="button"
              className={`action-circle-btn ${conversation.isMuted ? "muted" : ""}`}
              onClick={() => void onUpdateSettings({is_muted:!conversation.isMuted})}
            >
              {conversation.isMuted ? "🔕" : "🔔"} <span>{conversation.isMuted ? "Đã tắt" : "Tắt thông báo"}</span>
            </button>
            <button
              type="button"
              className="action-circle-btn"
              onClick={onSearch}
            >
              ⌕ <span>Tìm kiếm</span>
            </button>
          </div>
        </div>

        {/* Accordion 1: Chat Customization */}
        <div className="accordion-section">
          <button
            type="button"
            className="accordion-header"
            onClick={() => setOpenCustomization((prev) => !prev)}
          >
            <span>🎨 Tùy chỉnh cuộc trò chuyện</span>
            <span className="chevron">{openCustomization ? "▲" : "▼"}</span>
          </button>

          {openCustomization && (
            <div className="accordion-body">
              <button
                type="button"
                className="customization-row-btn"
                onClick={() => setDialog('theme')}
              >
                🔴 <span>Đổi chủ đề</span>
              </button>
              <button
                type="button"
                className="customization-row-btn"
                onClick={() => {setValue(conversation.nickname||conversation.participantName);setDialog('nickname');}}
              >
                ✏️ <span>Chỉnh sửa biệt danh</span>
              </button>
            </div>
          )}
        </div>

        {/* Accordion 2: Shared Media & Files */}
        <div className="accordion-section">
          <button
            type="button"
            className="accordion-header"
            onClick={() => setOpenMedia((prev) => !prev)}
          >
            <span>🖼️ File & Phương tiện đã chia sẻ</span>
            <span className="chevron">{openMedia ? "▲" : "▼"}</span>
          </button>

          {openMedia && (
            <div className="accordion-body">
              {/* Media Grid */}
              <div className="shared-media-subhead">Ảnh & Video</div>
              {sharedLoading ? <p className="empty-subtext">Đang tải phương tiện...</p> : sharedError ? <p className="chat-modal-error">{sharedError}</p> : sharedMedia.length === 0 ? (
                <p className="empty-subtext">Chưa có ảnh/video được chia sẻ</p>
              ) : (
                <div className="shared-media-grid">
                  {sharedMedia.map((m) => (
                    <a key={m.id} className="shared-media-thumb" href={m.url} target="_blank" rel="noreferrer" title={m.name}>
                      {m.type==='video'?<video src={m.url} muted preload="metadata"/>:<img src={safeImageSrc(m.url)} alt={m.name}/>}
                    </a>
                  ))}
                </div>
              )}

              {/* Files List */}
              <div className="shared-media-subhead" style={{ marginTop: "14px" }}>
                Tệp đính kèm ({sharedFiles.length})
              </div>
              {sharedLoading||sharedError ? null : sharedFiles.length === 0 ? (
                <p className="empty-subtext">Chưa có tài liệu được chia sẻ</p>
              ) : (
                <div className="shared-files-list">
                  {sharedFiles.map((f) => (
                    <a key={f.id} className="shared-file-item" href={f.url} target="_blank" rel="noreferrer">
                      <span className="file-icon">📄</span>
                      <div className="file-info">
                        <strong>{f.name}</strong>
                        <small>{f.size} · {f.type}</small>
                      </div>
                    </a>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Accordion 3: Privacy & Support */}
        <div className="accordion-section">
          <button
            type="button"
            className="accordion-header"
            onClick={() => setOpenPrivacy((prev) => !prev)}
          >
            <span>🔒 Quyền riêng tư & Hỗ trợ</span>
            <span className="chevron">{openPrivacy ? "▲" : "▼"}</span>
          </button>

          {openPrivacy && (
            <div className="accordion-body">
              <button
                type="button"
                className="customization-row-btn danger"
                onClick={() => setDialog('block')}
              >
                🚫 <span>Chặn người dùng</span>
              </button>
              <button
                type="button"
                className="customization-row-btn danger"
                onClick={() => {setValue("");setDialog('report');}}
              >
                ⚠️ <span>Báo cáo người dùng</span>
              </button>
            </div>
          )}
        </div>
      </div>
      {dialog&&<div className="chat-modal-backdrop chat-modal-contained" role="presentation">
        <section className="chat-modal-card compact" role="dialog" aria-modal="true">
          <header><h3>{dialog==='theme'?'Chọn chủ đề':dialog==='nickname'?'Đặt biệt danh':dialog==='block'?'Chặn người dùng':'Báo cáo vi phạm'}</h3><button type="button" onClick={()=>setDialog(null)}>✕</button></header>
          {dialog==='theme'?<div className="chat-theme-grid">{(['blue','indigo','emerald','rose','violet','amber'] as Conversation['theme'][]).map(theme=><button type="button" key={theme} className={`theme-swatch theme-${theme} ${conversation.theme===theme?'selected':''}`} aria-label={`Chủ đề ${theme}`} onClick={async()=>{setBusy(true);try{await onUpdateSettings({theme});setDialog(null);}catch(e){setError(e instanceof Error?e.message:'Không lưu được chủ đề.');}finally{setBusy(false);}}}/>)}</div>:dialog==='block'?<p>Bạn và {conversation.participantName} sẽ không thể xem hồ sơ hoặc nhắn tin cho nhau. Quan hệ bạn bè hiện tại cũng sẽ bị hủy.</p>:dialog==='report'?<textarea autoFocus value={value} onChange={e=>setValue(e.target.value)} placeholder="Mô tả hành vi vi phạm..." maxLength={3000}/>:<input autoFocus value={value} onChange={e=>setValue(e.target.value)} maxLength={100} placeholder="Nhập biệt danh..."/>}
          {error&&<p className="chat-modal-error">{error}</p>}
          {dialog!=='theme'&&<footer className="chat-modal-actions"><button type="button" onClick={()=>setDialog(null)}>Hủy</button><button type="button" className={dialog==='block'?'danger':''} disabled={busy} onClick={()=>void submit()}>{busy?'Đang xử lý...':dialog==='block'?'Xác nhận chặn':dialog==='report'?'Gửi báo cáo':'Lưu biệt danh'}</button></footer>}
        </section>
      </div>}
    </aside>
  );
}
