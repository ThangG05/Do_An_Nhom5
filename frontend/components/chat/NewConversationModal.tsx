"use client";

import { useEffect, useState } from "react";
import { searchUsers, UserSearchResult } from "@/lib/api";
import { safeImageSrc } from "@/lib/media";

export default function NewConversationModal({onClose,onStart}:{onClose:()=>void;onStart:(userId:string)=>Promise<unknown>}){
  const [query,setQuery]=useState(""),[results,setResults]=useState<UserSearchResult[]>([]),[loading,setLoading]=useState(false),[busy,setBusy]=useState(""),[error,setError]=useState("");
  useEffect(()=>{const value=query.trim();if(value.length<2){setResults([]);return;}const timer=window.setTimeout(()=>{setLoading(true);setError("");void searchUsers(value).then(rows=>setResults(rows.filter(row=>row.friendshipStatus==='friends'))).catch(e=>setError(e instanceof Error?e.message:"Không thể tìm sinh viên.")).finally(()=>setLoading(false));},300);return()=>window.clearTimeout(timer);},[query]);
  return <div className="chat-modal-backdrop" role="presentation" onMouseDown={e=>{if(e.target===e.currentTarget)onClose();}}>
    <section className="chat-modal-card" role="dialog" aria-modal="true" aria-labelledby="new-chat-title">
      <header><div><small>TIN NHẮN MỚI</small><h3 id="new-chat-title">Chọn người bạn muốn nhắn tin</h3></div><button type="button" onClick={onClose} aria-label="Đóng">✕</button></header>
      <label className="chat-modal-search"><span>⌕</span><input autoFocus value={query} onChange={e=>setQuery(e.target.value)} placeholder="Nhập tên hoặc mã sinh viên..."/></label>
      {error&&<p className="chat-modal-error">{error}</p>}
      <div className="chat-user-results">
        {loading&&<p>Đang tìm kiếm...</p>}
        {!loading&&query.trim().length>=2&&!results.length&&!error&&<p>Không tìm thấy bạn bè phù hợp.</p>}
        {results.map(user=><button type="button" key={user.id} disabled={!!busy} onClick={async()=>{setBusy(user.id);setError("");try{await onStart(user.id);onClose();}catch(e){setError(e instanceof Error?e.message:"Không thể bắt đầu cuộc trò chuyện.");}finally{setBusy("");}}}>
          <img src={safeImageSrc(user.avatar)} alt=""/><span><strong>{user.name}</strong><small>@{user.username}{user.faculty?` · ${user.faculty}`:""}</small></span><b>{busy===user.id?'Đang mở...':'Nhắn tin'}</b>
        </button>)}
      </div>
      <footer>Vì quyền riêng tư, bạn chỉ có thể bắt đầu trò chuyện với bạn bè.</footer>
    </section>
  </div>;
}
