"use client";

import { useEffect, useRef, useState } from "react";

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
        if (activeFlow.current === "search" && requestId === searchRequestId.current) setResults(found);
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
    onSelect(toPostLocation(result));
    onClose();
  };

  const useCurrentLocation = () => {
    if (!navigator.geolocation) {
      setMessage("Thiết bị hoặc trình duyệt này không hỗ trợ định vị.");
      return;
    }
    // Invalidate a pending search. Otherwise its late failure can paint a red
    // error while the browser is still correctly resolving GPS.
    searchRequestId.current += 1;
    const requestId = ++gpsRequestId.current;
    activeFlow.current = "gps";
    setIsSearching(false);
    setResults([]);
    setIsLocating(true);
    setMessage("");
    setMessageTone("info");
    const resolvePosition = () => {
      if (requestId !== gpsRequestId.current) return;
      navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        if (requestId !== gpsRequestId.current) return;
        try {
          const result = await reverseGeocode(coords.latitude, coords.longitude);
          onSelect(result ? toPostLocation(result) : {
            name: "Vị trí hiện tại", address: "Vị trí do bạn chia sẻ", latitude: coords.latitude, longitude: coords.longitude,
          });
          onClose();
        } catch {
          onSelect({ name: "Vị trí hiện tại", address: "Vị trí do bạn chia sẻ", latitude: coords.latitude, longitude: coords.longitude });
          onClose();
        } finally {
          setIsLocating(false);
        }
      },
      (error) => {
        if (requestId !== gpsRequestId.current) return;
        const denied = error.code === error.PERMISSION_DENIED;
        if (denied) {
          // The user asked for a silent GPS flow. Re-enable the button
          // without adding an alert; they can grant the permission and retry.
          setMessage("");
          setIsLocating(false);
          return;
        }
        // Keep waiting and retry silently. Windows location providers often
        // need several attempts after waking from sleep or starting Chrome.
        window.setTimeout(resolvePosition, 1_500);
      },
      // Ten seconds is often insufficient on desktop devices after a fresh
      // permission grant. Keep the UI in a loading state rather than showing
      // a false error while the operating system is still acquiring a fix.
      { enableHighAccuracy: false, timeout: 30_000, maximumAge: 60_000 },
      );
    };
    resolvePosition();
  };

  return (
    <div className="location-picker-backdrop" role="presentation" onClick={onClose}>
      <section className="location-picker" role="dialog" aria-modal="true" aria-labelledby="location-picker-title" onClick={(event) => event.stopPropagation()}>
        <div className="location-picker-header"><div><h3 id="location-picker-title">Thêm vị trí</h3><p>Chỉ chia sẻ vị trí khi bạn chủ động chọn.</p></div><button type="button" className="location-picker-close" onClick={onClose} aria-label="Đóng chọn vị trí">×</button></div>
        <button type="button" className="current-location-button" disabled={isLocating} onClick={useCurrentLocation}><span aria-hidden="true">⌖</span> {isLocating ? "Đang xác định vị trí..." : "Dùng vị trí hiện tại"}</button>
        <label className="location-search-label" htmlFor="post-location-search">Hoặc tìm địa điểm</label>
        <input id="post-location-search" autoFocus className="location-search-input" placeholder="Ví dụ: Học viện Ngân hàng, Hà Nội" value={query} onChange={(event) => setQuery(event.target.value)} />
        {isSearching && <p className="location-picker-status">Đang tìm địa điểm…</p>}
        {message && <p className={`location-picker-message ${messageTone}`} role="status">{message}</p>}
        {results.length > 0 && <div className="location-results" role="listbox" aria-label="Gợi ý địa điểm">{results.map((result) => <button type="button" key={`${result.latitude}-${result.longitude}-${result.address}`} className="location-result" onClick={() => choose(result)}><span aria-hidden="true">📍</span><span><strong>{result.name}</strong><small>{result.address}</small></span></button>)}</div>}
        {query.trim().length >= 2 && !isSearching && !message && results.length === 0 && <p className="location-picker-status">Không có địa điểm phù hợp tại Việt Nam.</p>}
      </section>
    </div>
  );
}
