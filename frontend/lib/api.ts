import { UserProfile, UserFriend, UserListing, UserPhoto, FriendshipStatus } from '@/types/user';
import { Post, CreatePostPayload } from '@/types/post';
import { authenticatedFetch, getAccessToken, getAuthUser, refreshAuthSession, updateStoredAvatar, updateStoredFullName } from '@/lib/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function api<T>(endpoint: string, options?: RequestInit): Promise<T> {
  try {
    const res = await authenticatedFetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });
    if (!res.ok) {
      const payload = await res.json().catch(() => null) as {detail?: string | {msg?: string}[]}|null;
      const detail = payload?.detail;
      throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(item => item.msg || 'Dữ liệu không hợp lệ.').join('\n') : `API error: ${res.statusText}`);
    }
    if (res.status === 204) return undefined as T;
    return await res.json();
  } catch (error) {
    console.warn(`[API] Request failed for ${endpoint}:`, error);
    throw error;
  }
}

export async function sendFeedback(message: string): Promise<void> {
  await api<{ message: string }>('/feedback', { method: 'POST', body: JSON.stringify({ message }) });
}

// API Functions Implementation
export async function fetchUserProfile(userId?: string): Promise<UserProfile> {
  return api<UserProfile>(!userId || userId === 'me' ? '/users/me' : `/users/${userId}`);
}

export async function updateUserProfile(data: Partial<UserProfile>): Promise<UserProfile> {
  const updated = await api<UserProfile>('/users/me', { method: 'PATCH', body: JSON.stringify(data) });
  updateStoredFullName(updated.name);
  return updated;
}

export type AvatarVisibility = 'PUBLIC' | 'FRIENDS' | 'PRIVATE';

export async function uploadProfileAvatar(file: File, caption: string, visibility: AvatarVisibility): Promise<string> {
  const form = new FormData();
  form.append('file', file);
  const uploadResponse = await authenticatedFetch(`${API_BASE_URL}/media/upload/avatar`, {
    method: 'POST',
    body: form,
  });
  if (!uploadResponse.ok) {
    const payload = await uploadResponse.json().catch(() => null) as { detail?: string } | null;
    throw new Error(payload?.detail || 'Không thể tải ảnh lên Cloudflare R2.');
  }
  const uploaded = await uploadResponse.json() as { media_id: string };
  const updated = await api<{ avatar_url: string }>('/users/me/avatar', {
    method: 'PUT',
    body: JSON.stringify({ media_id: uploaded.media_id, caption, visibility, create_post: true }),
  });
  updateStoredAvatar(updated.avatar_url);
  return updated.avatar_url;
}

export async function uploadProfileCover(file: File): Promise<string> {
  const form = new FormData();
  form.append('file', file);
  const response = await authenticatedFetch(`${API_BASE_URL}/media/upload/cover`, { method: 'POST', body: form });
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(payload?.detail || 'Không thể tải ảnh bìa lên R2.');
  }
  const uploaded = await response.json() as { media_id: string };
  const updated = await api<{ cover_url: string }>('/users/me/cover', { method: 'PUT', body: JSON.stringify({ media_id: uploaded.media_id }) });
  return updated.cover_url;
}

export async function fetchUserPosts(userId: string, filter?: string, limit?: number, offset = 0): Promise<Post[]> {
  return api<Post[]>(`/users/${userId}/posts?filter=${encodeURIComponent(filter || 'all')}${limit ? `&limit=${limit}&offset=${offset}` : ''}`);
}

export async function fetchUserFriends(userId: string, query?: string): Promise<UserFriend[]> {
  return api<UserFriend[]>(`/users/${userId}/friends?q=${encodeURIComponent(query || '')}`);
}

export async function fetchUserPhotos(userId: string): Promise<UserPhoto[]> {
  return api<UserPhoto[]>(`/users/${userId}/photos`);
}

