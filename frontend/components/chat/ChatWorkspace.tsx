"use client";

import React, { useState, useRef, useEffect } from "react";
import { Conversation, Message, RealtimeCallEvent } from "@/types/message";
import { safeImageSrc } from "@/lib/media";
import { searchConversationMessages } from "@/lib/api";
import RelativeTime from "@/components/ui/RelativeTime";

interface ChatWorkspaceProps {
  activeConversation: Conversation;
  messages: Message[];
  currentUserId: string;
  onSendMessage: (text: string, file?: File) => Promise<void>;
  onToggleDetailsPanel: () => void;
  showDetailsPanel: boolean;
  onBackMobile: () => void;
  realtimeEvent: RealtimeCallEvent | null;
  onSignal: (payload:Record<string,unknown>) => void;
  searchOpen: boolean;
  onCloseSearch: () => void;
}

export default function ChatWorkspace({
  activeConversation,
  messages,
  currentUserId,
  onSendMessage,
  onToggleDetailsPanel,
  showDetailsPanel,
  onBackMobile,
  realtimeEvent,
  onSignal,
  searchOpen,
  onCloseSearch,
}: ChatWorkspaceProps) {
  const [inputText, setInputText] = useState("");
  const [searchQuery,setSearchQuery]=useState(""),[searchResults,setSearchResults]=useState<Message[]|null>(null);
  const [call,setCall]=useState<{status:'incoming'|'calling'|'active';video:boolean;error?:string}|null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const peerRef=useRef<RTCPeerConnection|null>(null),localStreamRef=useRef<MediaStream|null>(null),remoteStreamRef=useRef<MediaStream|null>(null),pendingOfferRef=useRef<RTCSessionDescriptionInit|null>(null),pendingIceRef=useRef<RTCIceCandidateInit[]>([]),localVideoRef=useRef<HTMLVideoElement>(null),remoteVideoRef=useRef<HTMLVideoElement>(null),remoteAudioRef=useRef<HTMLAudioElement>(null);

  useEffect(()=>{if(!searchOpen){setSearchQuery("");setSearchResults(null);return;}const term=searchQuery.trim();if(!term){setSearchResults(null);return;}const timer=window.setTimeout(()=>{void searchConversationMessages(activeConversation.id,term).then(setSearchResults).catch(()=>setSearchResults([]));},250);return()=>window.clearTimeout(timer);},[searchOpen,searchQuery,activeConversation.id]);

  const stopStreams=()=>{localStreamRef.current?.getTracks().forEach(track=>track.stop());remoteStreamRef.current?.getTracks().forEach(track=>track.stop());localStreamRef.current=null;remoteStreamRef.current=null;peerRef.current?.close();peerRef.current=null;pendingOfferRef.current=null;pendingIceRef.current=[];};
  const finishCall=(notify=true,reason='ended')=>{if(notify){try{onSignal({event:'call.end',conversation_id:activeConversation.id,reason});}catch{/* socket already closed */}}stopStreams();setCall(null);};
  const createPeer=(stream:MediaStream)=>{const peer=new RTCPeerConnection({iceServers:[{urls:'stun:stun.l.google.com:19302'},{urls:'stun:stun1.l.google.com:19302'}]});stream.getTracks().forEach(track=>peer.addTrack(track,stream));peer.onicecandidate=event=>{if(event.candidate)onSignal({event:'call.ice',conversation_id:activeConversation.id,candidate:event.candidate.toJSON()});};peer.ontrack=event=>{const stream=event.streams[0]||new MediaStream([event.track]);remoteStreamRef.current=stream;if(remoteVideoRef.current)remoteVideoRef.current.srcObject=stream;if(remoteAudioRef.current)remoteAudioRef.current.srcObject=stream;};peer.onconnectionstatechange=()=>{if(peer.connectionState==='connected')setCall(current=>current?{...current,status:'active'}:current);if(['failed','closed'].includes(peer.connectionState))finishCall(false,'connection_failed');};peerRef.current=peer;return peer;};
  const getMedia=async(video:boolean)=>{if(!navigator.mediaDevices?.getUserMedia)throw new Error('Trình duyệt không hỗ trợ gọi thoại/video.');const stream=await navigator.mediaDevices.getUserMedia({audio:true,video});localStreamRef.current=stream;return stream;};
  const startCall=async(video:boolean)=>{try{setCall({status:'calling',video});const stream=await getMedia(video);const peer=createPeer(stream);const offer=await peer.createOffer();await peer.setLocalDescription(offer);onSignal({event:'call.offer',conversation_id:activeConversation.id,sdp:offer,video});}catch(e){stopStreams();setCall({status:'calling',video,error:e instanceof Error?e.message:'Không thể bắt đầu cuộc gọi.'});}};
  const acceptCall=async()=>{if(!call||!pendingOfferRef.current)return;try{const stream=await getMedia(call.video);const peer=createPeer(stream);await peer.setRemoteDescription(pendingOfferRef.current);for(const candidate of pendingIceRef.current)await peer.addIceCandidate(candidate);pendingIceRef.current=[];const answer=await peer.createAnswer();await peer.setLocalDescription(answer);onSignal({event:'call.answer',conversation_id:activeConversation.id,sdp:answer});setCall({...call,status:'active'});}catch(e){setCall({...call,error:e instanceof Error?e.message:'Không thể nhận cuộc gọi.'});}};
  useEffect(()=>{if(!realtimeEvent||realtimeEvent.conversation_id!==activeConversation.id)return;if(realtimeEvent.event==='call.offer'&&realtimeEvent.sdp){pendingOfferRef.current=realtimeEvent.sdp;setCall({status:'incoming',video:!!realtimeEvent.video});}else if(realtimeEvent.event==='call.answer'&&realtimeEvent.sdp&&peerRef.current){void peerRef.current.setRemoteDescription(realtimeEvent.sdp).then(async()=>{for(const candidate of pendingIceRef.current)await peerRef.current?.addIceCandidate(candidate);pendingIceRef.current=[];});}else if(realtimeEvent.event==='call.ice'&&realtimeEvent.candidate){if(peerRef.current?.remoteDescription)void peerRef.current.addIceCandidate(realtimeEvent.candidate);else pendingIceRef.current.push(realtimeEvent.candidate);}else if(realtimeEvent.event==='call.end'){finishCall(false,realtimeEvent.reason);}},[realtimeEvent?.sequence]);
  useEffect(()=>()=>stopStreams(),[]);
  useEffect(()=>{if(localVideoRef.current)localVideoRef.current.srcObject=localStreamRef.current;if(remoteVideoRef.current)remoteVideoRef.current.srcObject=remoteStreamRef.current;if(remoteAudioRef.current)remoteAudioRef.current.srcObject=remoteStreamRef.current;},[call?.status]);

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!inputText.trim()) return;
    await onSendMessage(inputText);
    setInputText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      void onSendMessage('', file);
    }
  };

  return (
    <main className={`messenger-center-panel chat-theme-${activeConversation.theme||'blue'}`} aria-label="Khung trò chuyện">
      {/* Header Bar */}
      <div className="chat-workspace-header">
        <div className="header-left-info">
          {/* Mobile Back Button */}
          <button
            type="button"
            className="mobile-back-btn"
            onClick={onBackMobile}
            aria-label="Quay lại danh sách tin nhắn"
          >
            ←
          </button>

          <div className="header-avatar-wrap">
            <div className="participant-avatar">{activeConversation.participantAvatar.startsWith('/') || activeConversation.participantAvatar.startsWith('http') ? <img src={safeImageSrc(activeConversation.participantAvatar)} alt={activeConversation.participantName} /> : activeConversation.participantAvatar}</div>
            <span
              className={`online-status-dot ${
                activeConversation.isOnline ? "online" : "offline"
              }`}
            />
          </div>

          <div className="header-text-meta">
            <strong className="recipient-name">
              {activeConversation.participantName}
            </strong>
            <span className="recipient-status">
              {activeConversation.isOnline
                ? "🟢 Đang hoạt động"
                : activeConversation.lastActive || "Ngoại tuyến"}
            </span>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="header-actions">
          <button
            type="button"
            className="chat-action-btn"
            title="Bắt đầu cuộc gọi thoại"
            onClick={() => void startCall(false)}
          >
            📞
          </button>
          <button
            type="button"
            className="chat-action-btn"
            title="Bắt đầu cuộc gọi video"
            onClick={() => void startCall(true)}
          >
            📹
          </button>
          <button
            type="button"
            className={`chat-action-btn ${showDetailsPanel ? "active" : ""}`}
            title="Thông tin cuộc trò chuyện"
            onClick={onToggleDetailsPanel}
          >
            ℹ️
          </button>
        </div>
      </div>

      {searchOpen&&<div className="conversation-search-bar"><span>⌕</span><input autoFocus value={searchQuery} onChange={e=>setSearchQuery(e.target.value)} placeholder="Tìm nội dung tin nhắn..."/><small>{searchResults?`${searchResults.length} kết quả`:''}</small><button type="button" onClick={onCloseSearch}>✕</button></div>}

      {/* Messages Scroll Area */}
      <div className="messages-scroll-area">
        <div className="time-divider">
          <span>HÔM NAY · HVNH HUB MESSENGER</span>
        </div>

        {(searchResults??messages).map((msg) => {
          const isMe = msg.senderId === currentUserId;

          return (
            <div
              key={msg.id}
              className={`message-bubble-row ${isMe ? "outgoing" : "incoming"}`}
            >
              {!isMe && (
                <div className="message-sender-avatar">{msg.senderAvatar}</div>
              )}

              <div className="bubble-content-wrap">
                <div className={`chat-bubble ${isMe ? "me" : "them"}`}>
                  <p>{msg.content}</p>
                  {msg.attachments && msg.attachments.length > 0 && (
                    <div className="attachment-preview">
                      {msg.attachments[0].type==='image'?<img src={safeImageSrc(msg.attachments[0].url)} alt="Tệp đính kèm" />:msg.attachments[0].type==='video'?<video src={msg.attachments[0].url} controls />:msg.attachments[0].type==='audio'?<audio src={msg.attachments[0].url} controls />:<a href={msg.attachments[0].url}>{msg.attachments[0].name}</a>}
                    </div>
                  )}
                </div>

                <div className="message-meta-sub">
                  <RelativeTime className="msg-time" value={msg.timestamp}/>
                  {isMe && (
                    <span className="msg-status-text">
                      {msg.status === "seen"
                        ? "✓✓ Đã xem"
                        : msg.status === "delivered"
                        ? "✓✓ Đã nhận"
                        : "✓ Đã gửi"}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        <div ref={messagesEndRef} />
      </div>

      {call&&<div className="call-overlay" role="dialog" aria-modal="true" aria-label="Cuộc gọi">
        <div className="call-stage">
          {call.video?<><video ref={remoteVideoRef} autoPlay playsInline className="call-remote-video"/><video ref={localVideoRef} autoPlay muted playsInline className="call-local-video"/></>:<><div className="call-audio-avatar"><img src={safeImageSrc(activeConversation.participantAvatar)} alt=""/></div><audio ref={remoteAudioRef} autoPlay/></>}
          <h3>{activeConversation.participantName}</h3><p>{call.error|| (call.status==='incoming'?'đang gọi cho bạn':call.status==='calling'?'Đang kết nối...':'Đã kết nối')}</p>
          <div className="call-actions">{call.status==='incoming'&&<button type="button" className="call-accept" onClick={()=>void acceptCall()}>Nhận cuộc gọi</button>}<button type="button" className="call-end" onClick={()=>finishCall(true,call.status==='incoming'?'rejected':'ended')}>{call.status==='incoming'?'Từ chối':'Kết thúc'}</button></div>
        </div>
      </div>}

      {/* Input Toolbar */}
      <div className="chat-input-toolbar">
        <div className="toolbar-left-tools">
          <button
            type="button"
            className="tool-btn"
            title="Đính kèm ảnh"
            onClick={() => fileInputRef.current?.click()}
          >
            🖼️
          </button>
          <button
            type="button"
            className="tool-btn"
            title="Đính kèm tệp"
            onClick={() => fileInputRef.current?.click()}
          >
            📎
          </button>
          <button
            type="button"
            className="tool-btn"
            title="Biểu tượng cảm xúc"
            onClick={() => setInputText((prev) => prev + " 😊")}
          >
            😊
          </button>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,video/mp4,video/webm,video/quicktime,audio/mpeg,audio/mp4,audio/ogg,audio/wav,audio/webm,application/pdf,text/plain,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.zip"
          style={{ display: "none" }}
          onChange={handleFileSelect}
        />

        <div className="input-field-wrap">
          <input
            type="text"
            className="chat-text-input"
            placeholder="Nhập tin nhắn..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>

        <button
          type="button"
          className="send-message-btn"
          disabled={!inputText.trim()}
          onClick={handleSend}
          title="Gửi tin nhắn"
        >
          ➤
        </button>
      </div>
    </main>
  );
}
