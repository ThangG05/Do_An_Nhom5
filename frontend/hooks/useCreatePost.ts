"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { validatePostDraft } from "@/lib/group-post";
import {
  PostCategory,
  PostPrivacy,
  PostMedia,
  MarketListingData,
  RoomListingData,
  EventListingData,
  StudyListingData,
  PostLocation,
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
  location: PostLocation | null;
  setLocation: (loc: PostLocation | null) => void;
  marketListing: MarketListingData;
  setMarketListing: React.Dispatch<React.SetStateAction<MarketListingData>>;
  roomListing: RoomListingData;
  setRoomListing: React.Dispatch<React.SetStateAction<RoomListingData>>;
  eventListing: EventListingData;
  setEventListing: React.Dispatch<React.SetStateAction<EventListingData>>;
  studyListing: StudyListingData;
  setStudyListing: React.Dispatch<React.SetStateAction<StudyListingData>>;
  isSubmitting: boolean;
  error: string | null;
  submitPost: () => Promise<Post | null>;
  resetForm: () => void;
}

export function useCreatePost(
  onPostCreated?: (payload: CreatePostPayload) => Promise<Post | null>
): UseCreatePostReturn {
  const [isOpen, setIsOpen] = useState(false);
  const [content, setContent] = useState("");
  const [category, setCategory] = useState<PostCategory>("general");
  const [privacy, setPrivacy] = useState<PostPrivacy>("public");
  const [mediaList, setMediaList] = useState<PostMedia[]>([]);
  const [taggedFriends, setTaggedFriends] = useState<string[]>([]);
  const [location, setLocation] = useState<PostLocation | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submittingRef = useRef(false);
  const mediaRef = useRef(mediaList);
  mediaRef.current = mediaList;
  useEffect(() => () => { mediaRef.current.forEach(item => { if (item.url.startsWith('blob:')) URL.revokeObjectURL(item.url); }); }, []);
  const [studyListing, setStudyListing] = useState<StudyListingData>({ subjectName: "" });

  // Specialized listing state defaults
  const [marketListing, setMarketListing] = useState<MarketListingData>({
    price: "",
    productName: "",
    condition: "",
    location: "",
  });

  const [roomListing, setRoomListing] = useState<RoomListingData>({
    rentPerMonth: "",
    area: "",
    amenities: [],
    location: "",
  });

  const [eventListing, setEventListing] = useState<EventListingData>({
    eventName: "",
    eventDate: "",
    eventTime: "",
    location: "",
    organizer: "",
  });

  const openModal = useCallback((initialCategory?: PostCategory) => {
    if (initialCategory) {
      setCategory(initialCategory);
    }
    setIsOpen(true);
    setError(null);
  }, []);

  const closeModal = useCallback(() => {
    if (submittingRef.current) return;
    setIsOpen(false);
  }, []);

  const resetForm = useCallback(() => {
    mediaRef.current.forEach(item => { if (item.url.startsWith('blob:')) URL.revokeObjectURL(item.url); });
    setStudyListing({ subjectName: "" });
    setContent("");
    setCategory("general");
    setPrivacy("public");
    setMediaList([]);
    setTaggedFriends([]);
    setLocation(null);
    setError(null);
    setMarketListing({
      price: "",
      productName: "",
      condition: "",
      location: "",
    });
    setRoomListing({
      rentPerMonth: "",
      area: "",
      amenities: [],
      location: "",
    });
    setEventListing({
      eventName: "",
      eventDate: "",
      eventTime: "",
      location: "",
      organizer: "",
    });
  }, []);

  const addMediaFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files);
    if (fileArray.length + mediaRef.current.length > 10) { setError("Mỗi bài được đính kèm tối đa 10 tệp."); return; }
    const allowed = /\.(jpe?g|png|webp|mp4|webm|mov|mp3|m4a|ogg|wav|pdf|txt|docx?|xlsx?|pptx?|zip)$/i;
    if (fileArray.some(file => !allowed.test(file.name) || !file.size)) { setError("Tệp rỗng hoặc định dạng không hỗ trợ. Chọn ảnh JPG/PNG/WebP, video, âm thanh, PDF, Office, TXT hoặc ZIP."); return; }
    const oversized = fileArray.find(file => file.size > (/\.(jpe?g|png|webp)$/i.test(file.name) ? 5 : /\.(mp4|webm|mov)$/i.test(file.name) ? 100 : 25) * 1024 * 1024);
    if (oversized) { setError(`Tệp ${oversized.name} quá lớn. Ảnh tối đa 5 MB, video 100 MB, âm thanh và tài liệu 25 MB.`); return; }
    setError(null);
    const newMedia: PostMedia[] = fileArray.map((file, idx) => ({
      id: `${Date.now()}-${idx}-${Math.random().toString(36).substring(2, 7)}`,
      url: URL.createObjectURL(file),
      type: file.type.startsWith("video/") ? "video" : file.type.startsWith("audio/") ? "audio" : file.type.startsWith("image/") ? "image" : "file",
      name: file.name,
      size: file.size,
      file,
      uploadProgress: 0,
      uploadStatus: "pending",
    }));
    setMediaList((prev) => [...prev, ...newMedia]);
  }, []);

  const removeMedia = useCallback((id: string) => {
    setMediaList((prev) => {const removed=prev.find(item=>item.id===id);if(removed?.url.startsWith('blob:'))URL.revokeObjectURL(removed.url);return prev.filter((m) => m.id !== id);});
  }, []);

  const submitPost = useCallback(async (): Promise<Post | null> => {
    if (submittingRef.current) return null;
    const errors = validatePostDraft({ content, category, marketListing, roomListing, eventListing, studyListing }, mediaList.length);
    if (Object.keys(errors).length) {
      setError(Object.values(errors)[0]);
      return null;
    }
    submittingRef.current = true;
    setIsSubmitting(true);
    setError(null);

    try {
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
        studyListing: category === "study" ? studyListing : undefined,
        onUploadProgress: (mediaId, progress, status, uploadError, uploadedMediaId) => setMediaList(previous => previous.map(item => item.id === mediaId ? {...item, uploadProgress: progress, uploadStatus: status, uploadError, uploadedMediaId: uploadedMediaId||item.uploadedMediaId} : item)),
      };

      if (!onPostCreated) throw new Error("Chưa cấu hình API đăng bài.");
      const createdPost = await onPostCreated(payload);
      if (!createdPost) throw new Error("Đăng bài không thành công.");

      resetForm();
      setIsOpen(false);
      return createdPost;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Đăng bài không thành công. Vui lòng thử lại.";
      setError(msg);
      return null;
    } finally {
      submittingRef.current = false;
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
    studyListing,
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
    studyListing,
    setStudyListing,
    isSubmitting,
    error,
    submitPost,
    resetForm,
  };
}