export async function fetchUserListings(userId: string, category = 'all'): Promise<UserListing[]> {
  return api<UserListing[]>(`/users/${userId}/listings?category=${encodeURIComponent(category)}`);
}
export async function fetchUserGroupPosts(userId: string, limit?: number, offset = 0): Promise<import('@/types/post').Post[]> {
  return api<import('@/types/post').Post[]>(`/users/${userId}/group-posts${limit ? `?limit=${limit}&offset=${offset}` : ''}`);
}

export async function updateFriendshipStatus(
  targetUserId: string,
  action: 'add' | 'accept' | 'reject' | 'unfriend' | 'cancel'
): Promise<{ status: FriendshipStatus }> {
  return api<{ status: FriendshipStatus }>(`/users/${targetUserId}/friendship`, {
    method: 'POST',
    body: JSON.stringify({ action }),
  });
}

export type UserSearchResult = UserFriend & { studentCode?: string };
export async function searchUsers(query: string, limit = 30): Promise<UserSearchResult[]> {
  return api(`/users/search?q=${encodeURIComponent(query)}&limit=${limit}`);
}

function uploadRequest(file:File,mediaId:string,token:string,onProgress?:CreatePostPayload['onUploadProgress']):Promise<Response>{
  return new Promise((resolve,reject)=>{const xhr=new XMLHttpRequest(),form=new FormData();form.append('file',file);xhr.open('POST',`${API_BASE_URL}/media/upload/post`);xhr.setRequestHeader('Authorization',`Bearer ${token}`);xhr.upload.onprogress=event=>{if(event.lengthComputable)onProgress?.(mediaId,Math.round(event.loaded/event.total*100),'uploading');};xhr.onerror=()=>{onProgress?.(mediaId,0,'error','Mất kết nối khi tải lên.');reject(new Error('Mất kết nối khi tải media lên R2.'));};xhr.onload=()=>{const response=new Response(xhr.responseText,{status:xhr.status,headers:{'Content-Type':xhr.getResponseHeader('Content-Type')||'application/json'}});if(!response.ok)onProgress?.(mediaId,0,'error','Không thể tải media lên R2.');resolve(response);};onProgress?.(mediaId,0,'uploading');xhr.send(form);});
}

async function uploadWithProgress(file:File,mediaId:string,onProgress?:CreatePostPayload['onUploadProgress']):Promise<Response>{
  let token=getAccessToken();if(!token)token=(await refreshAuthSession()).access_token;
  let response=await uploadRequest(file,mediaId,token,onProgress);
  if(response.status===401){token=(await refreshAuthSession()).access_token;response=await uploadRequest(file,mediaId,token,onProgress);}
  return response;
}

export async function uploadPostMedia(file: File): Promise<string> {
  const response = await uploadWithProgress(file, file.name);
  if (!response.ok) {
    const error = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(error?.detail || 'Không thể tải tệp lên.');
  }
  return ((await response.json()) as { media_id: string }).media_id;
}

export async function createProfilePost(payload: CreatePostPayload, groupId?: string): Promise<Post> {
  const mediaIds = await Promise.all(payload.media.map(async (item) => {
    if(item.uploadedMediaId)return item.uploadedMediaId;
    if (!item.file) throw new Error('Không tìm thấy tệp media gốc.');
    const response = await uploadWithProgress(item.file, item.id, payload.onUploadProgress);
    if (!response.ok) {
      const error = await response.json().catch(() => null) as { detail?: string } | null;
      throw new Error(error?.detail || 'Không thể tải media lên R2.');
    }
    const mediaId=((await response.json()) as { media_id: string }).media_id;
    payload.onUploadProgress?.(item.id,100,'complete',undefined,mediaId);
    return mediaId;
  }));
  return api<Post>(groupId ? `/groups/${groupId}/posts` : '/users/me/posts', {
    method: 'POST',
    body: JSON.stringify({
      content: payload.content,
      form_version: 2,
      privacy: payload.privacy,
      category: payload.category,
      media_ids: mediaIds,
      marketListing: payload.marketListing,
      roomListing: payload.roomListing,
      eventListing: payload.eventListing,
      studyListing: payload.studyListing,
      location: payload.location,
    }),
  });
}

export interface LocationSuggestion {
  name: string;
  address: string;
  latitude: number;
  longitude: number;
}

