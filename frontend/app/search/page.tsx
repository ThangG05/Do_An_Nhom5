"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { searchUsers, type UserSearchResult } from "@/lib/api";
import { safeImageSrc } from "@/lib/media";

export default function SearchPage() {
  const params = useSearchParams();
  const query = (params.get("q") || "").trim();
  const [items, setItems] = useState<UserSearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true); setError("");
    searchUsers(query).then(setItems).catch((e) => setError(e instanceof Error ? e.message : "Không thể tìm kiếm."))
      .finally(() => setLoading(false));
  }, [query]);

  return <main className="user-search-page">
    <header><span>TÌM KIẾM SINH VIÊN</span><h1>Kết quả cho “{query}”</h1><p>Tìm theo họ tên, mã sinh viên hoặc username.</p></header>
    {loading && <div className="user-search-state">Đang tìm kiếm…</div>}
    {error && <div className="user-search-state error">{error}</div>}
    {!loading && !error && <section className="user-search-results">
      {items.map(user => <Link href={`/profile/${user.id}`} className="user-search-card" key={user.id}>
        <img src={safeImageSrc(user.avatar)} alt="" />
        <div><strong>{user.name}</strong><span>@{user.username}{user.studentCode ? ` · ${user.studentCode}` : ""}</span><small>{user.faculty || "Sinh viên HVNH"}</small></div>
        <b>Xem hồ sơ</b>
      </Link>)}
      {!items.length && <div className="user-search-state">Không tìm thấy sinh viên phù hợp. Người đã chặn bạn hoặc bị bạn chặn sẽ không xuất hiện.</div>}
    </section>}
  </main>;
}
