"use client";

import Link from "next/link";
import {usePathname,useRouter} from "next/navigation";
import {useEffect,useState} from "react";
import {getAuthUser,logoutSession,type AuthUser} from "@/lib/auth";
import "./admin-shell.css";

const sections=[
  {href:"/admin",label:"Tổng quan",icon:"▦"},
  {href:"/admin/analytics",label:"Thống kê",icon:"⌁"},
  {href:"/admin/groups",label:"Quản lý nhóm",icon:"◉"},
  {href:"/admin/users",label:"Tài khoản",icon:"♙"},
  {href:"/admin/reports",label:"Báo cáo vi phạm",icon:"!"},
  {href:"/admin/audit",label:"Nhật ký quản trị",icon:"≡"},
  {href:"/admin/settings",label:"Cấu hình hệ thống",icon:"⚙"},
];

export default function AdminLayout({children}:{children:React.ReactNode}){
  const pathname=usePathname(),router=useRouter();
  const [user,setUser]=useState<AuthUser|null>(null),[open,setOpen]=useState(false),[ready,setReady]=useState(false),[accountOpen,setAccountOpen]=useState(false);
  useEffect(()=>{setUser(getAuthUser());setReady(true);},[pathname]);
  const signOut=async()=>{await logoutSession();router.replace('/login');};
  if(!ready)return <div className="admin-shell-loading">Đang kiểm tra quyền quản trị...</div>;
  if(!user||user.system_role!=="SUPER_ADMIN")return <main className="admin-access-denied"><section><h1>Không có quyền truy cập</h1><p>Khu vực này chỉ dành cho Super Admin.</p><Link href="/home">Trở về trang chủ</Link></section></main>;
  return <div className="admin-shell">
    <aside className={open?"admin-sidebar open":"admin-sidebar"}>
      <Link href="/admin" className="admin-brand" onClick={()=>setOpen(false)}><img src="/assets/logo.png" alt=""/><div><strong>HVNH HUB</strong><small>SUPER ADMIN</small></div></Link>
      <div className="admin-side-label">QUẢN TRỊ HỆ THỐNG</div>
      <nav>{sections.map(item=>{const active=item.href==="/admin"?pathname==="/admin":pathname.startsWith(item.href);return <Link className={active?"active":""} aria-current={active?"page":undefined} key={item.href} href={item.href} onClick={()=>setOpen(false)}><i>{item.icon}</i><span>{item.label}</span></Link>;})}</nav>
      <div className="admin-side-footer"><button onClick={()=>void signOut()}>Đăng xuất</button></div>
    </aside>
    {open&&<button className="admin-sidebar-backdrop" aria-label="Đóng menu" onClick={()=>setOpen(false)}/>} 
    <div className="admin-workspace">
      <header className="admin-topbar"><button className="admin-menu-toggle" onClick={()=>setOpen(true)}>☰</button><div><span>TRUNG TÂM ĐIỀU HÀNH</span><strong>{sections.find(item=>item.href==="/admin"?pathname==="/admin":pathname.startsWith(item.href))?.label||"Quản trị hệ thống"}</strong></div><div className="admin-account-wrap"><button className="admin-identity" onClick={()=>setAccountOpen(value=>!value)} aria-expanded={accountOpen} aria-label="Mở menu tài khoản quản trị"><div><strong>{user.full_name||'Super Admin'}</strong><small>{user.email}</small></div>{user.avatar_url?<img src={user.avatar_url} alt=""/>:<span className="admin-identity-initial">{(user.full_name||'A').slice(0,1).toUpperCase()}</span>}</button>{accountOpen&&<div className="admin-account-menu"><div className="admin-account-summary">{user.avatar_url?<img src={user.avatar_url} alt=""/>:<span className="admin-identity-initial">{(user.full_name||'A').slice(0,1).toUpperCase()}</span>}<div><strong>{user.full_name||'Super Admin'}</strong><span>{user.email}</span><small>SUPER ADMIN</small></div></div><nav><Link href="/admin" onClick={()=>setAccountOpen(false)}><i>▦</i><span><b>Trung tâm quản trị</b><small>Về trang tổng quan</small></span></Link><Link href="/admin/audit" onClick={()=>setAccountOpen(false)}><i>≡</i><span><b>Nhật ký hoạt động</b><small>Xem lịch sử quản trị</small></span></Link><Link href="/admin/settings" onClick={()=>setAccountOpen(false)}><i>⚙</i><span><b>Cài đặt hệ thống</b><small>Bảo trì và kiểm duyệt</small></span></Link></nav><button className="admin-menu-logout" onClick={()=>void signOut()}><i>↪</i> Đăng xuất</button></div>}</div></header>
      <div className="admin-workspace-content">{children}</div>
    </div>
  </div>;
}
