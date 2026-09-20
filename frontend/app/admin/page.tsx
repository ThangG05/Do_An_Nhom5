"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import {fetchAdminDashboard} from "@/lib/api";
import type {AdminDashboard} from "@/types/admin";

export default function AdminOverviewPage(){
 const [dashboard,setDashboard]=useState<AdminDashboard|null>(null),[error,setError]=useState("");
 useEffect(()=>{fetchAdminDashboard().then(setDashboard).catch(e=>setError(e instanceof Error?e.message:"Không tải được tổng quan."));},[]);
 const cards=dashboard?[["Người dùng",dashboard.total_users],["Đang hoạt động",dashboard.active_users],["Bị khóa",dashboard.locked_users],["Bài chờ duyệt",dashboard.pending_posts],["Bài đã duyệt",dashboard.approved_posts],["Tin nhắn",dashboard.total_messages]]:[];
 return <main className="admin-console"><header className="admin-page-heading"><div><span>DASHBOARD</span><h1>Tổng quan hệ thống</h1><p>Theo dõi nhanh tình trạng vận hành và chuyển tới module cần xử lý.</p></div></header>{error&&<div className="admin-error">{error}</div>}
 <section className="admin-metric-grid admin-overview-metrics">{cards.map(([label,value])=><article key={label}><small>{label}</small><strong>{value}</strong></article>)}</section>
 <section className="admin-module-grid"><Link href="/admin/users"><b>Quản lý tài khoản</b><span>Tra cứu, phân quyền và xử lý tài khoản</span></Link><Link href="/admin/reports"><b>Báo cáo vi phạm</b><span>Xem và giải quyết nội dung bị báo cáo</span></Link><Link href="/admin/groups"><b>Quản lý nhóm</b><span>Theo dõi hoạt động các nhóm chuyên môn</span></Link><Link href="/admin/analytics"><b>Thống kê</b><span>Biểu đồ hoạt động và xuất Excel</span></Link><Link href="/admin/audit"><b>Nhật ký quản trị</b><span>Kiểm tra lịch sử thao tác quản trị</span></Link><Link href="/admin/settings"><b>Cấu hình hệ thống</b><span>Bảo trì và từ khóa kiểm duyệt</span></Link></section>
 </main>;
}
