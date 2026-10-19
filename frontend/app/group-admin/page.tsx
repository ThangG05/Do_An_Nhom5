"use client";

import {useCallback, useEffect, useMemo, useRef, useState} from "react";
import {useSearchParams} from "next/navigation";
import Link from "next/link";
import PostCard from "@/components/post/PostCard";
import PendingGroupPostCard from "@/components/admin/PendingGroupPostCard";
import ReportQueue from "@/components/admin/ReportQueue";
import {
  decideGroupJoin, fetchGroupJoinRequests, fetchGroupMembers, fetchGroupPosts,
  fetchGroups, fetchPendingGroupPosts, kickGroupMember, moderateGroupPost,
  removeApprovedGroupPost, setGroupPostPinned,
} from "@/lib/api";
import {getAuthUser} from "@/lib/auth";
import type {ApiGroup, GroupJoinRequest, GroupMember, GroupPost} from "@/types/group-api";
import {useDialog} from "@/components/ui/DialogProvider";
import RelativeTime from "@/components/ui/RelativeTime";
import StudyLibrary from "@/components/group/StudyLibrary";
import SubjectCatalog from "@/components/group/SubjectCatalog";
import {safeImageSrc} from "@/lib/media";
import {openStudyDocumentReportCount, pendingStudyDocumentCount} from "@/lib/study-library";

type Tab = "overview" | "pending" | "posts" | "members" | "reports" | "documents" | "subjects";
const dedicatedSlugs = new Set(["pass-do", "ghep-phong-tim-tro", "su-kien", "hoc-tap"]);

function dedicatedSlug(email?: string): string | null {
  const match = /^admin-([a-z-]+)@hvnh\.edu\.vn$/i.exec(email || "");
  return match && dedicatedSlugs.has(match[1]) ? match[1] : null;
}

