export interface MaintenanceState{enabled:boolean;message:string;expected_end_at:string|null}
export interface BlacklistKeyword{id:string;keyword:string;action:'BLOCK'|'REVIEW';is_active:boolean;created_at:string}
