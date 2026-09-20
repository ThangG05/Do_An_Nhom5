"use client";

import {useCallback,useEffect,useState} from "react";
import Link from "next/link";
import {fetchBlockedUsers,setUserBlocked} from "@/lib/api";
import type {UserFriend} from "@/types/user";
import {safeImageSrc} from "@/lib/media";
import {useDialog} from "@/components/ui/DialogProvider";

export default function BlockedUsersPage(){
  const dialog=useDialog();
  const [users,setUsers]=useState<UserFriend[]>([]),[loading,setLoading]=useState(true),[busy,setBusy]=useState<string|null>(null),[error,setError]=useState("");
  const load=useCallback(async()=>{setLoading(true);try{setUsers(await fetchBlockedUsers());setError("");}catch(e){setError(e instanceof Error?e.message:"Không tải được danh sách đã chặn.");}finally{setLoading(false);}},[]);
  useEffect(()=>{void load();},[load]);
  const unblock=async(user:UserFriend)=>{if(!await dialog.confirm({title:'Bỏ chặn người dùng?',message:`${user.name} có thể xem hồ sơ và kết bạn lại với bạn.`,confirmLabel:'Bỏ chặn'}))return;setBusy(user.id);try{await setUserBlocked(user.id,false);setUsers(current=>current.filter(item=>item.id!==user.id));dialog.notify({title:'Đã bỏ chặn người dùng',tone:'success'});}catch(e){setError(e instanceof Error?e.message:"Không thể bỏ chặn người dùng.");}finally{setBusy(null);}};
  return <main className="blocked-page"><section className="blocked-card">
    <header><div><span>QUYỀN RIÊNG TƯ</span><h1>Danh sách đã chặn</h1><p>Người bị chặn không thể xem hồ sơ, bài viết, kết bạn hoặc nhắn tin với bạn.</p></div><Link href="/settings/password">Đổi mật khẩu</Link></header>
    {error&&<div className="admin-error">{error}</div>}
    {loading?<p className="blocked-empty">Đang tải danh sách...</p>:users.length===0?<div className="blocked-empty"><strong>Bạn chưa chặn ai</strong><p>Các tài khoản bạn chặn sẽ xuất hiện tại đây.</p></div>:<div className="blocked-list">{users.map(user=><article key={user.id}><img src={safeImageSrc(user.avatar)} alt=""/><div><strong>{user.name}</strong><p>@{user.username}{user.faculty?` · ${user.faculty}`:""}</p></div><button disabled={busy===user.id} onClick={()=>void unblock(user)}>{busy===user.id?'Đang xử lý...':'Bỏ chặn'}</button></article>)}</div>}
  </section></main>;
}
