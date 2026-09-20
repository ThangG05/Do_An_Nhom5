"use client";

import {createContext,useCallback,useContext,useEffect,useMemo,useRef,useState} from "react";

type Tone='default'|'danger'|'success';
type ConfirmOptions={title:string;message:string;confirmLabel?:string;cancelLabel?:string;tone?:Tone};
type PromptOptions=ConfirmOptions&{placeholder?:string;initialValue?:string;multiline?:boolean;required?:boolean;minLength?:number;inputType?:'text'|'number';};
type Toast={id:number;title:string;message?:string;tone:Tone};
type DialogState={kind:'confirm'|'prompt';options:ConfirmOptions|PromptOptions;resolve:(value:boolean|string|null)=>void}|null;
type DialogApi={confirm:(options:ConfirmOptions)=>Promise<boolean>;prompt:(options:PromptOptions)=>Promise<string|null>;notify:(options:{title:string;message?:string;tone?:Tone})=>void};

const DialogContext=createContext<DialogApi|null>(null);

export function DialogProvider({children}:{children:React.ReactNode}){
 const [dialog,setDialog]=useState<DialogState>(null),[value,setValue]=useState(""),[validation,setValidation]=useState(""),[toasts,setToasts]=useState<Toast[]>([]);const toastId=useRef(0);
 const open=useCallback((kind:'confirm'|'prompt',options:ConfirmOptions|PromptOptions)=>new Promise<boolean|string|null>(resolve=>{setValue(kind==='prompt'?(options as PromptOptions).initialValue||'':'');setValidation('');setDialog({kind,options,resolve});}),[]);
 const confirm=useCallback((options:ConfirmOptions)=>open('confirm',options) as Promise<boolean>,[open]);
 const prompt=useCallback((options:PromptOptions)=>open('prompt',options) as Promise<string|null>,[open]);
 const notify=useCallback((options:{title:string;message?:string;tone?:Tone})=>{const id=++toastId.current;setToasts(current=>[...current,{id,title:options.title,message:options.message,tone:options.tone||'default'}]);window.setTimeout(()=>setToasts(current=>current.filter(item=>item.id!==id)),4200);},[]);
 const close=(result:boolean|string|null)=>{dialog?.resolve(result);setDialog(null);setValidation('');};
 useEffect(()=>{if(!dialog)return;const previous=document.body.style.overflow;document.body.style.overflow='hidden';const onKey=(event:KeyboardEvent)=>{if(event.key==='Escape'){dialog.resolve(dialog.kind==='confirm'?false:null);setDialog(null);setValidation('');}};document.addEventListener('keydown',onKey);return()=>{document.body.style.overflow=previous;document.removeEventListener('keydown',onKey);};},[dialog]);
 const submit=()=>{if(!dialog)return;if(dialog.kind==='confirm'){close(true);return;}const options=dialog.options as PromptOptions,trimmed=value.trim();if(options.required!==false&&!trimmed){setValidation('Vui lòng nhập nội dung.');return;}if(options.minLength&&trimmed.length<options.minLength){setValidation(`Nội dung cần ít nhất ${options.minLength} ký tự.`);return;}close(trimmed);};
 const api=useMemo(()=>({confirm,prompt,notify}),[confirm,prompt,notify]);
 return <DialogContext.Provider value={api}>{children}
  {dialog&&<div className="system-dialog-backdrop" role="presentation" onMouseDown={event=>{if(event.target===event.currentTarget)close(dialog.kind==='confirm'?false:null);}}><section className={`system-dialog-card tone-${dialog.options.tone||'default'}`} role="dialog" aria-modal="true" aria-labelledby="system-dialog-title"><header><div className="system-dialog-icon">{dialog.options.tone==='danger'?'!':dialog.options.tone==='success'?'✓':'i'}</div><div><h2 id="system-dialog-title">{dialog.options.title}</h2><p>{dialog.options.message}</p></div></header>{dialog.kind==='prompt'&&<div className="system-dialog-input">{(dialog.options as PromptOptions).multiline?<textarea autoFocus value={value} onChange={e=>setValue(e.target.value)} placeholder={(dialog.options as PromptOptions).placeholder}/>:<input autoFocus type={(dialog.options as PromptOptions).inputType||'text'} value={value} onChange={e=>setValue(e.target.value)} placeholder={(dialog.options as PromptOptions).placeholder}/>} {validation&&<small>{validation}</small>}</div>}<footer><button type="button" onClick={()=>close(dialog.kind==='confirm'?false:null)}>{dialog.options.cancelLabel||'Hủy'}</button><button type="button" className={dialog.options.tone==='danger'?'danger':''} onClick={submit}>{dialog.options.confirmLabel||'Xác nhận'}</button></footer></section></div>}
  <div className="system-toast-region" aria-live="polite">{toasts.map(toast=><article key={toast.id} className={`system-toast tone-${toast.tone}`}><span>{toast.tone==='success'?'✓':toast.tone==='danger'?'!':'i'}</span><div><strong>{toast.title}</strong>{toast.message&&<p>{toast.message}</p>}</div><button type="button" onClick={()=>setToasts(current=>current.filter(item=>item.id!==toast.id))} aria-label="Đóng thông báo">✕</button></article>)}</div>
 </DialogContext.Provider>;
}

export function useDialog(){const value=useContext(DialogContext);if(!value)throw new Error('useDialog must be used inside DialogProvider');return value;}
