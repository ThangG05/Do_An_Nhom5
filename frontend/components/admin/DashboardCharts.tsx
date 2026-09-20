"use client";

import {useState} from "react";
import {exportAdminDashboard} from "@/lib/api";
import type {AdminDashboard} from "@/types/admin";
import {formatShortDate} from "@/lib/dateTime";

export default function DashboardCharts({dashboard}:{dashboard:AdminDashboard}){
  const [exporting,setExporting]=useState(false);
  const max=Math.max(1,...dashboard.activity.flatMap(item=>[item.new_users,item.posts,item.messages]));
  const exportFile=async()=>{setExporting(true);try{await exportAdminDashboard();}finally{setExporting(false);}};
  return <section className="admin-charts" id="activity">
    <header><div><h2>Hoạt động 14 ngày gần nhất</h2><p>Người dùng mới, bài viết và tin nhắn theo ngày.</p></div><button type="button" disabled={exporting} onClick={()=>void exportFile()}>{exporting?'Đang tạo Excel...':'Xuất báo cáo Excel'}</button></header>
    <div className="admin-chart-legend"><span className="users">Người dùng mới</span><span className="posts">Bài viết</span><span className="messages">Tin nhắn</span></div>
    <div className="admin-bar-chart" role="img" aria-label="Biểu đồ hoạt động 14 ngày">
      {dashboard.activity.map(item=><div className="admin-chart-day" key={item.date} title={`${item.date}: ${item.new_users} người dùng, ${item.posts} bài viết, ${item.messages} tin nhắn`}>
        <div className="admin-bars"><i className="users" style={{height:`${Math.max(2,item.new_users/max*100)}%`}}/><i className="posts" style={{height:`${Math.max(2,item.posts/max*100)}%`}}/><i className="messages" style={{height:`${Math.max(2,item.messages/max*100)}%`}}/></div>
        <small title={item.date}>{formatShortDate(`${item.date}T00:00:00`)}</small>
      </div>)}
    </div>
  </section>;
}
