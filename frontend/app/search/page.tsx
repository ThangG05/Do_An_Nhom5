"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { searchUsers, type UserSearchResult } from "@/lib/api";
import UserAvatar from "@/components/ui/UserAvatar";

export default function SearchPage() {
  const params = useSearchParams();
  const query = (params.get("q") || "").trim();
  const [items, setItems] = useState<UserSearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true); setError("");
    setItems([]);
    searchUsers(query).then(rows => { if (active) setItems(rows); })
      .catch((e) => { if (active) setError(e instanceof Error ? e.message : "Không thể tìm kiếm."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [query]);

  return <main className="user-search-page">
    <header><span>TÌM KIẾM SINH VIÊN</span><h1>Kết quả cho “{query}”</h1><p>Tìm theo họ tên, mã sinh viên hoặc username.</p></header>
    {loading && <div className="user-search-state">Đang tìm kiếm…</div>}
    {error && <div className="user-search-state error">{error}</div>}
    {!loading && !error && <section className="user-search-results">
      {items.map(user => <Link href={`/profile/${user.id}`} className="user-search-card" key={user.id}>
        <UserAvatar src={user.avatar} name={user.name} imageClassName="user-search-avatar" fallbackClassName="user-search-avatar user-avatar-initials" />
        <div><strong>{user.name}</strong><span>@{user.username}{user.studentCode ? ` · ${user.studentCode}` : ""}</span><small>{user.accountStatus && user.accountStatus !== 'ACTIVE' ? 'Tài khoản tạm ngừng hoạt động' : user.faculty || "Sinh viên HVNH"}</small></div>
        <b>Xem hồ sơ</b>
      </Link>)}
      {!items.length && <div className="user-search-state">Không tìm thấy sinh viên phù hợp. Tài khoản bị chặn hoặc tạm ngừng hoạt động mà không phải bạn bè sẽ không xuất hiện.</div>}
    </section>}
  </main>;
}
