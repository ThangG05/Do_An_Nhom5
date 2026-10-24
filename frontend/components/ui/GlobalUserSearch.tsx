"use client";

import { useEffect, useRef, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { searchUsers, type UserSearchResult } from '@/lib/api';
import UserAvatar from './UserAvatar';
import { IconSearch } from './Icons';
import styles from './GlobalUserSearch.module.css';

const MIN_QUERY_LENGTH = 2;

export default function GlobalUserSearch() {
  const router = useRouter();
  const pathname = usePathname();
  const rootRef = useRef<HTMLDivElement>(null);
  const activeIndexRef = useRef(-1);
  const [query, setQuery] = useState('');
  const [matches, setMatches] = useState<UserSearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  useEffect(() => { setOpen(false); activeIndexRef.current = -1; setActiveIndex(-1); }, [pathname]);

  useEffect(() => {
    const value = query.trim();
    activeIndexRef.current = -1;
    setActiveIndex(-1);
    setMatches([]);
    setError(false);
    if (value.length < MIN_QUERY_LENGTH) { setLoading(false); return; }
    let current = true;
    setLoading(true);
    const timer = window.setTimeout(() => {
      void searchUsers(value, 6).then(rows => {
        if (current) setMatches(rows);
      }).catch(() => {
        if (current) setError(true);
      }).finally(() => {
        if (current) setLoading(false);
      });
    }, 250);
    return () => { current = false; window.clearTimeout(timer); };
  }, [query]);

  useEffect(() => {
    if (!open) return;
    const onOutside = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onOutside);
    return () => document.removeEventListener('mousedown', onOutside);
  }, [open]);

  const goToProfile = (userId: string) => {
    setOpen(false);
    activeIndexRef.current = -1;
    setActiveIndex(-1);
    router.push(`/profile/${encodeURIComponent(userId)}`);
  };

  const showSuggestions = open && query.trim().length >= MIN_QUERY_LENGTH;

  return <div className={styles.root} ref={rootRef}>
    <form className="global-search-pill" role="search" onSubmit={event => {
      event.preventDefault();
      const selected = matches[activeIndexRef.current];
      if (selected) {
        goToProfile(selected.id);
      } else if (query.trim()) {
        setOpen(false);
        router.push(`/search?q=${encodeURIComponent(query.trim())}`);
      }
    }}>
      <IconSearch size={16} className="search-pill-icon" />
      <input
        type="search"
        className="search-pill-input"
        placeholder="Tìm kiếm sinh viên"
        value={query}
        onChange={event => { activeIndexRef.current = -1; setActiveIndex(-1); setQuery(event.target.value); setOpen(true); }}
        onFocus={() => { if (query.trim().length >= MIN_QUERY_LENGTH) setOpen(true); }}
        onKeyDown={event => {
          if (event.key === 'Escape') { setOpen(false); activeIndexRef.current = -1; setActiveIndex(-1); }
          if (event.key === 'ArrowDown' && showSuggestions && matches.length) {
            event.preventDefault();
            const next = Math.min(activeIndexRef.current + 1, matches.length - 1);
            activeIndexRef.current = next;
            setActiveIndex(next);
          }
          if (event.key === 'ArrowUp' && showSuggestions && matches.length) {
            event.preventDefault();
            const next = Math.max(activeIndexRef.current - 1, -1);
            activeIndexRef.current = next;
            setActiveIndex(next);
          }
        }}
        role="combobox"
        aria-label="Tìm kiếm sinh viên"
        aria-autocomplete="list"
        aria-expanded={showSuggestions}
        aria-controls={showSuggestions && matches.length ? 'global-user-search-results' : undefined}
        aria-activedescendant={activeIndex >= 0 && showSuggestions ? `global-user-search-item-${activeIndex}` : undefined}
      />
    </form>

    {showSuggestions && <div className={styles.dropdown}>
      <div className={styles.heading}>Gợi ý sinh viên</div>
      {loading ? <p className={styles.state}>Đang tìm kiếm…</p> : error ? <p className={styles.state}>Chưa thể tìm kiếm. Hãy thử lại.</p> : matches.length ? (
        <ul id="global-user-search-results" role="listbox" className={styles.list}>
          {matches.map((user, index) => <li key={user.id} id={`global-user-search-item-${index}`} role="option" aria-selected={activeIndex === index}>
            <button type="button" className={`${styles.item} ${activeIndex === index ? styles.active : ''}`} onMouseEnter={() => { activeIndexRef.current = index; setActiveIndex(index); }} onClick={() => goToProfile(user.id)}>
              <UserAvatar src={user.avatar} name={user.name} imageClassName={styles.avatar} fallbackClassName={`${styles.avatar} user-avatar-initials`} />
              <span className={styles.identity}><strong>{user.name}</strong><small>{user.studentCode || user.username}{user.friendshipStatus === 'self' ? ' · Trang cá nhân của bạn' : ''}{user.accountStatus && user.accountStatus !== 'ACTIVE' ? ' · Tạm ngừng hoạt động' : ''}</small></span>
            </button>
          </li>)}
        </ul>
      ) : <p className={styles.state}>Không tìm thấy sinh viên phù hợp.</p>}
      <button type="button" className={styles.more} onClick={() => { setOpen(false); router.push(`/search?q=${encodeURIComponent(query.trim())}`); }}>Xem tất cả kết quả <span aria-hidden="true">→</span></button>
    </div>}
  </div>;
}
