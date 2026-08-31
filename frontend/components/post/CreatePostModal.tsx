"use client";

import React, { useRef, useEffect } from "react";
import { PostCategory, PostPrivacy } from "@/types/post";
import { UseCreatePostReturn } from "@/hooks/useCreatePost";

interface CreatePostModalProps {
  postState: UseCreatePostReturn;
}

const CATEGORY_OPTIONS: { val: PostCategory; label: string; icon: string }[] = [
  { val: "general", label: "Thảo luận chung", icon: "💬" },
  { val: "market", label: "Pass đồ / Chợ SV", icon: "🛒" },
  { val: "roommate", label: "Ghép phòng / Tìm trọ", icon: "🏠" },
  { val: "event", label: "Sự kiện HVNH", icon: "📅" },
  { val: "study", label: "Tài liệu Học tập", icon: "📚" },
];

const PRIVACY_OPTIONS: { val: PostPrivacy; label: string; icon: string }[] = [
  { val: "public", label: "Công khai", icon: "🌐" },
  { val: "friends", label: "Bạn bè", icon: "👥" },
];

const AMENITY_TAGS = [
  "Điều hòa",
  "Nóng lạnh",
  "Máy giặt",
  "Ban công",
  "Tủ lạnh",
  "Khép kín",
  "Không chung chủ",
  "Có chỗ để xe",
];

