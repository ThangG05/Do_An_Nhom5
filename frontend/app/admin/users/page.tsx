"use client";
import {useCallback,useEffect,useState} from "react";
import DisciplineActions from "@/components/admin/DisciplineActions";
import {fetchAdminUsers,fetchGroups,setUserGroupAdmin} from "@/lib/api";
import type {AdminUser} from "@/types/admin";
import type {ApiGroup} from "@/types/group-api";
import type {RagPeriod} from "@/types/admin";
import RagTokenSummary from "@/components/admin/RagTokenSummary";

export default function AdminUsersPage(){
 const [users,setUsers]=useState<AdminUser[]>([]),[groups,setGroups]=useState<ApiGroup[]>([]),[q,setQ]=useState(""),[status,setStatus]=useState(""),[loading,setLoading]=useState(true),[error,setError]=useState("");
 const [period,setPeriod]=useState<RagPeriod>("30d"),[startDate,setStartDate]=useState(""),[endDate,setEndDate]=useState("");
 const validPeriod=period!=="custom"||Boolean(startDate&&endDate&&startDate<=endDate);
 const load=useCallback(async()=>{if(!validPeriod){setLoading(false);return;}setLoading(true);try{const u=await fetchAdminUsers(q,status,period,startDate,endDate);setUsers(u.items);setError("");}catch(e){setError(e instanceof Error?e.message:"Không tải được tài khoản.");}finally{setLoading(false);}},[q,status,period,startDate,endDate,validPeriod]);
 useEffect(()=>{void fetchGroups().then(rows=>setGroups(rows.filter(x=>["pass-do","ghep-phong-tim-tro","su-kien","hoc-tap"].includes(x.slug))),e=>setError(e instanceof Error?e.message:"Không tải được nhóm."));},[]);
 useEffect(()=>{const timer=setTimeout(()=>void load(),250);return()=>clearTimeout(timer);},[load]);
 const toggleGroup=async(user:AdminUser,group:ApiGroup)=>{await setUserGroupAdmin(user.id,group.id,!user.admin_groups.some(x=>x.id===group.id));await load();};
 return <main className="admin-console"><header className="admin-page-heading"><div><span>ACCOUNT MANAGEMENT</span><h1>Tài khoản và phân quyền</h1><p>Tra cứu, gán Group Admin và xử lý kỷ luật người dùng.</p></div></header>{error&&<div className="admin-error">{error}</div>}
 <section className="admin-users"><header><div><h2>Danh sách tài khoản</h2><p>Mỗi thay đổi được ghi vào nhật ký quản trị.</p></div><div><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Tên, mã SV, email, khoa..."/><select value={status} onChange={e=>setStatus(e.target.value)}><option value="">Mọi trạng thái</option><option value="ACTIVE">Hoạt động</option><option value="LOCKED">Tạm khóa</option><option value="DISABLED">Khóa vĩnh viễn</option></select></div></header>
 <div className="admin-rag-period"><strong>Token RAG</strong><select value={period} onChange={e=>setPeriod(e.target.value as RagPeriod)} aria-label="Khoảng thời gian token"><option value="today">Hôm nay</option><option value="7d">7 ngày</option><option value="30d">30 ngày</option><option value="custom">Tùy chọn</option><option value="all">Toàn thời gian</option></select>{period==="custom"&&<><input type="date" value={startDate} onChange={e=>setStartDate(e.target.value)} aria-label="Từ ngày"/><span>đến</span><input type="date" value={endDate} onChange={e=>setEndDate(e.target.value)} aria-label="Đến ngày"/></>}{!validPeriod&&<small>Chọn khoảng ngày hợp lệ.</small>}</div>
 {loading?<p className="admin-loading">Đang tải dữ liệu...</p>:<div className="admin-user-list">{users.map(user=><article key={user.id}><div className="admin-user-main"><div className="admin-avatar">{user.full_name.slice(0,1).toUpperCase()}</div><div><strong>{user.full_name}</strong><p>{user.email} · @{user.username}</p><small>{user.student_code||"Chưa có mã SV"}{user.faculty?` · ${user.faculty}`:""}</small></div><span className={`admin-status ${user.status.toLowerCase()}`}>{user.status}</span></div><RagTokenSummary user={user} period={period} startDate={startDate} endDate={endDate}/><div className="admin-role-row"><b>Quản trị nhóm:</b>{groups.map(group=><button disabled={user.system_role==="SUPER_ADMIN"} className={user.admin_groups.some(x=>x.id===group.id)?"selected":""} key={group.id} onClick={()=>void toggleGroup(user,group)}>{group.name}</button>)}</div><div className="admin-account-actions">{user.system_role==="SUPER_ADMIN"?<span>SUPER ADMIN</span>:<DisciplineActions user={user} onDone={load}/>}</div></article>)}{!users.length&&<p className="admin-loading">Không tìm thấy tài khoản.</p>}</div>}</section></main>;
}
