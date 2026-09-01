"use client";

import { useState, useCallback, useMemo } from "react";
import {
  GroupTab,
  MarketItem,
  RoomItem,
  EventItem,
  GroupHeaderData,
  EventUserStatus,
} from "@/types/group";

const INITIAL_HEADER_DATA: GroupHeaderData = {
  id: "grp-hvnh-hub",
  title: "Cộng Đồng Sinh Viên HVNH",
  description:
    "Không gian trao đổi giáo trình, pass đồ dùng cá nhân, tìm phòng trọ/ở ghép và cập nhật các sự kiện chính thức tại Học viện Ngân hàng.",
  bannerImage: "https://picsum.photos/seed/hvnh-campus-banner/1400/420",
  avatarImage: "BAV",
  memberCount: 14280,
  postCount: 3520,
  isJoined: true,
};

const INITIAL_MARKET_ITEMS: MarketItem[] = [
  {
    id: "mkt-1",
    title: "Pass lại Giáo trình Tài chính Doanh nghiệp K24 (Mới 99%)",
    price: "45.000đ",
    originalPrice: "90.000đ",
    condition: "Like New",
    location: "KTX Học viện Ngân hàng",
    sellerName: "Lê Minh Anh",
    sellerAvatar: "MA",
    sellerPhone: "0987123456",
    image: "https://picsum.photos/seed/finance-book/600/400",
    category: "Giáo trình & Tài liệu",
    status: "available",
    createdAt: "30 phút trước",
  },
  {
    id: "mkt-2",
    title: "Thanh lý Máy tính Casio fx-580VN X chính hãng tem BITEX",
    price: "320.000đ",
    originalPrice: "650.000đ",
    condition: "Like New",
    location: "Ngõ 12 Chùa Bộc, Đống Đa",
    sellerName: "Nguyễn Hoàng Nam",
    sellerAvatar: "HN",
    sellerPhone: "0912345678",
    image: "https://picsum.photos/seed/casio-calculator/600/400",
    category: "Đồ dùng học tập",
    status: "available",
    createdAt: "2 giờ trước",
  },
  {
    id: "mkt-3",
    title: "Xe máy Wave Alpha 2021 chính chủ biển Hà Nội - Xe đi giữ gìn",
    price: "13.500.000đ",
    condition: "Used",
    location: "Cổng phụ HVNH - Chùa Bộc",
    sellerName: "Trần Đức Tiến",
    sellerAvatar: "DT",
    sellerPhone: "0978999888",
    image: "https://picsum.photos/seed/wave-motorbike/600/400",
    category: "Phương tiện đi lại",
    status: "available",
    createdAt: "5 giờ trước",
  },
  {
    id: "mkt-4",
    title: "Tai nghe Bluetooth Sony WH-1000XM4 chống ồn cao cấp",
    price: "3.800.000đ",
    originalPrice: "6.900.000đ",
    condition: "Like New",
    location: "Khu tập thể Ngân Hàng",
    sellerName: "Phạm Thu Trang",
    sellerAvatar: "TT",
    sellerPhone: "0934567890",
    image: "https://picsum.photos/seed/sony-headphone/600/400",
    category: "Đồ điện tử",
    status: "sold",
    createdAt: "1 ngày trước",
  },
];

const INITIAL_ROOM_ITEMS: RoomItem[] = [
  {
    id: "rm-1",
    title: "Cho thuê phòng trọ khép kín full đồ ngõ 43 Chùa Bộc - Cách cổng trường 200m",
    rentPerMonth: "3.200.000đ",
    area: "28 m²",
    address: "Ngõ 43 Chùa Bộc, Đống Đa, Hà Nội",
    distanceToSchool: "200m (Đi bộ 3 phút)",
    amenities: ["Điều hòa", "Nóng lạnh", "Máy giặt", "Ban công", "Không chung chủ"],
    status: "available",
    landlordName: "Cô Hương (Chủ nhà)",
    landlordPhone: "0912888999",
    image: "https://picsum.photos/seed/room-studio/600/400",
    createdAt: "1 giờ trước",
  },
  {
    id: "rm-2",
    title: "Tìm 1 nữ ở ghép căn hộ chung cư 2PN gần Học viện Ngân hàng",
    rentPerMonth: "2.100.000đ",
    area: "65 m²",
    address: "Chung cư Star City, Lê Văn Lương",
    distanceToSchool: "1.2 km",
    amenities: ["Điều hòa", "Nóng lạnh", "Tủ lạnh", "Sàn gỗ", "Thang máy", "Cho nuôi pet"],
    status: "available",
    landlordName: "Nguyễn Phương Thảo",
    landlordPhone: "0945666777",
    image: "https://picsum.photos/seed/apartment-living/600/400",
    createdAt: "4 giờ trước",
  },
  {
    id: "rm-3",
    title: "Phòng trọ giá rẻ cho nam sinh viên gần KTX Ngân Hàng",
    rentPerMonth: "1.800.000đ",
    area: "18 m²",
    address: "Ngõ 165 Chùa Bộc, Đống Đa",
    distanceToSchool: "350m",
    amenities: ["Nóng lạnh", "Có chỗ để xe", "An ninh tốt"],
    status: "rented",
    landlordName: "Chú Tuấn",
    landlordPhone: "0904123123",
    image: "https://picsum.photos/seed/budget-room/600/400",
    createdAt: "2 ngày trước",
  },
];