export default function CreatePostModal({ postState }: CreatePostModalProps) {
  const {
    isOpen,
    closeModal,
    content,
    setContent,
    category,
    setCategory,
    privacy,
    setPrivacy,
    mediaList,
    addMediaFiles,
    removeMedia,
    marketListing,
    setMarketListing,
    roomListing,
    setRoomListing,
    eventListing,
    setEventListing,
    location,
    setLocation,
    isSubmitting,
    error,
    submitPost,
  } = postState;

  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Close modal on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        closeModal();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, closeModal]);

  // Focus textarea when modal opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addMediaFiles(e.target.files);
    }
  };

  const toggleAmenity = (amenity: string) => {
    setRoomListing((prev) => {
      const exists = prev.amenities.includes(amenity);
      return {
        ...prev,
        amenities: exists
          ? prev.amenities.filter((a) => a !== amenity)
          : [...prev.amenities, amenity],
      };
    });
  };

  const getPlaceholder = () => {
    switch (category) {
      case "market":
        return "Mô tả sản phẩm bạn muốn pass (tình trạng, lý do nhượng lại, liên hệ)...";
      case "roommate":
        return "Mô tả yêu cầu ở ghép hoặc thông tin phòng trọ cho thuê...";
      case "event":
        return "Chi tiết về sự kiện, chương trình hoặc hoạt động câu lạc bộ...";
      case "study":
        return "Chia sẻ đề thi, giáo trình, tài liệu môn học...";
      default:
        return "Bạn đang nghĩ gì thế, sinh viên HVNH?";
    }
  };

  return (
    <div
      className="create-post-overlay"
      onClick={closeModal}
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-post-title"
    >
      <div
        className="create-post-modal"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="modal-header">
          <h2 id="create-post-title">Tạo bài viết mới</h2>
          <button
            type="button"
            className="modal-close-btn"
            onClick={closeModal}
            aria-label="Đóng bảng tạo bài viết"
          >
            ✕
          </button>
        </div>

        <div className="modal-body">
          {/* Author Header */}
          <div className="author-row">
            <div className="author-avatar" aria-hidden="true">
              SV
            </div>
            <div className="author-meta">
              <div className="author-name-row">
                <strong>Sinh viên HVNH</strong>
                <span className="verified-badge" title="Tài khoản @hvnh.edu.vn đã xác thực">
                  ✓ HVNH
                </span>
              </div>

              <div className="selector-group">
                {/* Category Dropdown */}
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value as PostCategory)}
                  aria-label="Chọn chuyên mục đăng bài"
                  className="custom-select"
                >
                  {CATEGORY_OPTIONS.map((opt) => (
                    <option key={opt.val} value={opt.val}>
                      {opt.icon} {opt.label}
                    </option>
                  ))}
                </select>

                {/* Privacy Dropdown */}
                <select
                  value={privacy}
                  onChange={(e) => setPrivacy(e.target.value as PostPrivacy)}
                  aria-label="Chọn quyền riêng tư"
                  className="custom-select privacy-select"
                >
                  {PRIVACY_OPTIONS.map((opt) => (
                    <option key={opt.val} value={opt.val}>
                      {opt.icon} {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Specialized Fields: Market (Pass đồ) */}
          {category === "market" && (
            <div className="specialized-box market-box">
              <div className="box-title">🛒 Thông tin sản phẩm Pass đồ</div>
              <div className="form-grid-2">
                <div className="field-unit">
                  <label htmlFor="market-price">Giá thanh lý (VNĐ)</label>
                  <input
                    id="market-price"
                    type="text"
                    placeholder="VD: 150.000đ hoặc Thỏa thuận"
                    value={marketListing.price}
                    onChange={(e) =>
                      setMarketListing((prev) => ({ ...prev, price: e.target.value }))
                    }
                  />
                </div>
                <div className="field-unit">
                  <label htmlFor="market-condition">Tình trạng đồ</label>
                  <select
                    id="market-condition"
                    value={marketListing.condition}
                    onChange={(e) =>
                      setMarketListing((prev) => ({ ...prev, condition: e.target.value }))
                    }
                    className="custom-select"
                  >
                    <option value="Mới 100% (Chưa dùng)">Mới 100% (Chưa dùng)</option>
                    <option value="Đã qua sử dụng (Tốt)">Đã qua sử dụng (Tốt)</option>
                    <option value="Cũ / Cần sang tay nhanh">Cũ / Cần sang tay nhanh</option>
                  </select>
                </div>
              </div>
              <div className="field-unit" style={{ marginTop: "10px" }}>
                <label htmlFor="market-location">Khu vực giao dịch</label>
                <input
                  id="market-location"
                  type="text"
                  placeholder="VD: KTX HVNH, Cổng Chùa Bộc, Tòa D..."
                  value={marketListing.location}
                  onChange={(e) =>
                    setMarketListing((prev) => ({ ...prev, location: e.target.value }))
                  }
                />
              </div>
            </div>
          )}

          {/* Specialized Fields: Roommate (Ghép phòng / Phòng trọ) */}
          {category === "roommate" && (
            <div className="specialized-box room-box">
              <div className="box-title">🏠 Thông tin Phòng trọ / Ở ghép</div>
              <div className="form-grid-2">
                <div className="field-unit">
                  <label htmlFor="room-price">Giá thuê/tháng</label>
                  <input
                    id="room-price"
                    type="text"
                    placeholder="VD: 2.500.000đ/tháng"
                    value={roomListing.rentPerMonth}
                    onChange={(e) =>
                      setRoomListing((prev) => ({ ...prev, rentPerMonth: e.target.value }))
                    }
                  />
                </div>
                <div className="field-unit">
                  <label htmlFor="room-area">Diện tích (m²)</label>
                  <input
                    id="room-area"
                    type="text"
                    placeholder="VD: 25 m²"
                    value={roomListing.area}
                    onChange={(e) =>
                      setRoomListing((prev) => ({ ...prev, area: e.target.value }))
                    }
                  />
                </div>
              </div>
              <div className="field-unit" style={{ marginTop: "10px" }}>
                <label>Tiện ích phòng:</label>
                <div className="tags-flex">
                  {AMENITY_TAGS.map((tag) => {
                    const selected = roomListing.amenities.includes(tag);
                    return (
                      <button
                        key={tag}
                        type="button"
                        className={`tag-chip ${selected ? "active" : ""}`}
                        onClick={() => toggleAmenity(tag)}
                      >
                        {selected ? "✓ " : "+ "}
                        {tag}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Specialized Fields: Event (Sự kiện) */}
          {category === "event" && (
            <div className="specialized-box event-box">
              <div className="box-title">📅 Thông tin Sự kiện HVNH</div>
              <div className="form-grid-2">
                <div className="field-unit">
                  <label htmlFor="event-date">Ngày diễn ra</label>
                  <input
                    id="event-date"
                    type="date"
                    value={eventListing.eventDate}
                    onChange={(e) =>
                      setEventListing((prev) => ({ ...prev, eventDate: e.target.value }))
                    }
                  />
                </div>
                <div className="field-unit">
                  <label htmlFor="event-time">Thời gian</label>
                  <input
                    id="event-time"
                    type="text"
                    placeholder="VD: 18:00 - 21:00"
                    value={eventListing.eventTime}
                    onChange={(e) =>
                      setEventListing((prev) => ({ ...prev, eventTime: e.target.value }))
                    }
                  />
                </div>
              </div>
              <div className="form-grid-2" style={{ marginTop: "10px" }}>
                <div className="field-unit">
                  <label htmlFor="event-location">Địa điểm</label>
                  <input
                    id="event-location"
                    type="text"
                    placeholder="VD: Hội trường D1, Sân bóng..."
                    value={eventListing.location}
                    onChange={(e) =>
                      setEventListing((prev) => ({ ...prev, location: e.target.value }))
                    }
                  />
                </div>
                <div className="field-unit">
                  <label htmlFor="event-organizer">Đơn vị tổ chức</label>
                  <input
                    id="event-organizer"
                    type="text"
                    placeholder="VD: Đoàn Thanh niên, CLB..."
                    value={eventListing.organizer}
                    onChange={(e) =>
                      setEventListing((prev) => ({ ...prev, organizer: e.target.value }))
                    }
                  />
                </div>
              </div>
            </div>
          )}

          {/* Main Text Content Input */}
          <div className="post-input-container">
            <textarea
              ref={textareaRef}
              className="post-textarea"
              placeholder={getPlaceholder()}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={4}
            />
          </div>

          {/* Location Tag Badge */}
          {location && (
            <div className="location-badge">
              📍 <span>{location}</span>
              <button
                type="button"
                onClick={() => setLocation("")}
                aria-label="Xóa địa điểm"
              >
                ✕
              </button>
            </div>
          )}

          {/* Media Attachments Preview Grid */}
          {mediaList.length > 0 && (
            <div className="media-preview-grid">
              {mediaList.map((m) => (
                <div key={m.id} className="preview-item">
                  {m.type === "image" ? (
                    <img src={m.url} alt="Xem trước ảnh đăng bài" />
                  ) : (
                    <video src={m.url} controls />
                  )}
                  <button
                    type="button"
                    className="remove-media-btn"
                    onClick={() => removeMedia(m.id)}
                    aria-label="Xóa tệp này"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Add-to-post Action Toolbar */}
          <div className="add-to-post-bar">
            <span>Thêm vào bài viết của bạn</span>
            <div className="action-icons">
              {/* Photo/Video upload trigger */}
              <button
                type="button"
                className="action-icon-btn photo-btn"
                title="Tải ảnh / video"
                onClick={() => fileInputRef.current?.click()}
              >
                🖼️ <small>Ảnh/Video</small>
              </button>

              {/* Tag activity / location trigger */}
              <button
                type="button"
                className="action-icon-btn location-btn"
                title="Thêm địa điểm"
                onClick={() => {
                  const loc = prompt("Nhập địa điểm (ví dụ: Thư viện HVNH):");
                  if (loc) setLocation(loc);
                }}
              >
                📍 <small>Địa điểm</small>
              </button>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*,video/*"
              multiple
              style={{ display: "none" }}
              onChange={handleFileChange}
            />
          </div>

          {/* Error Banner */}
          {error && <div className="post-error-banner">{error}</div>}
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <button
            type="button"
            className="submit-post-btn"
            disabled={isSubmitting || (!content.trim() && mediaList.length === 0)}
            onClick={submitPost}
          >
            {isSubmitting ? (
              <span className="spinner-wrap">
                <span className="inline-spinner" /> Đang đăng...
              </span>
            ) : (
              "Đăng bài viết"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
