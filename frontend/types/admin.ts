export interface AdminGroupStat { id:string;name:string;slug:string;members:number;approved_posts:number;pending_posts:number }
export interface AdminActivityPoint { date:string;new_users:number;posts:number;messages:number }
export interface AdminDashboard { total_users:number;active_users:number;locked_users:number;disabled_users:number;pending_posts:number;approved_posts:number;rejected_posts:number;total_likes:number;total_comments:number;total_messages:number;groups:AdminGroupStat[];activity:AdminActivityPoint[] }
export interface AdminGroupRef { id:string;name:string;slug:string }
export interface AdminUser { id:string;email:string;username:string;full_name:string;student_code:string|null;faculty:string|null;status:'PENDING'|'ACTIVE'|'LOCKED'|'DISABLED';system_role:'USER'|'SUPER_ADMIN';admin_groups:AdminGroupRef[];created_at:string;last_login_at:string|null;suspended_until:string|null;warning_count:number }
export interface AdminUserPage { items:AdminUser[];total:number;limit:number;offset:number }
export interface AdminAuditLog{id:string;actor_name:string;action:string;target_type:string;target_id:string|null;metadata:Record<string,unknown>;created_at:string}
