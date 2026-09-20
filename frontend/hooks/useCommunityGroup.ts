"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchFeed, fetchGroups } from "@/lib/api";
import type { Post } from "@/types/post";
import type { EventItem, EventUserStatus, GroupHeaderData, GroupTab, MarketItem, RoomItem } from "@/types/group";

const EMPTY_HEADER: GroupHeaderData = {
  id: "community", title: "Cộng đồng sinh viên HVNH",
  description: "Các bài đăng Pass đồ, phòng trọ và sự kiện từ cộng đồng HVNH Hub.",
  bannerImage: "", avatarImage: "BAV", memberCount: 0, postCount: 0, isJoined: false,
};

const imageOf = (post: Post) => post.media?.find((item) => item.type === "image")?.url || "";

function marketItem(post: Post): MarketItem {
  const condition = post.marketListing?.condition;
  return {
    id: post.id, title: post.content || "Bài đăng Pass đồ",
    price: post.marketListing?.price || "Liên hệ",
    condition: condition === "Brand New" || condition === "Like New" ? condition : "Used",
    location: post.marketListing?.location || "Chưa cập nhật địa điểm",
    sellerName: post.author.name, sellerAvatar: post.author.avatar,
    image: imageOf(post), category: "Bài đăng cộng đồng", status: "available",
    createdAt: post.createdAt,
  };
}

function roomItem(post: Post): RoomItem {
  return {
    id: post.id, title: post.content || "Bài đăng phòng trọ",
    rentPerMonth: post.roomListing?.rentPerMonth || "Liên hệ",
    area: post.roomListing?.area || "Chưa cập nhật",
    address: post.roomListing?.location || "Chưa cập nhật địa chỉ",
    distanceToSchool: "Chưa cập nhật", amenities: post.roomListing?.amenities || [],
    status: "available", landlordName: post.author.name, landlordPhone: "",
    image: imageOf(post), createdAt: post.createdAt,
  };
}

function eventItem(post: Post): EventItem {
  const parsed = post.eventListing?.eventDate ? new Date(post.eventListing.eventDate) : null;
  const date = parsed && !Number.isNaN(parsed.getTime()) ? parsed : null;
  return {
    id: post.id, title: post.content || "Sự kiện HVNH",
    day: date ? String(date.getDate()).padStart(2, "0") : "--",
    month: date ? `Tháng ${date.getMonth() + 1}` : "Chưa cập nhật",
    time: post.eventListing?.eventTime || "Chưa cập nhật",
    location: post.eventListing?.location || "Chưa cập nhật địa điểm",
    organizer: post.eventListing?.organizer || post.author.name,
    coverImage: imageOf(post), goingCount: 0, interestedCount: 0,
    userStatus: null, createdAt: post.createdAt,
  };
}

export function useCommunityGroup() {
  const [activeTab, setActiveTab] = useState<GroupTab>("market");
  const [headerData, setHeaderData] = useState<GroupHeaderData>(EMPTY_HEADER);
  const [posts, setPosts] = useState<Post[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [marketConditionFilter, setMarketConditionFilter] = useState("all");
  const [marketStatusFilter, setMarketStatusFilter] = useState("all");
  const [roomStatusFilter, setRoomStatusFilter] = useState("all");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [feed, groups] = await Promise.all([fetchFeed(100), fetchGroups()]);
      setPosts(feed);
      setHeaderData({
        ...EMPTY_HEADER,
        memberCount: groups.reduce((total, group) => total + group.member_count, 0),
        postCount: feed.filter((post) => ["market", "roommate", "event"].includes(post.category)).length,
        isJoined: groups.some((group) => group.membership === "MEMBER" || group.membership === "ADMIN"),
      });
    } catch (reason) {
      setPosts([]); setHeaderData(EMPTY_HEADER);
      setError(reason instanceof Error ? reason.message : "Không thể tải dữ liệu cộng đồng.");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const marketItems = useMemo(() => posts.filter((post) => post.category === "market").map(marketItem).filter((item) => {
    const query = searchQuery.toLocaleLowerCase("vi");
    return (!query || item.title.toLocaleLowerCase("vi").includes(query) || item.location.toLocaleLowerCase("vi").includes(query))
      && (marketConditionFilter === "all" || item.condition === marketConditionFilter)
      && (marketStatusFilter === "all" || item.status === marketStatusFilter);
  }), [posts, searchQuery, marketConditionFilter, marketStatusFilter]);

  const roomItems = useMemo(() => posts.filter((post) => post.category === "roommate").map(roomItem).filter((item) => {
    const query = searchQuery.toLocaleLowerCase("vi");
    return (!query || item.title.toLocaleLowerCase("vi").includes(query) || item.address.toLocaleLowerCase("vi").includes(query))
      && (roomStatusFilter === "all" || item.status === roomStatusFilter);
  }), [posts, searchQuery, roomStatusFilter]);

  const eventItems = useMemo(() => posts.filter((post) => post.category === "event").map(eventItem).filter((item) => {
    const query = searchQuery.toLocaleLowerCase("vi");
    return !query || item.title.toLocaleLowerCase("vi").includes(query) || item.location.toLocaleLowerCase("vi").includes(query);
  }), [posts, searchQuery]);

  return {
    activeTab, setActiveTab, headerData, toggleJoinGroup: () => undefined,
    searchQuery, setSearchQuery, marketItems, marketConditionFilter, setMarketConditionFilter,
    marketStatusFilter, setMarketStatusFilter, toggleSoldStatus: () => undefined,
    roomItems, roomStatusFilter, setRoomStatusFilter, eventItems,
    toggleEventStatus: (_eventId: string, _targetStatus: EventUserStatus) => undefined,
    loading, error, refetch: load,
  };
}
