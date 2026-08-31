"use client";

import React from "react";
import { EventItem, EventUserStatus } from "@/types/group";
import { IconSearch, IconEvent } from "@/components/ui/Icons";

interface EventsCardMatrixProps {
  items: EventItem[];
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onToggleStatus: (eventId: string, status: EventUserStatus) => void;
}

export default function EventsCardMatrix({
  items,
  searchQuery,
  onSearchChange,
  onToggleStatus,
}: EventsCardMatrixProps) {
  return (
    <section className="group-module-section" aria-label="Sự Kiện Sinh Viên HVNH">
      {/* Filter Bar */}
      <div className="matrix-filter-bar">
        <div className="filter-search-box">
          <IconSearch size={16} color="#0F172A" className="search-icon-svg" />
          <input
            type="text"
            placeholder="Tìm kiếm sự kiện, workshop, giải đấu..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
          />
          {searchQuery && (
            <button
              type="button"
              className="clear-search-btn"
              onClick={() => onSearchChange("")}
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Empty State */}
      {items.length === 0 && (
        <div className="matrix-empty-state">
          <div className="empty-icon"><IconEvent size={32} color="#64748B" /></div>
          <h3>Chưa có sự kiện phù hợp</h3>
          <p>Thử tìm kiếm với từ khóa khác hoặc theo dõi lại sau.</p>
        </div>
      )}

      {/* Events Grid Matrix */}
      <div className="events-grid-matrix">
        {items.map((event) => (
          <article key={event.id} className="event-card">
            {/* Cover Image & Square Calendar Date Badge */}
            <div className="event-cover-wrap">
              <img src={event.coverImage} alt={event.title} loading="lazy" />

              {/* Calendar Date Block Badge */}
              <div className="calendar-date-badge">
                <span className="date-day">{event.day}</span>
                <span className="date-month">{event.month}</span>
              </div>

              <div className="event-attendee-pill">
                <span>{event.goingCount} người sẽ tham gia · {event.interestedCount} quan tâm</span>
              </div>
            </div>

            {/* Event Body Meta */}
            <div className="event-card-body">
              <div className="event-time-row">
                <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="#64748B" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline-block', verticalAlign: 'middle', marginRight: 4 }}>
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                <span>{event.time}</span>
              </div>

              <h3 className="event-card-title">{event.title}</h3>

              <div className="event-location-row">
                <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="#64748B" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline-block', verticalAlign: 'middle', marginRight: 4 }}>
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                  <circle cx="12" cy="10" r="3" />
                </svg>
                <span>{event.location}</span>
              </div>

              <div className="event-organizer-row" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <img src="/assets/logo.png" alt={event.organizer} className="author-avatar-img" />
                <span>Tổ chức bởi: <strong>{event.organizer}</strong></span>
              </div>

              {/* Event Action Buttons */}
              <div className="event-card-actions">
                <button
                  type="button"
                  className={`event-action-btn going-btn ${
                    event.userStatus === "going" ? "active" : ""
                  }`}
                  onClick={() => onToggleStatus(event.id, "going")}
                >
                  {event.userStatus === "going" ? "✓ Sẽ tham gia" : "+ Tham gia"}
                </button>

                <button
                  type="button"
                  className={`event-action-btn interested-btn ${
                    event.userStatus === "interested" ? "active" : ""
                  }`}
                  onClick={() => onToggleStatus(event.id, "interested")}
                >
                  {event.userStatus === "interested" ? "Đã quan tâm" : "Quan tâm"}
                </button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