export async function searchLocations(query: string): Promise<LocationSuggestion[]> {
  const params = new URLSearchParams({ q: query, limit: '5' });
  return api<LocationSuggestion[]>(`/locations/search?${params.toString()}`);
}

export async function reverseGeocode(latitude: number, longitude: number): Promise<LocationSuggestion | null> {
  const params = new URLSearchParams({ latitude: String(latitude), longitude: String(longitude) });
  return api<LocationSuggestion | null>(`/locations/reverse?${params.toString()}`);
}

export interface FeedPage { items: Post[]; nextCursor: string | null; }

/** Cursor pagination avoids progressively slower OFFSET queries while scrolling. */
export async function fetchFeedPage(limit = 30, cursor = '', category = ''): Promise<FeedPage> {
  const query = new URLSearchParams({ limit: String(limit) });
  if (cursor) query.set('cursor', cursor);
  if (category) query.set('category', category);
  const response = await authenticatedFetch(`${API_BASE_URL}/posts/feed?${query.toString()}`, { headers: { 'Content-Type': 'application/json' } });
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(payload?.detail || `API error: ${response.statusText}`);
  }
  return { items: await response.json() as Post[], nextCursor: response.headers.get('X-Next-Cursor') };
}

// Kept for external callers compiled against the older offset-based helper.
export async function fetchFeed(limit = 30, offset = 0, category = ''): Promise<Post[]> {
  return api<Post[]>(`/posts/feed?limit=${limit}&offset=${offset}${category ? `&category=${encodeURIComponent(category)}` : ''}`);
}

export async function fetchPost(postId: string): Promise<Post> {
  return api<Post>(`/posts/${encodeURIComponent(postId)}`);
}

export async function registerPostShare(postId: string, destinationType: 'POST' | 'MESSAGE', destinationId: string): Promise<{ sharesCount: number }> {
  return api(`/posts/${encodeURIComponent(postId)}/shares`, {
    method: 'POST',
    body: JSON.stringify({ destination_type: destinationType, destination_id: destinationId }),
  });
}

export async function setPostLike(postId: string, isLiked: boolean): Promise<{ isLiked: boolean; likesCount: number }> {
  return api(`/posts/${postId}/like`, { method: 'PUT', body: JSON.stringify({ is_liked: isLiked }) });
}

export async function addPostComment(postId: string, content: string, parentId?: string, image?: File, mentions: { user_id: string; start: number; end: number }[] = []): Promise<import('@/types/post').Comment> {
  let mediaId: string | undefined;
  if (image) {
    const form=new FormData(); form.append('file',image);
    const response=await authenticatedFetch(`${API_BASE_URL}/media/upload/comment`,{method:'POST',body:form});
    if(!response.ok)throw new Error('Không thể tải ảnh bình luận lên R2.');
    mediaId=((await response.json()) as {media_id:string}).media_id;
  }
  return api(`/posts/${postId}/comments`, { method: 'POST', body: JSON.stringify({ content, parent_id: parentId, media_id: mediaId, mentions }) });
}
export async function fetchPostComments(postId: string, limit = 100, focusCommentId?: string): Promise<import('@/types/post').Comment[]> {
  const focus = focusCommentId ? `&focus_comment_id=${encodeURIComponent(focusCommentId)}` : '';
  return api(`/posts/${postId}/comments?limit=${limit}${focus}`);
}

export async function editPost(postId: string, content: string, privacy?: Post['privacy'], category?:Post['category'],mediaIds?:string[], details?: Pick<CreatePostPayload, 'marketListing' | 'roomListing' | 'eventListing' | 'studyListing' | 'location'>): Promise<Post> {
  return api(`/posts/${postId}`, { method: 'PATCH', body: JSON.stringify({ content, privacy, category, media_ids:mediaIds, ...(details || {}), ...(details ? { form_version: 2 } : {}) }) });
}
export async function editComment(commentId:string,content:string):Promise<import('@/types/post').Comment>{return api(`/posts/comments/${commentId}`,{method:'PATCH',body:JSON.stringify({content})});}
export async function deleteComment(commentId:string):Promise<void>{await api(`/posts/comments/${commentId}`,{method:'DELETE'});}

