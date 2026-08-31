"use client";

import { useState, useCallback } from "react";
import {
  PostCategory,
  PostPrivacy,
  PostMedia,
  MarketListingData,
  RoomListingData,
  EventListingData,
  CreatePostPayload,
  Post,
} from "@/types/post";

export interface UseCreatePostReturn {
  isOpen: boolean;
  openModal: (initialCategory?: PostCategory) => void;
  closeModal: () => void;
  content: string;
  setContent: (text: string) => void;
  category: PostCategory;
  setCategory: (cat: PostCategory) => void;
  privacy: PostPrivacy;
  setPrivacy: (p: PostPrivacy) => void;
  mediaList: PostMedia[];
  addMediaFiles: (files: FileList | File[]) => void;
  removeMedia: (id: string) => void;
  taggedFriends: string[];
  setTaggedFriends: React.Dispatch<React.SetStateAction<string[]>>;
  location: string;
  setLocation: (loc: string) => void;
  marketListing: MarketListingData;
  setMarketListing: React.Dispatch<React.SetStateAction<MarketListingData>>;
  roomListing: RoomListingData;
  setRoomListing: React.Dispatch<React.SetStateAction<RoomListingData>>;
  eventListing: EventListingData;
  setEventListing: React.Dispatch<React.SetStateAction<EventListingData>>;
  isSubmitting: boolean;
  error: string | null;
  submitPost: () => Promise<Post | null>;
  resetForm: () => void;
}

export function useCreatePost(
  onPostCreated?: (newPost: Post) => void
): UseCreatePostReturn {
  const [isOpen, setIsOpen] = useState(false);
  const [content, setContent] = useState("");
  const [category, setCategory] = useState<PostCategory>("general");
  const [privacy, setPrivacy] = useState<PostPrivacy>("public");
  const [mediaList, setMediaList] = useState<PostMedia[]>([]);
  const [taggedFriends, setTaggedFriends] = useState<string[]>([]);
  const [location, setLocation] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Specialized listing state defaults
  const [marketListing, setMarketListing] = useState<MarketListingData>({
    price: "",
    condition: "Đã qua sử dụng (Tốt)",
    location: "Ký túc xá HVNH",
  });

  const [roomListing, setRoomListing] = useState<RoomListingData>({
    rentPerMonth: "",
    area: "",
    amenities: ["Điều hòa", "Nóng lạnh", "Khép kín"],
    location: "Chùa Bộc, Đống Đa",
  });

  const [eventListing, setEventListing] = useState<EventListingData>({
    eventDate: "",
    eventTime: "18:00",
    location: "Hội trường D1, HVNH",
    organizer: "CLB Sinh viên HVNH",
  });

  const openModal = useCallback((initialCategory?: PostCategory) => {
    if (initialCategory) {
      setCategory(initialCategory);
    }
    setIsOpen(true);
    setError(null);
  }, []);

  const closeModal = useCallback(() => {
    setIsOpen(false);
  }, []);

  const resetForm = useCallback(() => {
    setContent("");
    setCategory("general");
    setPrivacy("public");
    setMediaList([]);
    setTaggedFriends([]);
    setLocation("");
    setError(null);
    setMarketListing({
      price: "",
      condition: "Đã qua sử dụng (Tốt)",
      location: "Ký túc xá HVNH",
    });
    setRoomListing({
      rentPerMonth: "",
      area: "",
      amenities: ["Điều hòa", "Nóng lạnh", "Khép kín"],
      location: "Chùa Bộc, Đống Đa",
    });
    setEventListing({
      eventDate: "",
      eventTime: "18:00",
      location: "Hội trường D1, HVNH",
      organizer: "CLB Sinh viên HVNH",
    });
  }, []);

  const addMediaFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files);
    const newMedia: PostMedia[] = fileArray.map((file, idx) => ({
      id: `${Date.now()}-${idx}-${Math.random().toString(36).substring(2, 7)}`,
      url: URL.createObjectURL(file),
      type: file.type.startsWith("video/") ? "video" : "image",
      name: file.name,
      size: file.size,
    }));
    setMediaList((prev) => [...prev, ...newMedia]);
  }, []);

  const removeMedia = useCallback((id: string) => {
    setMediaList((prev) => prev.filter((m) => m.id !== id));
  }, []);

  const submitPost = useCallback(async (): Promise<Post | null> => {
    if (!content.trim() && mediaList.length === 0) {
      setError("Vui lòng nhập nội dung bài viết hoặc tải lên hình ảnh.");
      return null;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // Simulate backend API call with delay
      await new Promise((res) => setTimeout(res, 800));

      const payload: CreatePostPayload = {
        content: content.trim(),
        category,
        privacy,
        media: mediaList,
        taggedFriends,
        location: location || undefined,
        marketListing: category === "market" ? marketListing : undefined,
        roomListing: category === "roommate" ? roomListing : undefined,
        eventListing: category === "event" ? eventListing : undefined,
      };

      const createdPost: Post = {
        id: `post-${Date.now()}`,
        author: {
          id: "usr-current",
          name: "Sinh viên HVNH",
          avatar: "SV",
          role: "Sinh viên K25",
          isVerified: true,
        },
        createdAt: "Vừa xong",
        content: payload.content,
        category: payload.category,
        privacy: payload.privacy,
        media: payload.media,
        likesCount: 0,
        commentsCount: 0,
        isLiked: false,
        marketListing: payload.marketListing,
        roomListing: payload.roomListing,
        eventListing: payload.eventListing,
      };

      if (onPostCreated) {
        onPostCreated(createdPost);
      }

      resetForm();
      closeModal();
      return createdPost;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Đăng bài không thành công. Vui lòng thử lại.";
      setError(msg);
      return null;
    } finally {
      setIsSubmitting(false);
    }
  }, [
    content,
    mediaList,
    category,
    privacy,
    taggedFriends,
    location,
    marketListing,
    roomListing,
    eventListing,
    onPostCreated,
    resetForm,
    closeModal,
  ]);

  return {
    isOpen,
    openModal,
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
    taggedFriends,
    setTaggedFriends,
    location,
    setLocation,
    marketListing,
    setMarketListing,
    roomListing,
    setRoomListing,
    eventListing,
    setEventListing,
    isSubmitting,
    error,
    submitPost,
    resetForm,
  };
}