const INITIAL_EVENT_ITEMS: EventItem[] = [
  {
    id: "evt-1",
    title: "Chào Tân Sinh Viên K27 - BA Youth Festival 2026",
    day: "15",
    month: "Tháng 9",
    time: "18:30 - 22:00",
    location: "Sân vận động Học viện Ngân hàng",
    organizer: "Đoàn Thanh Niên & Hội Sinh Viên HVNH",
    coverImage: "https://picsum.photos/seed/campus-festival/800/450",
    goingCount: 1450,
    interestedCount: 3200,
    userStatus: "going",
    createdAt: "2 ngày trước",
  },
  {
    id: "evt-2",
    title: "Workshop: Định Hướng Nghề Nghiệp Ngành Fintech & Ngân Hàng Số",
    day: "22",
    month: "Tháng 9",
    time: "08:30 - 11:30",
    location: "Hội trường D1 - HVNH",
    organizer: "Khoa Ngân Hàng & CLB Nhà Đầu Tư Trẻ",
    coverImage: "https://picsum.photos/seed/fintech-workshop/800/450",
    goingCount: 380,
    interestedCount: 890,
    userStatus: "interested",
    createdAt: "3 ngày trước",
  },
  {
    id: "evt-3",
    title: "Giải Bóng Đá Nam Sinh Viên HVNH Cup 2026",
    day: "05",
    month: "Tháng 10",
    time: "07:30 - 17:30",
    location: "Sân bóng đá cỏ nhân tạo HVNH",
    organizer: "CLB Thể Thao HVNH",
    coverImage: "https://picsum.photos/seed/football-cup/800/450",
    goingCount: 620,
    interestedCount: 1100,
    userStatus: null,
    createdAt: "5 ngày trước",
  },
];

export function useCommunityGroup() {
  const [activeTab, setActiveTab] = useState<GroupTab>("market");
  const [headerData, setHeaderData] = useState<GroupHeaderData>(INITIAL_HEADER_DATA);
  const [marketItems, setMarketItems] = useState<MarketItem[]>(INITIAL_MARKET_ITEMS);
  const [roomItems, setRoomItems] = useState<RoomItem[]>(INITIAL_ROOM_ITEMS);
  const [eventItems, setEventItems] = useState<EventItem[]>(INITIAL_EVENT_ITEMS);

  // Filters state
  const [searchQuery, setSearchQuery] = useState("");
  const [marketConditionFilter, setMarketConditionFilter] = useState<string>("all");
  const [marketStatusFilter, setMarketStatusFilter] = useState<string>("all");
  const [roomStatusFilter, setRoomStatusFilter] = useState<string>("all");

  const toggleJoinGroup = useCallback(() => {
    setHeaderData((prev) => ({
      ...prev,
      isJoined: !prev.isJoined,
      memberCount: prev.isJoined ? prev.memberCount - 1 : prev.memberCount + 1,
    }));
  }, []);

  const toggleSoldStatus = useCallback((itemId: string) => {
    setMarketItems((prev) =>
      prev.map((item) => {
        if (item.id === itemId) {
          const nextStatus = item.status === "available" ? "sold" : "available";
          return { ...item, status: nextStatus };
        }
        return item;
      })
    );
  }, []);

  const toggleEventStatus = useCallback(
    (eventId: string, targetStatus: EventUserStatus) => {
      setEventItems((prev) =>
        prev.map((evt) => {
          if (evt.id === eventId) {
            const currentStatus = evt.userStatus;
            let nextStatus: EventUserStatus = targetStatus;
            let goingDelta = 0;
            let interestedDelta = 0;

            if (currentStatus === targetStatus) {
              nextStatus = null;
              if (targetStatus === "going") goingDelta = -1;
              if (targetStatus === "interested") interestedDelta = -1;
            } else {
              if (currentStatus === "going") goingDelta -= 1;
              if (currentStatus === "interested") interestedDelta -= 1;

              if (targetStatus === "going") goingDelta += 1;
              if (targetStatus === "interested") interestedDelta += 1;
            }

            return {
              ...evt,
              userStatus: nextStatus,
              goingCount: Math.max(0, evt.goingCount + goingDelta),
              interestedCount: Math.max(0, evt.interestedCount + interestedDelta),
            };
          }
          return evt;
        })
      );
    },
    []
  );

  // Filtered lists
  const filteredMarketItems = useMemo(() => {
    return marketItems.filter((item) => {
      const matchQuery =
        !searchQuery ||
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.location.toLowerCase().includes(searchQuery.toLowerCase());

      const matchCondition =
        marketConditionFilter === "all" || item.condition === marketConditionFilter;

      const matchStatus =
        marketStatusFilter === "all" || item.status === marketStatusFilter;

      return matchQuery && matchCondition && matchStatus;
    });
  }, [marketItems, searchQuery, marketConditionFilter, marketStatusFilter]);

  const filteredRoomItems = useMemo(() => {
    return roomItems.filter((item) => {
      const matchQuery =
        !searchQuery ||
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.address.toLowerCase().includes(searchQuery.toLowerCase());

      const matchStatus =
        roomStatusFilter === "all" || item.status === roomStatusFilter;

      return matchQuery && matchStatus;
    });
  }, [roomItems, searchQuery, roomStatusFilter]);

  const filteredEventItems = useMemo(() => {
    return eventItems.filter((item) => {
      return (
        !searchQuery ||
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.location.toLowerCase().includes(searchQuery.toLowerCase())
      );
    });
  }, [eventItems, searchQuery]);

  return {
    activeTab,
    setActiveTab,
    headerData,
    toggleJoinGroup,
    searchQuery,
    setSearchQuery,
    // Market
    marketItems: filteredMarketItems,
    marketConditionFilter,
    setMarketConditionFilter,
    marketStatusFilter,
    setMarketStatusFilter,
    toggleSoldStatus,
    // Room
    roomItems: filteredRoomItems,
    roomStatusFilter,
    setRoomStatusFilter,
    // Event
    eventItems: filteredEventItems,
    toggleEventStatus,
  };
}
