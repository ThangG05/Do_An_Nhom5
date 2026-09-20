"use client";

import {useEffect,useState} from 'react';
import {DateInput,formatFullDateTime,formatRelativeTime} from '@/lib/dateTime';

export default function RelativeTime({value,className,prefix=''}:{value:DateInput;className?:string;prefix?:string}){
  const [now,setNow]=useState(()=>Date.now());
  useEffect(()=>{const timer=window.setInterval(()=>setNow(Date.now()),60000);return()=>window.clearInterval(timer);},[]);
  const date=value instanceof Date?value:new Date(value??'');
  return <time suppressHydrationWarning className={className} dateTime={Number.isNaN(date.getTime())?undefined:date.toISOString()} title={formatFullDateTime(value)}>{prefix}{formatRelativeTime(value,now)}</time>;
}
