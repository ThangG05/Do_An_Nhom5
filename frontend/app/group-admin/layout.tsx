"use client";
import Link from "next/link";
import {usePathname,useRouter} from "next/navigation";
import {useEffect,useState} from "react";
import {getAuthUser,logoutSession,type AuthUser} from "@/lib/auth";
import "../admin/admin-shell.css";
import "./group-admin-shell.css";
import "./hide-account-link.css";
import "./group-admin-fixes.css";
import "./member-ui.css";
import "./member-alignment.css";

export default function GroupAdminLayout({children}:{children:React.ReactNode}){
  const pathname=usePathname(),router=useRouter();
  const [user,setUser]=useState<AuthUser|null>(null),[ready,setReady]=useState(false),[accountOpen,setAccountOpen]=useState(false);
  useEffect(()=>{setUser(getAuthUser());setReady(true);},[pathname]);
  if(!ready)return <div className="admin-shell-loading">Đang kiểm tra quyền quản trị nhóm...</div>;
  const allowed=!!user&&(user.system_role==='SUPER_ADMIN'||user.admin_group_slugs.length>0);
  if(!allowed)return <main className="admin-access-denied"><section><h1>Không có quyền truy cập</h1><p>Khu vực này chỉ dành cho Group Admin.</p><Link href="/groups">Trở về hội nhóm</Link></section></main>;
  const signOut=async()=>{await logoutSession();router.replace('/login');};
  return <div className="admin-shell group-admin-shell">
    <div className="admin-workspace"><header className="admin-topbar"><Link href="/group-admin" className="group-admin-top-brand"><img src="/assets/logo.png" alt="HVNH Hub"/><strong>HVNH Hub</strong></Link><div className="group-admin-top-title"><span>TRUNG TÂM ĐIỀU HÀNH NHÓM</span><strong>Quản trị nhóm</strong></div><div className="group-admin-account-wrap"><button className="admin-identity" onClick={()=>setAccountOpen(value=>!value)} aria-expanded={accountOpen}><div><strong>{user.full_name||'Group Admin'}</strong><small>{user.email}</small></div>{user.avatar_url?<img src={user.avatar_url} alt=""/>:<span className="admin-identity-initial">{(user.full_name||'A').slice(0,1).toUpperCase()}</span>}</button>{accountOpen&&<div className="group-admin-account-menu"><strong>{user.full_name||'Group Admin'}</strong><span>{user.email}</span><Link href="/groups">Về hội nhóm</Link><button onClick={()=>void signOut()}>Đăng xuất</button></div>}</div></header><div className="admin-workspace-content">{children}</div></div>
  </div>;
}
