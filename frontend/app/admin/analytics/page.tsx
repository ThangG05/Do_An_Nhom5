"use client";
import {useEffect,useState} from "react";
import DashboardCharts from "@/components/admin/DashboardCharts";
import {fetchAdminDashboard} from "@/lib/api";
import type {AdminDashboard} from "@/types/admin";
export default function AdminAnalyticsPage(){const [data,setData]=useState<AdminDashboard|null>(null),[error,setError]=useState("");useEffect(()=>{fetchAdminDashboard().then(setData).catch(e=>setError(e instanceof Error?e.message:"Không tải được thống kê."));},[]);return <main className="admin-console"><header className="admin-page-heading"><div><span>ANALYTICS</span><h1>Thống kê hoạt động</h1><p>Phân tích hoạt động theo thời gian và xuất báo cáo Excel.</p></div></header>{error&&<div className="admin-error">{error}</div>}{data?<DashboardCharts dashboard={data}/>:!error&&<p className="admin-loading">Đang tải biểu đồ...</p>}</main>}
