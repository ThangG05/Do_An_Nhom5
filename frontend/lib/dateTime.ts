export type DateInput = string | number | Date | null | undefined;

function asDate(value:DateInput):Date|null{
  if(value===null||value===undefined||value==='')return null;
  const date=value instanceof Date?value:new Date(value);
  return Number.isNaN(date.getTime())?null:date;
}

export function formatRelativeTime(value:DateInput,now=Date.now()):string{
  const date=asDate(value);if(!date)return 'Không rõ thời gian';
  const seconds=Math.max(0,Math.floor((now-date.getTime())/1000));
  if(seconds<60)return 'Vừa xong';
  if(seconds<3600)return `${Math.floor(seconds/60)} phút trước`;
  if(seconds<86400)return `${Math.floor(seconds/3600)} giờ trước`;
  return new Intl.DateTimeFormat('vi-VN',{day:'2-digit',month:'2-digit',year:'numeric'}).format(date);
}

export function formatFullDateTime(value:DateInput):string{
  const date=asDate(value);if(!date)return 'Không rõ thời gian';
  return new Intl.DateTimeFormat('vi-VN',{dateStyle:'long',timeStyle:'medium'}).format(date);
}

export function formatShortDate(value:DateInput):string{
  const date=asDate(value);if(!date)return '—';
  return new Intl.DateTimeFormat('vi-VN',{day:'2-digit',month:'2-digit'}).format(date);
}
