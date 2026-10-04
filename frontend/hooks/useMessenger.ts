"use client";
import {useCallback,useEffect,useMemo,useRef,useState} from "react";
import {useSearchParams} from "next/navigation";
import {Conversation,Message,RealtimeCallEvent} from "@/types/message";
import {createDirectConversation,fetchConversations,fetchMessages,sendChatMessage,updateConversationSettings} from "@/lib/api";
import {getAuthUser} from "@/lib/auth";
import {useRealtime} from "@/components/realtime/RealtimeProvider";

export function useMessenger(){
 const [conversations,setConversations]=useState<Conversation[]>([]),[activeId,setActiveId]=useState(""),[messagesMap,setMessagesMap]=useState<Record<string,Message[]>>({}),[searchQuery,setSearchQuery]=useState(""),[showDetailsPanel,setShowDetailsPanel]=useState(true),[mobileView,setMobileView]=useState<"list"|"chat">("list");
 const [currentUserId,setCurrentUserId]=useState(""),[realtimeEvent,setRealtimeEvent]=useState<RealtimeCallEvent|null>(null);const params=useSearchParams();const sequenceRef=useRef(0);const {send:sendRealtime}=useRealtime();
 const loadConversations=useCallback(async()=>{const rows=await fetchConversations();setConversations(rows);setActiveId(id=>id||rows[0]?.id||"");return rows;},[]);
 useEffect(()=>{setCurrentUserId(getAuthUser()?.id||"");void (async()=>{const target=params.get('userId'),requested=params.get('conversationId');if(target){const conv=await createDirectConversation(target);await loadConversations();setActiveId(conv.id);}else{const rows=await loadConversations();if(requested&&rows.some(row=>row.id===requested))setActiveId(requested);}const pending=window.sessionStorage.getItem('hvnh-pending-call');if(pending){window.sessionStorage.removeItem('hvnh-pending-call');sequenceRef.current+=1;setRealtimeEvent({...JSON.parse(pending),sequence:sequenceRef.current} as RealtimeCallEvent);}})().catch(console.error);},[loadConversations,params]);
 useEffect(()=>{if(!activeId)return;void fetchMessages(activeId).then(rows=>{setMessagesMap(p=>({...p,[activeId]:rows}));setConversations(p=>p.map(c=>c.id===activeId?{...c,unreadCount:0}:c));window.dispatchEvent(new Event('messages-changed'));}).catch(console.error);},[activeId]);
 useEffect(()=>{const onRealtime=(event:Event)=>{const data=(event as CustomEvent<Record<string,unknown>>).detail;if(data.event==='message.created'){const msg=data.message as Message;setMessagesMap(p=>({...p,[msg.conversationId]:[...(p[msg.conversationId]||[]).filter(x=>x.id!==msg.id),msg]}));void loadConversations();window.dispatchEvent(new Event('messages-changed'));}else if(data.event==='messages.seen'){setMessagesMap(p=>({...p,[String(data.conversation_id)]:(p[String(data.conversation_id)]||[]).map(m=>m.senderId===currentUserId?{...m,status:'seen'}:m)}));}else if(data.event==='presence.changed'){setConversations(p=>p.map(c=>c.participantId===data.user_id?{...c,isOnline:!!data.online,lastActive:data.online?'Đang hoạt động':'Ngoại tuyến'}:c));}else if(data.event==='conversation.updated'){void loadConversations();}else if(String(data.event).startsWith('call.')){sequenceRef.current+=1;setRealtimeEvent({...data,sequence:sequenceRef.current} as RealtimeCallEvent);if(data.event==='call.offer')setActiveId(String(data.conversation_id));}};window.addEventListener('hvnh-realtime',onRealtime);return()=>window.removeEventListener('hvnh-realtime',onRealtime);},[loadConversations,currentUserId]);
 const activeConversation=useMemo(()=>conversations.find(c=>c.id===activeId),[conversations,activeId]);const activeMessages=messagesMap[activeId]||[];const filtered=useMemo(()=>{const q=searchQuery.toLowerCase().trim();return q?conversations.filter(c=>c.participantName.toLowerCase().includes(q)||c.lastMessageSnippet.toLowerCase().includes(q)):conversations;},[conversations,searchQuery]);
 const selectConversation=useCallback((id:string)=>{setActiveId(id);setMobileView('chat');},[]);
 const sendMessage=useCallback(async(content:string,file?:File)=>{if(!activeId)return;const created=await sendChatMessage(activeId,content.trim(),file);setMessagesMap(p=>({...p,[activeId]:[...(p[activeId]||[]).filter(x=>x.id!==created.id),created]}));await loadConversations();window.dispatchEvent(new Event('messages-changed'));},[activeId,loadConversations]);
 const startConversation=useCallback(async(userId:string)=>{const conversation=await createDirectConversation(userId);await loadConversations();setActiveId(conversation.id);setMobileView('chat');return conversation;},[loadConversations]);
 const updateSettings=useCallback(async(payload:{theme?:Conversation['theme'];nickname?:string;is_muted?:boolean})=>{
  if(!activeId)return;
  setConversations(rows=>rows.map(row=>{
   if(row.id!==activeId)return row;
   return {...row, ...(payload.theme!==undefined?{theme:payload.theme}:{}), ...(payload.nickname!==undefined?{nickname:payload.nickname}:{}), ...(payload.is_muted!==undefined?{isMuted:payload.is_muted}:{})};
  }));
  await updateConversationSettings(activeId,payload);
  await loadConversations();
 },[activeId,loadConversations]);
 const removeActiveConversation=useCallback(()=>{setConversations(rows=>rows.filter(row=>row.id!==activeId));setActiveId('');setMobileView('list');},[activeId]);
 return{conversations:filtered,activeConversation,activeMessages,selectConversation,startConversation,searchQuery,setSearchQuery,showDetailsPanel,toggleDetailsPanel:()=>setShowDetailsPanel(v=>!v),sendMessage,updateSettings,sendRealtime,realtimeEvent,removeActiveConversation,currentUserId,mobileView,setMobileView};
}
