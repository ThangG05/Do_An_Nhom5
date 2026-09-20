"use client";
import {useCallback,useEffect,useState} from "react";
import {fetchReportQueue,resolveReport} from "@/lib/api";
import {getAuthUser} from "@/lib/auth";
import type {ApiReport} from "@/types/report";
import {useDialog} from "@/components/ui/DialogProvider";

export default function ReportQueue({groupId}:{groupId?:string}){
 const [items,setItems]=useState<ApiReport[]>([]),[error,setError]=useState("");
 const dialog=useDialog();
 const load=useCallback(async()=>{try{const rows=await fetchReportQueue('PENDING');setItems(groupId?rows.filter(r=>r.group_id===groupId):rows);setError("");}catch(e){setError(e instanceof Error?e.message:"Không tải được báo cáo.");}},[groupId]);
 useEffect(()=>{void load();},[load]);
 const decide=async(item:ApiReport,decision:'RESOLVE'|'REJECT',action:'NONE'|'HIDE_CONTENT'|'LOCK_USER'|'DISABLE_USER')=>{const note=await dialog.prompt({title:decision==='REJECT'?'Bác bỏ báo cáo':'Xác nhận xử lý',message:'Ghi rõ kết quả và căn cứ để người báo cáo có thể theo dõi.',placeholder:'Ghi chú kết quả xử lý...',multiline:true,minLength:3,tone:action==='DISABLE_USER'?'danger':'default'});if(!note)return;try{await resolveReport(item.id,decision,action,note);await load();dialog.notify({title:'Đã xử lý báo cáo',tone:'success'});}catch(e){setError(e instanceof Error?e.message:"Không xử lý được báo cáo.");}};
 const superAdmin=getAuthUser()?.system_role==='SUPER_ADMIN';
 return <section className="report-queue"><header><div><span>REPORT MANAGEMENT</span><h2>Báo cáo vi phạm</h2></div><b>{items.length} đang chờ</b></header>{error&&<div className="admin-error">{error}</div>}<div className="report-list">{items.map(item=><article key={item.id}><div className="report-copy"><div><span className="report-type">{item.target_type}</span>{item.group_name&&<span className="report-group">{item.group_name}</span>}</div><strong>{item.reporter_name} đã báo cáo</strong><p className="report-reason">{item.reason}</p><blockquote>{item.target_summary||"Đối tượng không còn hiển thị"}</blockquote>{item.evidence_url&&<a href={item.evidence_url} target="_blank" rel="noreferrer">Xem minh chứng</a>}</div><div className="report-actions"><button onClick={()=>void decide(item,'REJECT','NONE')}>Bác bỏ</button>{item.target_type!=="USER"&&<button className="warning" onClick={()=>void decide(item,'RESOLVE','HIDE_CONTENT')}>Xác nhận & gỡ nội dung</button>}{superAdmin&&item.target_type==="USER"&&<><button className="warning" onClick={()=>void decide(item,'RESOLVE','LOCK_USER')}>Xác nhận & khóa</button><button className="danger" onClick={()=>void decide(item,'RESOLVE','DISABLE_USER')}>Vô hiệu hóa</button></>}</div></article>)}{!items.length&&!error&&<p className="live-empty">Không có báo cáo đang chờ xử lý.</p>}</div></section>;
}