export default function GroupAdminPage() {
  const dialog = useDialog();
  const params = useSearchParams();
  const previousRequested = useRef<string | null>(null);
  const loadVersion = useRef(0);
  const busyRef = useRef(false);
  const [groups, setGroups] = useState<ApiGroup[]>([]);
  const [groupId, setGroupId] = useState("");
  const [pending, setPending] = useState<GroupPost[]>([]);
  const [posts, setPosts] = useState<GroupPost[]>([]);
  const [joins, setJoins] = useState<GroupJoinRequest[]>([]);
  const [members, setMembers] = useState<GroupMember[]>([]);
  const [pendingDocuments, setPendingDocuments] = useState(0);
  const [documentReports, setDocumentReports] = useState(0);
  const [tab, setTab] = useState<Tab>("overview");
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [loadingGroups, setLoadingGroups] = useState(true);
  const [loadingContent, setLoadingContent] = useState(false);
  const [busy, setBusy] = useState(false);
  const active = groups.find(group => group.id === groupId);

  const loadGroups = useCallback(async () => {
    const auth = getAuthUser();
    const all = await fetchGroups();
    // The API membership is live; local auth data can be stale after a role change.
    const owned = all.filter(group => group.membership === "ADMIN");
    const assigned = dedicatedSlug(auth?.email);
    const scoped = assigned ? owned.filter(group => group.slug === assigned) : owned;
    setGroups(scoped);
    setError(assigned && !scoped.length ? "Tài khoản quản trị chưa được gán đúng nhóm. Vui lòng liên hệ Super Admin." : "");

    const requested = params.get("groupId");
    const routeChanged = previousRequested.current !== requested;
    previousRequested.current = requested;
    setGroupId(current => {
      if (assigned) return scoped[0]?.id || "";
      if (routeChanged && requested && scoped.some(group => group.id === requested)) return requested;
      if (current && scoped.some(group => group.id === current)) return current;
      if (requested && scoped.some(group => group.id === requested)) return requested;
      return scoped[0]?.id || "";
    });
  }, [params]);

  const load = useCallback(async () => {
    const version = ++loadVersion.current;
    if (!groupId) return;
    setLoadingContent(true);
    try {
      const [waiting, approved, requests, people] = await Promise.all([
        fetchPendingGroupPosts(groupId), fetchGroupPosts(groupId),
        fetchGroupJoinRequests(groupId), fetchGroupMembers(groupId, query),
      ]);
      if (version !== loadVersion.current) return;
      setPending(waiting);
      setPosts(approved);
      setJoins(requests);
      setMembers(people);
    } finally {
      if (version === loadVersion.current) setLoadingContent(false);
    }
  }, [groupId, query]);

  useEffect(() => {
    void loadGroups().catch(cause => setError(cause instanceof Error ? cause.message : "Không tải được nhóm quản trị.")).finally(() => setLoadingGroups(false));
  }, [loadGroups]);
  useEffect(() => {
    setPending([]);
    setPosts([]);
    setJoins([]);
    setMembers([]);
  }, [groupId]);
  useEffect(() => { void load().catch(cause => setError(cause instanceof Error ? cause.message : "Không tải được dữ liệu nhóm.")); }, [load]);

  useEffect(() => {
    if (!groupId || active?.slug !== "hoc-tap") { setPendingDocuments(0); setDocumentReports(0); return; }
    let alive = true;
    let loadingCount = false;
    const refreshCount = async () => {
      if (!alive || loadingCount || document.visibilityState === "hidden") return;
      loadingCount = true;
      try {
        const [pendingResult, reportResult] = await Promise.all([
          pendingStudyDocumentCount(groupId), openStudyDocumentReportCount(groupId),
        ]);
        if (alive) { setPendingDocuments(pendingResult.count); setDocumentReports(reportResult.count); }
      } catch { /* Keep the last known badge if polling briefly fails. */ }
      finally { loadingCount = false; }
    };
    void refreshCount();
    const timer = window.setInterval(() => void refreshCount(), 30_000);
    document.addEventListener("visibilitychange", refreshCount);
    return () => { alive = false; window.clearInterval(timer); document.removeEventListener("visibilitychange", refreshCount); };
  }, [groupId, active?.slug]);
  const act = async (work: () => Promise<unknown>) => {
    if (busyRef.current) return;
    busyRef.current = true;
    setBusy(true);
    setError("");
    try { await work(); await load(); await loadGroups(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Không thể thực hiện thao tác."); }
    finally { busyRef.current = false; setBusy(false); }
  };
  const removePost = async (post: GroupPost) => {
    const reason = await dialog.prompt({title: "Gỡ bài đã duyệt", message: "Tác giả sẽ nhận được lý do gỡ bài.", placeholder: "Nhập lý do gỡ bài...", multiline: true, minLength: 3, tone: "danger"});
    if (reason) await act(() => removeApprovedGroupPost(groupId, post.id, reason));
  };
  const rejectPost = async (post: GroupPost) => {
    const reason = await dialog.prompt({title: "Từ chối bài viết", message: `Nêu lý do để ${post.author.name} biết cách chỉnh sửa.`, placeholder: "Lý do từ chối...", multiline: true, minLength: 3, tone: "danger"});
    if (reason) await act(() => moderateGroupPost(groupId, post.id, "REJECT", reason));
  };
  const kickMember = async (member: GroupMember) => {
    if (await dialog.confirm({title: "Xóa thành viên khỏi nhóm?", message: `${member.name} sẽ mất quyền truy cập nội dung dành cho thành viên.`, confirmLabel: "Xóa khỏi nhóm", tone: "danger"})) await act(() => kickGroupMember(groupId, member.id));
  };
  const stats = useMemo(() => [
    {label: "Chờ duyệt", value: pending.length},
    {label: "Yêu cầu gia nhập", value: joins.length},
    {label: "Thành viên", value: active?.member_count ?? members.length},
    {label: "Bài đang hiển thị", value: posts.length},
  ], [pending.length, joins.length, active?.member_count, members.length, posts.length]);

  if (loadingGroups) return <main className="group-admin-page"><div className="group-admin-empty">Đang tải nhóm quản trị...</div></main>;
  if (!groups.length) return <main className="group-admin-page"><div className="group-admin-empty"><h1>Không có nhóm được phân công</h1><p>{error || "Super Admin cần gán bạn làm Admin của một nhóm."}</p></div></main>;

  return <main className="group-admin-page">
    <header className="group-admin-hero"><div><span>GROUP ADMIN WORKSPACE</span><h1>Quản trị nhóm {active?.name || ""}</h1><p>Mọi dữ liệu và thao tác đều giới hạn trong nhóm được phân công.</p></div>
      {groups.length > 1 && <select value={groupId} aria-label="Chọn nhóm quản trị" onChange={event => { setGroupId(event.target.value); setTab("overview"); }}>{groups.map(group => <option key={group.id} value={group.id}>{group.name}</option>)}</select>}
    </header>
    {error && <div className="group-admin-error" role="alert">{error}</div>}
    <section className="group-admin-stats">{stats.map(stat => <article key={stat.label}><b>{stat.value}</b><span>{stat.label}</span></article>)}</section>
    <nav className="group-admin-nav" aria-label="Mục quản trị nhóm">{([
      ["overview", "Tổng quan"], ["pending", `Kiểm duyệt${pending.length ? ` (${pending.length})` : ""}`],
      ["posts", "Bài đã duyệt"], ["members", `Thành viên${members.length ? ` (${members.length})` : ""}`], ["reports", "Báo cáo"],
      ...(active?.slug === "hoc-tap" ? [["documents", "Kho tài liệu"], ["subjects", "Môn học"]] : []),
    ] as [Tab, string][]).map(([id, label]) => <button type="button" key={id} className={tab === id ? "active" : ""} onClick={() => setTab(id)}><span>{label}</span>{id === "documents" && pendingDocuments + documentReports > 0 && <span className="group-admin-pending-badge" aria-label={`${pendingDocuments} tài liệu chờ duyệt, ${documentReports} tố cáo`}>{pendingDocuments + documentReports}</span>}</button>)}</nav>

    {tab === "overview" && <section className="group-admin-panel"><h2>Công việc cần xử lý</h2><div className="admin-task-grid">
      <button type="button" onClick={() => setTab("pending")}><b>{pending.length}</b><span>Bài đang chờ quyết định</span></button>
      <button type="button" onClick={() => setTab("members")}><b>{joins.length}</b><span>Yêu cầu tham gia mới</span></button>
      <button type="button" onClick={() => setTab("reports")}><b>→</b><span>Mở hàng chờ báo cáo</span></button>
    </div></section>}

    {tab === "pending" && <section className="group-admin-panel group-pending-panel"><div className="group-pending-heading"><div><span>KIỂM DUYỆT NỘI DUNG</span><h2>Bài viết chờ phê duyệt</h2><p>Xem đầy đủ bài viết trước khi quyết định hiển thị trong nhóm.</p></div><b>{pending.length} bài chờ</b></div>
      <div className="group-pending-list">{!loadingContent && pending.map(post => <PendingGroupPostCard key={post.id} post={post} groupName={active?.name || ""} busy={busy} onApprove={() => { void act(() => moderateGroupPost(groupId, post.id, "APPROVE")); }} onReject={() => { void rejectPost(post); }} />)}</div>
      {loadingContent ? <p className="admin-empty-state" role="status">Đang tải bài chờ duyệt...</p> : !pending.length && <p className="admin-empty-state">Không có bài chờ duyệt trong nhóm này.</p>}
    </section>}

    {tab === "posts" && <section className="group-admin-panel"><h2>Bài viết đang hiển thị</h2>{posts.map(post => <div className="managed-post" key={post.id}><PostCard post={post} moderatorGroupId={groupId} moderatorActions={{isPinned: post.isPinned, busy, onTogglePin: () => { void act(() => setGroupPostPinned(groupId, post.id, !post.isPinned)); }, onRemove: () => { void removePost(post); }}} /></div>)}{!posts.length && <p className="admin-empty-state">Nhóm chưa có bài đã duyệt.</p>}</section>}

    {tab === "members" && <section className="group-admin-panel"><div className="panel-title-row"><h2>Thành viên và yêu cầu gia nhập</h2><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Tìm theo tên hoặc mã sinh viên" /></div>
      {joins.map(request => <article className="moderation-row join" key={request.id}><div><strong>{request.name}</strong><p>@{request.username}</p></div><div><button type="button" disabled={busy} onClick={() => { void act(() => decideGroupJoin(groupId, request.id, "APPROVE")); }}>Chấp nhận</button><button type="button" disabled={busy} className="danger" onClick={() => { void act(() => decideGroupJoin(groupId, request.id, "REJECT")); }}>Từ chối</button></div></article>)}
      <div className="member-table">{members.map(member => <article key={member.id}><Link href={`/profile/${member.id}`} className="member-identity" aria-label={`Xem trang cá nhân của ${member.name}`}><img src={safeImageSrc(member.avatar_url)} alt="" /><span><strong>{member.name}</strong><small>{member.student_code ? `Mã sinh viên: ${member.student_code}` : member.username}</small></span></Link><b>{member.role}</b>{member.role === "MEMBER" && <button type="button" disabled={busy} className="danger" onClick={() => { void kickMember(member); }}>Xóa khỏi nhóm</button>}</article>)}</div>
      {!members.length && <p className="admin-empty-state">Không tìm thấy thành viên.</p>}
    </section>}

    {tab === "reports" && groupId && <ReportQueue groupId={groupId} />}
    {tab === "documents" && active?.slug === "hoc-tap" && <StudyLibrary groupId={groupId} isAdmin canRead pendingCount={pendingDocuments} reportCount={documentReports} />}
    {tab === "subjects" && active?.slug === "hoc-tap" && <SubjectCatalog groupId={groupId} />}
  </main>;
}
