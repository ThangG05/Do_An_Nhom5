export interface ApiReport{id:string;reporter_id:string|null;reporter_name:string;target_type:'USER'|'POST'|'COMMENT';target_id:string;reason:string;status:'PENDING'|'REVIEWING'|'RESOLVED'|'REJECTED';group_id:string|null;group_name:string|null;target_summary:string;evidence_url:string|null;resolution_note:string|null;created_at:string;handled_at:string|null}

export interface ReportDetail {
  post: import('@/types/post').Post | null;
  comment: import('@/types/post').Comment | null;
  user: { id: string; name: string; avatar: string; student_code: string | null; joined_at: string; status: string } | null;
}