export async function deletePost(postId: string): Promise<void> {
  await api<void>(`/posts/${postId}`, { method: 'DELETE' });
}

export interface ApiNotification {
  id: string;
  type: 'POST_REVIEW' | 'POST_LIKE' | 'COMMENT' | 'FRIEND_REQUEST' | 'MESSAGE' | 'SYSTEM';
  title: string;
  content: string;
  actor_id: string | null;
  actor_name: string;
  actor_avatar: string | null;
  reference_type: string | null;
  reference_id: string | null;
  payload: Record<string, unknown>;
  link: string | null;
  is_unread: boolean;
  created_at: string;
}

export interface NotificationPage {
  items: ApiNotification[];
  total: number;
  unread_count: number;
  limit: number;
  offset: number;
}

export async function fetchNotifications(limit = 30, offset = 0, filter: 'all' | 'unread' | 'friends' = 'all'): Promise<NotificationPage> {
  return api(`/notifications?limit=${limit}&offset=${offset}&unread_only=${filter === 'unread'}&friend_only=${filter === 'friends'}`);
}

export async function fetchUnreadNotificationCount(): Promise<number> {
  const result = await api<{ unread_count: number }>('/notifications/unread-count');
  return result.unread_count;
}

export async function fetchHeaderUnreadCounts(): Promise<{ notifications: number; messages: number }> {
  return api('/notifications/header-counts');
}

export async function setNotificationRead(id: string, isRead: boolean): Promise<ApiNotification> {
  return api(`/notifications/${id}`, { method: 'PATCH', body: JSON.stringify({ is_read: isRead }) });
}

export async function markAllNotificationsRead(): Promise<void> {
  await api('/notifications/read-all', { method: 'POST' });
}

export async function removeNotification(id: string): Promise<void> {
  await api<void>(`/notifications/${id}`, { method: 'DELETE' });
}

export async function fetchConversations(): Promise<import('@/types/message').Conversation[]> { return api('/chat/conversations'); }
export async function createDirectConversation(targetUserId: string): Promise<import('@/types/message').Conversation> { return api('/chat/conversations/direct',{method:'POST',body:JSON.stringify({target_user_id:targetUserId})}); }
export async function fetchMessages(conversationId: string): Promise<import('@/types/message').Message[]> { return api(`/chat/conversations/${conversationId}/messages`); }
export async function searchConversationMessages(conversationId:string,query:string):Promise<import('@/types/message').Message[]>{return api(`/chat/conversations/${conversationId}/messages/search?q=${encodeURIComponent(query)}`);}
export async function fetchConversationShared(conversationId:string):Promise<{media:import('@/types/message').MessageAttachment[];files:import('@/types/message').MessageAttachment[]}>{return api(`/chat/conversations/${conversationId}/shared`);}
export async function updateConversationSettings(conversationId:string,payload:{theme?:import('@/types/message').Conversation['theme'];nickname?:string;is_muted?:boolean}):Promise<void>{await api(`/chat/conversations/${conversationId}/settings`,{method:'PATCH',body:JSON.stringify(payload)});}
export async function sendChatMessage(conversationId:string,content:string,file?:File,replyToId?:string):Promise<import('@/types/message').Message>{
  const media_ids:string[]=[];
  if(file){const form=new FormData();form.append('file',file);const response=await authenticatedFetch(`${API_BASE_URL}/media/upload/message`,{method:'POST',body:form});if(!response.ok){const e=await response.json().catch(()=>null) as {detail?:string}|null;throw new Error(e?.detail||'Không thể tải media tin nhắn.');}media_ids.push(((await response.json()) as {media_id:string}).media_id);}
  return api(`/chat/conversations/${conversationId}/messages`,{method:'POST',body:JSON.stringify({content,media_ids,reply_to_id:replyToId||null})});
}
export async function recallChatMessage(conversationId:string,messageId:string):Promise<import('@/types/message').Message>{
  try {
    return await api(`/chat/conversations/${conversationId}/messages/${messageId}`,{method:'DELETE'});
  } catch (error) {
    if (!(error instanceof TypeError)) throw error;
    // A lost response can occur after the server has already committed the recall.
    const messages = await fetchMessages(conversationId).catch(() => null);
    const recalled = messages?.find(message => message.id === messageId && message.isRecalled);
    if (recalled) return recalled;
    throw new Error('Không kết nối được máy chủ để thu hồi tin nhắn. Vui lòng thử lại.');
  }
}
export async function fetchUnreadMessageCount():Promise<number>{const result=await api<{unread_count:number}>('/chat/unread-count');return result.unread_count;}
export async function createWebSocketTicket():Promise<string>{const result=await api<{ticket:string;expires_in:number}>('/chat/ws-ticket',{method:'POST'});return result.ticket;}

