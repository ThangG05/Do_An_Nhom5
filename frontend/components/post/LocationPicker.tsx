"use client";

import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";

import { reverseGeocode, searchLocations, type LocationSuggestion } from "@/lib/api";
import type { PostLocation } from "@/types/post";

interface LocationPickerProps {
  open: boolean;
  onClose: () => void;
  onSelect: (location: PostLocation) => void;
}

const toPostLocation = (result: LocationSuggestion): PostLocation => ({
  name: result.name,
  address: result.address,
  latitude: result.latitude,
  longitude: result.longitude,
});

export default function LocationPicker({ open, onClose, onSelect }: LocationPickerProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<LocationSuggestion[]>([]);
  const [activeResult, setActiveResult] = useState(0);
  const [isSearching, setIsSearching] = useState(false);
  const [isLocating, setIsLocating] = useState(false);
  const [message, setMessage] = useState("");
  const [messageTone, setMessageTone] = useState<"error" | "info">("info");
  const searchRequestId = useRef(0);
  const gpsRequestId = useRef(0);
  const activeFlow = useRef<"search" | "gps" | null>(null);

  useEffect(() => {
    if (!open) {
      gpsRequestId.current += 1;
      searchRequestId.current += 1;
      activeFlow.current = null;
      setIsLocating(false);
      return;
    }
    setQuery("");
    setResults([]);
    setMessage("");
    setMessageTone("info");
    activeFlow.current = null;
    searchRequestId.current += 1;
  }, [open]);

  useEffect(() => {
    const normalized = query.trim();
    if (!open || normalized.length < 2) {
      setResults([]);
      setIsSearching(false);
      return;
    }
    const requestId = ++searchRequestId.current;
    activeFlow.current = "search";
    const timeout = window.setTimeout(async () => {
      if (activeFlow.current !== "search" || requestId !== searchRequestId.current) return;
      setIsSearching(true);
      setMessage("");
      setMessageTone("info");
      try {
        const found = await searchLocations(normalized);
        if (activeFlow.current === "search" && requestId === searchRequestId.current) {
          setResults(found);
          setActiveResult(0);
        }
      } catch (error) {
        if (activeFlow.current === "search" && requestId === searchRequestId.current) {
          setResults([]);
          setMessage(error instanceof Error ? error.message : "Không thể tìm địa điểm.");
          setMessageTone("error");
        }
      } finally {
        if (requestId === searchRequestId.current) setIsSearching(false);
      }
    }, 280);
    return () => window.clearTimeout(timeout);
  }, [open, query]);

  if (!open) return null;

  const choose = (result: LocationSuggestion) => {
    activeFlow.current = null;
    onSelect(toPostLocation(result));
    onClose();
  };

  const useCurrentLocation = () => {
    if (!window.isSecureContext) {
      setMessage("Vị trí hiện tại cần HTTPS hoặc localhost. Bạn vẫn có thể tìm địa điểm bên dưới.");
      setMessageTone("error");
      return;
    }
    if (!navigator.geolocation) {
      setMessage("Trình duyệt này không hỗ trợ định vị. Bạn có thể tìm địa điểm bên dưới.");
      setMessageTone("error");
      return;
    }
    // A single bounded GPS request prevents the UI waiting through several
    // consecutive browser timeouts. Typing a place can still be used instead.
    searchRequestId.current += 1;
    const requestId = ++gpsRequestId.current;
    activeFlow.current = "gps";
    setIsSearching(false);
    setResults([]);
    setIsLocating(true);
    setMessage("");
    setMessageTone("info");
    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        if (requestId !== gpsRequestId.current) return;
        try {
          const result = await reverseGeocode(coords.latitude, coords.longitude);
          if (requestId !== gpsRequestId.current) return;
          if (!result) {
            setMessage("Chưa xác định được địa chỉ đủ chính xác. Hãy tìm địa điểm theo tên.");
            setMessageTone("info");
            return;
          }
          onSelect(toPostLocation(result));
          onClose();
        } catch {
          if (requestId === gpsRequestId.current) {
            setMessage("Chưa tra cứu được địa chỉ. Hãy tìm địa điểm theo tên.");
            setMessageTone("info");
          }
        } finally {
          setIsLocating(false);
        }
      },
      (error) => {
        if (requestId !== gpsRequestId.current) return;
        if (error.code !== error.PERMISSION_DENIED && error.code !== error.TIMEOUT) {
          setMessage("");
          setMessageTone("info");
          setIsLocating(false);
          return;
        }
        const detail = error.code === error.PERMISSION_DENIED
          ? "Bạn chưa cho phép trình duyệt truy cập vị trí. Hãy bật quyền vị trí hoặc tìm địa điểm theo tên."
          : "Trình duyệt không lấy được vị trí trong 15 giây. Hãy thử lại hoặc tìm địa điểm theo tên.";
        setMessage(detail);
        setMessageTone("error");
        setIsLocating(false);
      },
      { enableHighAccuracy: false, timeout: 15_000, maximumAge: 120_000 },
    );
  };

  const handleQueryChange = (value: string) => {
    // If the user starts typing while GPS is resolving, prefer their explicit
    // search and ignore any late location callback.
    gpsRequestId.current += 1;
    searchRequestId.current += 1;
    activeFlow.current = "search";
    setIsLocating(false);
    setMessage("");
    setMessageTone("info");
    setQuery(value);
  };

  const handleSearchKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (!results.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveResult(index => (index + 1) % results.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveResult(index => (index - 1 + results.length) % results.length);
    } else if (event.key === "Enter") {
      event.preventDefault();
      choose(results[activeResult] || results[0]);
    }
  };

  return (
    <div className="location-picker-backdrop" role="presentation" onClick={onClose}>
      <section className="location-picker" role="dialog" aria-modal="true" aria-labelledby="location-picker-title" onClick={(event) => event.stopPropagation()}>
        <div className="location-picker-header"><div><h3 id="location-picker-title">Thêm vị trí</h3><p>Chỉ chia sẻ vị trí khi bạn chủ động chọn.</p></div><button type="button" className="location-picker-close" onClick={onClose} aria-label="Đóng chọn vị trí">×</button></div>
        <button type="button" className="current-location-button" disabled={isLocating} onClick={useCurrentLocation}><span aria-hidden="true">⌖</span> {isLocating ? "Đang xác định vị trí..." : "Dùng vị trí hiện tại"}</button>
        <label className="location-search-label" htmlFor="post-location-search">Hoặc tìm địa điểm</label>
        <input id="post-location-search" autoFocus className="location-search-input" placeholder="Ví dụ: Học viện Ngân hàng, Hà Nội" value={query} onChange={(event) => handleQueryChange(event.target.value)} onKeyDown={handleSearchKeyDown} role="combobox" aria-autocomplete="list" aria-controls="post-location-results" aria-expanded={results.length > 0} />
        {isSearching && <p className="location-picker-status">Đang tìm địa điểm…</p>}
        {message && <p className={`location-picker-message ${messageTone}`} role="status">{message}</p>}
        {results.length > 0 && <div className="location-results" id="post-location-results" role="listbox" aria-label="Gợi ý địa điểm">{results.map((result, index) => <button type="button" role="option" aria-selected={index === activeResult} key={`${result.latitude}-${result.longitude}-${result.address}`} className={`location-result${index === activeResult ? " active" : ""}`} onMouseEnter={() => setActiveResult(index)} onClick={() => choose(result)}><span aria-hidden="true">📍</span><span><strong>{result.name}</strong><small>{result.address}</small></span></button>)}</div>}
        {query.trim().length >= 2 && !isSearching && !message && results.length === 0 && <p className="location-picker-status">Không có địa điểm phù hợp tại Việt Nam.</p>}
      </section>
    </div>
  );
}
