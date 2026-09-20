"use client";
import {useCallback,useEffect,useRef,useState} from "react";
import Link from "next/link";
import CreatePostCard from "@/components/post/CreatePostCard";
import CreatePostModal from "@/components/post/CreatePostModal";
import PostCard from "@/components/post/PostCard";
import {useCreatePost} from "@/hooks/useCreatePost";
import type {Post,PostCategory} from "@/types/post";
import {getAuthUser,type AuthUser} from "@/lib/auth";
import {createProfilePost,fetchFeed} from "@/lib/api";
import AIPet from "@/components/ai/AIPet";

const PAGE_SIZE=10;
const filters:{value:''|PostCategory;label:string}[]=[{value:'',label:'Tất cả'},{value:'general',label:'Bài chung'},{value:'market',label:'Pass đồ'},{value:'roommate',label:'Phòng trọ'},{value:'event',label:'Sự kiện'},{value:'study',label:'Học tập'}];
function FeedSkeleton(){return <div className="feed-skeleton" aria-hidden="true"><div className="skeleton-head"><i/><div><b/><span/></div></div><p/><p/><div className="skeleton-media"/></div>}

export default function HomePage(){
 const [posts,setPosts]=useState<Post[]>([]),[authUser,setAuthUser]=useState<AuthUser|null>(null),[loading,setLoading]=useState(false),[hasMore,setHasMore]=useState(true),[feedError,setFeedError]=useState(""),[category,setCategory]=useState<''|PostCategory>('');
 const offsetRef=useRef(0),sentinelRef=useRef<HTMLDivElement|null>(null),loadingRef=useRef(false);
 const loadMore=useCallback(async(reset=false)=>{if(loadingRef.current||(!reset&&!hasMore))return;loadingRef.current=true;setLoading(true);try{const offset=reset?0:offsetRef.current;const next=await fetchFeed(PAGE_SIZE,offset,category);setPosts(previous=>reset?next:[...previous,...next.filter(item=>!previous.some(existing=>existing.id===item.id))]);offsetRef.current=offset+next.length;setHasMore(next.length===PAGE_SIZE);setFeedError("");}catch(error){setFeedError(error instanceof Error?error.message:"Không thể tải bảng tin.");}finally{loadingRef.current=false;setLoading(false);}},[hasMore,category]);
 useEffect(()=>setAuthUser(getAuthUser()),[]);
 useEffect(()=>{offsetRef.current=0;setHasMore(true);setPosts([]);void loadMore(true);},[category]); // eslint-disable-line react-hooks/exhaustive-deps
 useEffect(()=>{const target=sentinelRef.current;if(!target)return;const observer=new IntersectionObserver(entries=>{if(entries[0]?.isIntersecting)void loadMore();},{rootMargin:"500px 0px"});observer.observe(target);return()=>observer.disconnect();},[loadMore]);
 const handlePostCreated=async(payload:Parameters<typeof createProfilePost>[0])=>{const created=await createProfilePost(payload);if(!category||created.category===category)setPosts(previous=>[created,...previous]);return created;};
 const createPostState=useCreatePost(handlePostCreated);
 return <main className="home-page-single-column"><div className="home-content-full"><section className="home-welcome"><p>Cộng đồng HVNH</p><h1>Chào mừng trở lại{authUser?.full_name?`, ${authUser.full_name}`:""}</h1><span>Khám phá những tin tức và bài đăng mới nhất trong trường hôm nay.</span></section>
  <div className="home-layout"><section className="home-feed" aria-label="Bài viết mới"><CreatePostCard onOpenModal={createPostState.openModal} userAvatar={authUser?.avatar_url||undefined} userName={authUser?.full_name||undefined}/><div className="feed-filter-bar" role="tablist" aria-label="Lọc bảng tin">{filters.map(item=><button type="button" role="tab" aria-selected={category===item.value} className={category===item.value?'active':''} key={item.value||'all'} onClick={()=>setCategory(item.value)}>{item.label}</button>)}</div>
   {loading&&!posts.length?<><FeedSkeleton/><FeedSkeleton/><FeedSkeleton/></>:posts.map(post=><PostCard key={post.id} post={post}/>)}
   <div ref={sentinelRef} className="feed-load-sentinel" aria-live="polite">{loading&&posts.length>0&&<span><i/>Đang tải thêm bài viết...</span>}{feedError&&<><p>{feedError}</p><button type="button" className="btn btn-secondary" onClick={()=>void loadMore()}>Thử lại</button></>}{!loading&&!feedError&&!hasMore&&posts.length>0&&<small>Bạn đã xem hết bài viết.</small>}{!loading&&!feedError&&!posts.length&&<small>Chưa có bài viết trong chuyên mục này.</small>}</div>
  </section><aside className="home-side-panel"><h2>Khám phá cộng đồng HVNH</h2><p>Tham gia các nhóm chuyên biệt theo chủ đề: Pass đồ, Phòng trọ, Sự kiện và Học tập.</p><Link href="/groups" className="btn btn-primary btn-block">Xem các nhóm</Link></aside></div>
 </div><CreatePostModal postState={createPostState}/><AIPet userName={authUser?.full_name}/></main>;
}