export async function fetchGroups(): Promise<import('@/types/group-api').ApiGroup[]> {
  return api('/groups');
}

export async function requestGroupJoin(groupId: string): Promise<void> {
  await api(`/groups/${groupId}/join`, { method: 'POST' });
}

export async function leaveGroup(groupId: string): Promise<void> {
  await api(`/groups/${groupId}/leave`, { method: 'DELETE' });
}

export async function fetchGroupPosts(groupId: string, query = '', sort: 'latest'|'featured'|'pinned' = 'latest', limit?: number, offset = 0): Promise<import('@/types/group-api').GroupPost[]> {
  return api(`/groups/${groupId}/posts?q=${encodeURIComponent(query)}&sort=${sort}${limit ? `&limit=${limit}&offset=${offset}` : ''}`);
}

export async function fetchMyGroupPosts(groupId: string, limit?: number, offset = 0): Promise<import('@/types/group-api').GroupPost[]> {
  return api(`/groups/${groupId}/posts/mine${limit ? `?limit=${limit}&offset=${offset}` : ''}`);
}

export async function createGroupPost(groupId: string, content: string, files: File[]): Promise<import('@/types/group-api').GroupPost> {
  const mediaIds = await Promise.all(files.map(async (file) => {
    const form = new FormData();
    form.append('file', file);
    const response = await authenticatedFetch(`${API_BASE_URL}/media/upload/post`, { method: 'POST', body: form });
    if (!response.ok) throw new Error('Không thể tải media lên R2.');
    return ((await response.json()) as { media_id: string }).media_id;
  }));
  return api(`/groups/${groupId}/posts`, { method: 'POST', body: JSON.stringify({ content, media_ids: mediaIds }) });
}

export async function fetchPendingGroupPosts(groupId: string): Promise<import('@/types/group-api').GroupPost[]> {
  return api(`/groups/${groupId}/admin/posts/pending`);
}

export async function fetchGroupJoinRequests(groupId: string): Promise<import('@/types/group-api').GroupJoinRequest[]> {
  return api(`/groups/${groupId}/admin/join-requests`);
}

export async function decideGroupJoin(groupId: string, requestId: string, decision: 'APPROVE' | 'REJECT'): Promise<void> {
  await api(`/groups/${groupId}/admin/join-requests/${requestId}`, { method: 'PATCH', body: JSON.stringify({ decision }) });
}

export async function moderateGroupPost(groupId: string, postId: string, decision: 'APPROVE' | 'REJECT', reason?: string): Promise<import('@/types/group-api').GroupPost> {
  return api(`/groups/${groupId}/admin/posts/${postId}/moderate`, { method: 'PATCH', body: JSON.stringify({ decision, reason }) });
}

export async function setGroupPostPinned(groupId: string, postId: string, isPinned: boolean): Promise<void> {
  await api(`/groups/${groupId}/admin/posts/${postId}/pin`, { method: 'PUT', body: JSON.stringify({ is_pinned: isPinned }) });
}

export async function fetchGroupMembers(groupId: string, query = ''): Promise<import('@/types/group-api').GroupMember[]> {
  return api(`/groups/${groupId}/admin/members?q=${encodeURIComponent(query)}`);
}

export async function kickGroupMember(groupId: string, userId: string): Promise<void> {
  await api(`/groups/${groupId}/admin/members/${userId}`, { method: 'DELETE' });
}
export async function removeApprovedGroupPost(groupId:string,postId:string,reason:string):Promise<void>{await api(`/groups/${groupId}/admin/posts/${postId}`,{method:'DELETE',body:JSON.stringify({reason})});}
export async function removeGroupComment(groupId:string,commentId:string):Promise<void>{await api(`/groups/${groupId}/admin/comments/${commentId}`,{method:'DELETE'});}

export async function fetchAdminDashboard():Promise<import('@/types/admin').AdminDashboard>{return api('/admin/dashboard');}
export async function fetchGroupAdmins(groupId:string):Promise<import('@/types/admin').GroupAdminInfo[]>{return api(`/admin/groups/${encodeURIComponent(groupId)}/admins`);}
export async function exportAdminDashboard():Promise<void>{
  const response=await authenticatedFetch(`${API_BASE_URL}/admin/dashboard/export`);
  if(!response.ok)throw new Error('Không thể xuất báo cáo Excel.');
  const blob=await response.blob();
  const disposition=response.headers.get('content-disposition')||'';
  const filename=disposition.match(/filename="?([^";]+)"?/i)?.[1]||'hvnh-hub-dashboard.xlsx';
  const url=URL.createObjectURL(blob);const anchor=document.createElement('a');anchor.href=url;anchor.download=filename;anchor.click();URL.revokeObjectURL(url);
}
export function ragPeriodQuery(period:import('@/types/admin').RagPeriod,startDate='',endDate=''){
  const params=new URLSearchParams({period});
  if(period==='custom'){params.set('start_date',startDate);params.set('end_date',endDate);}
  return params.toString();
}
export async function fetchAdminUsers(q='',status='',period:import('@/types/admin').RagPeriod='30d',startDate='',endDate='',role:'ADMIN'|'USER'='USER',offset=0,limit=10):Promise<import('@/types/admin').AdminUserPage>{
  const path = `/admin/users?q=${encodeURIComponent(q)}&status=${encodeURIComponent(status)}&role=${role}&limit=${limit}&offset=${offset}&${ragPeriodQuery(period,startDate,endDate)}`;
  try { return await api(path); }
  catch (error) {
    if (!(error instanceof TypeError)) throw error;
    await new Promise(resolve => setTimeout(resolve, 400));
    return api(path);
  }
}
export async function fetchAdminUserRagUsage(userId:string,period:import('@/types/admin').RagPeriod='30d',startDate='',endDate='',offset=0):Promise<import('@/types/admin').RagUserUsage>{return api(`/admin/users/${userId}/rag-usage?${ragPeriodQuery(period,startDate,endDate)}&offset=${offset}`);}
export async function fetchAdminProfile(userId:string):Promise<import('@/types/admin').AdminProfilePreview>{return api(`/admin/users/${encodeURIComponent(userId)}/profile`);}
export async function fetchAdminPublicPosts(q='',status:'ALL'|'APPROVED'|'HIDDEN'='ALL',offset=0,limit=10,authorId?:string):Promise<import('@/types/admin').AdminPublicPostPage>{const params=new URLSearchParams({q,status,offset:String(offset),limit:String(limit)});if(authorId)params.set('author_id',authorId);return api(`/admin/public-posts?${params}`);}
export async function setAdminUserStatus(userId:string,status:'ACTIVE'|'LOCKED'|'DISABLED',reason:string):Promise<void>{await api(`/admin/users/${userId}/status`,{method:'PATCH',body:JSON.stringify({status,reason})});}
export async function disciplineAdminUser(userId:string,action:'WARN'|'SUSPEND'|'BAN'|'UNLOCK',reason:string,durationDays?:number):Promise<void>{await api(`/admin/users/${userId}/discipline`,{method:'POST',body:JSON.stringify({action,reason,duration_days:durationDays})});}
export async function fetchAdminAuditLogs():Promise<import('@/types/admin').AdminAuditLog[]>{return api('/admin/audit-logs?limit=100');}
export async function createReport(target_type:'USER'|'POST'|'COMMENT',target_id:string,reason:string,evidence_media_id?:string):Promise<void>{await api('/reports',{method:'POST',body:JSON.stringify({target_type,target_id,reason,evidence_media_id})});}
export async function fetchReportQueue(status=''):Promise<import('@/types/report').ApiReport[]>{return api(`/reports/admin?status=${encodeURIComponent(status)}`);}
export async function fetchReportDetail(reportId:string):Promise<import('@/types/report').ReportDetail>{return api(`/reports/admin/${encodeURIComponent(reportId)}`);}
export async function resolveReport(id:string,decision:'RESOLVE'|'REJECT',action:'NONE'|'HIDE_CONTENT'|'LOCK_USER'|'DISABLE_USER',note:string):Promise<string>{const result=await api<{message:string}>(`/reports/admin/${id}`,{method:'PATCH',body:JSON.stringify({decision,action,note})});return result.message;}
export async function requestPasswordReset(email:string):Promise<void>{await api('/auth/password/forgot',{method:'POST',body:JSON.stringify({email})});}
export async function resetPassword(email:string,code:string,newPassword:string):Promise<void>{await api('/auth/password/reset',{method:'POST',body:JSON.stringify({email,code,new_password:newPassword})});}
export async function changePassword(currentPassword:string,newPassword:string):Promise<void>{await api('/auth/password/change',{method:'POST',body:JSON.stringify({current_password:currentPassword,new_password:newPassword})});}
export async function setUserBlocked(userId:string,blocked:boolean):Promise<void>{await api(`/users/${userId}/block`,{method:blocked?'PUT':'DELETE'});}
export async function fetchBlockedUsers():Promise<UserFriend[]>{return api('/users/me/blocked');}
export async function fetchSystemStatus():Promise<import('@/types/system').MaintenanceState>{const response=await fetch(`${API_BASE_URL}/system/status`,{cache:'no-store'});if(!response.ok)throw new Error('Không tải được trạng thái hệ thống.');return response.json();}
export async function updateMaintenance(payload:import('@/types/system').MaintenanceState):Promise<import('@/types/system').MaintenanceState>{return api('/system/admin/maintenance',{method:'PUT',body:JSON.stringify(payload)});}
export async function fetchBlacklist():Promise<import('@/types/system').BlacklistKeyword[]>{return api('/system/admin/keywords');}
export async function createBlacklistKeyword(keyword:string,action:'BLOCK'|'REVIEW'):Promise<void>{await api('/system/admin/keywords',{method:'POST',body:JSON.stringify({keyword,action})});}
export async function updateBlacklistKeyword(id:string,payload:Partial<Pick<import('@/types/system').BlacklistKeyword,'keyword'|'action'|'is_active'>>):Promise<void>{await api(`/system/admin/keywords/${id}`,{method:'PATCH',body:JSON.stringify(payload)});}
export async function deleteBlacklistKeyword(id:string):Promise<void>{await api(`/system/admin/keywords/${id}`,{method:'DELETE'});}
export async function askAIAssistant(question:string,conversationId?:string):Promise<import('@/types/ai').AIChatResponse>{return api('/ai/chat',{method:'POST',body:JSON.stringify({question,conversation_id:conversationId||null})});}
export async function fetchAIConversations():Promise<import('@/types/ai').AIConversation[]>{return api('/ai/conversations?limit=50&offset=0');}
export async function createAIConversation(title?:string):Promise<import('@/types/ai').AIConversation>{return api('/ai/conversations',{method:'POST',body:JSON.stringify({title:title||null})});}
export async function fetchAIConversationMessages(id:string):Promise<import('@/types/ai').AIConversationMessages>{return api(`/ai/conversations/${id}/messages?limit=200`);}
export async function renameAIConversation(id:string,title:string):Promise<import('@/types/ai').AIConversation>{return api(`/ai/conversations/${id}`,{method:'PATCH',body:JSON.stringify({title})});}
export async function deleteAIConversation(id:string):Promise<void>{await api(`/ai/conversations/${id}`,{method:'DELETE'});}
