"use client";

import { useState, useCallback, useMemo } from "react";
import { Conversation, Message } from "@/types/message";

const CURRENT_USER_ID = "usr-current";

const INITIAL_CONVERSATIONS: Conversation[] = [
  {
    id: "conv-1",
    participantId: "usr-101",
    participantName: "Lê Minh Anh",
    participantAvatar: "MA",
    isOnline: true,
    lastActive: "Đang hoạt động",
    lastMessageSnippet: "Dạ vâng ạ, chiều nay 3h em qua KTX lấy sách Giáo trình Tài chính nhé!",
    lastMessageTime: "12m",
    unreadCount: 2,
    role: "Sinh viên K25 - Khoa Tài Chính",
    bio: "Pass đồ học tập & sách cũ giá rẻ cho sinh viên HVNH 📚",
    sharedMedia: [
      {
        id: "m-1",
        url: "https://picsum.photos/seed/finance-book/600/400",
        type: "image",
        name: "Giao_trinh_TC.jpg",
      },
      {
        id: "m-2",
        url: "https://picsum.photos/seed/casio-calculator/600/400",
        type: "image",
        name: "May_tinh_fx580.jpg",
      },
    ],
    sharedFiles: [
      {
        id: "f-1",
        name: "De_thi_Tai_chinh_doanh_nghiep_2025.pdf",
        size: "2.4 MB",
        type: "PDF",
        url: "#",
      },
      {
        id: "f-2",
        name: "Bai_tap_on_tap_chuong_3.docx",
        size: "850 KB",
        type: "DOCX",
        url: "#",
      },
    ],
  },
  {
    id: "conv-2",
    participantId: "usr-102",
    participantName: "Nguyễn Hoàng Nam",
    participantAvatar: "HN",
    isOnline: false,
    lastActive: "Hoạt động 25 phút trước",
    lastMessageSnippet: "Phòng trọ ngõ 43 Chùa Bộc còn không bạn ơi? Có sẵn điều hòa nóng lạnh chưa?",
    lastMessageTime: "1h",
    unreadCount: 0,
    role: "Sinh viên K24 - Khoa Ngân Hàng",
    bio: "CLB Thể Thao HVNH ⚽ | Đang tìm phòng ở ghép",
    sharedMedia: [
      {
        id: "m-3",
        url: "https://picsum.photos/seed/room-studio/600/400",
        type: "image",
        name: "Anh_phong_Chua_Boc.jpg",
      },
    ],
    sharedFiles: [],
  },
  {
    id: "conv-3",
    participantId: "usr-103",
    participantName: "Phạm Thu Trang",
    participantAvatar: "TT",
    isOnline: true,
    lastActive: "Đang hoạt động",
    lastMessageSnippet: "Tối nay 18h30 có đi xem BA Youth Festival không Trang?",
    lastMessageTime: "Hôm qua",
    unreadCount: 0,
    role: "Sinh viên K26 - Khoa Kế Toán",
    bio: "CLB Âm Nhạc HVNH 🎵",
    sharedMedia: [],
    sharedFiles: [
      {
        id: "f-3",
        name: "Lich_trinh_BA_Youth_Festival.pdf",
        size: "1.2 MB",
        type: "PDF",
        url: "#",
      },
    ],
  },
];

const INITIAL_MESSAGES_MAP: Record<string, Message[]> = {
  "conv-1": [
    {
      id: "msg-1",
      conversationId: "conv-1",
      senderId: "usr-101",
      senderName: "Lê Minh Anh",
      senderAvatar: "MA",
      content: "Chào bạn, mình thấy bạn đăng pass cuốn Giáo trình Tài chính Doanh nghiệp.",
      timestamp: "10:30 AM",
      status: "seen",
      type: "text",
    },
    {
      id: "msg-2",
      conversationId: "conv-1",
      senderId: CURRENT_USER_ID,
      senderName: "Sinh viên HVNH",
      senderAvatar: "SV",
      content: "Chào Minh Anh! Đúng rồi bạn nha, sách mới 99% không gạch xóa gì đâu.",
      timestamp: "10:32 AM",
      status: "seen",
      type: "text",
    },
    {
      id: "msg-3",
      conversationId: "conv-1",
      senderId: "usr-101",
      senderName: "Lê Minh Anh",
      senderAvatar: "MA",
      content: "Dạ vâng ạ, chiều nay 3h em qua KTX lấy sách Giáo trình Tài chính nhé!",
      timestamp: "10:45 AM",
      status: "delivered",
      type: "text",
    },
  ],
  "conv-2": [
    {
      id: "msg-4",
      conversationId: "conv-2",
      senderId: "usr-102",
      senderName: "Nguyễn Hoàng Nam",
      senderAvatar: "HN",
      content: "Phòng trọ ngõ 43 Chùa Bộc còn không bạn ơi? Có sẵn điều hòa nóng lạnh chưa?",
      timestamp: "09:15 AM",
      status: "seen",
      type: "text",
    },
    {
      id: "msg-5",
      conversationId: "conv-2",
      senderId: CURRENT_USER_ID,
      senderName: "Sinh viên HVNH",
      senderAvatar: "SV",
      content: "Còn bạn nhé! Phòng có đủ điều hòa, nóng lạnh, máy giặt dùng chung và không chung chủ.",
      timestamp: "09:20 AM",
      status: "seen",
      type: "text",
    },
  ],
  "conv-3": [
    {
      id: "msg-6",
      conversationId: "conv-3",
      senderId: "usr-103",
      senderName: "Phạm Thu Trang",
      senderAvatar: "TT",
      content: "Tối nay 18h30 có đi xem BA Youth Festival không Trang?",
      timestamp: "Hôm qua 17:00",
      status: "seen",
      type: "text",
    },
  ],
};

export function useMessenger() {
  const [conversations, setConversations] = useState<Conversation[]>(INITIAL_CONVERSATIONS);
  const [activeConversationId, setActiveConversationId] = useState<string>("conv-1");
  const [messagesMap, setMessagesMap] = useState<Record<string, Message[]>>(INITIAL_MESSAGES_MAP);
  const [searchQuery, setSearchQuery] = useState("");
  const [showDetailsPanel, setShowDetailsPanel] = useState(true);
  const [mobileView, setMobileView] = useState<"list" | "chat">("list");

  const activeConversation = useMemo(() => {
    return conversations.find((c) => c.id === activeConversationId) || conversations[0];
  }, [conversations, activeConversationId]);

  const activeMessages = useMemo(() => {
    return messagesMap[activeConversationId] || [];
  }, [messagesMap, activeConversationId]);

  const filteredConversations = useMemo(() => {
    if (!searchQuery.trim()) return conversations;
    const q = searchQuery.toLowerCase();
    return conversations.filter(
      (c) =>
        c.participantName.toLowerCase().includes(q) ||
        c.lastMessageSnippet.toLowerCase().includes(q)
    );
  }, [conversations, searchQuery]);

  const selectConversation = useCallback((id: string) => {
    setActiveConversationId(id);
    setMobileView("chat");
    // Clear unread count on selection
    setConversations((prev) =>
      prev.map((c) => (c.id === id ? { ...c, unreadCount: 0 } : c))
    );
  }, []);

  const toggleDetailsPanel = useCallback(() => {
    setShowDetailsPanel((prev) => !prev);
  }, []);

  const sendMessage = useCallback(
    (content: string, mediaUrl?: string) => {
      if (!content.trim() && !mediaUrl) return;

      const newMsgId = `msg-${Date.now()}`;
      const timestampStr = new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });

      const newMsg: Message = {
        id: newMsgId,
        conversationId: activeConversationId,
        senderId: CURRENT_USER_ID,
        senderName: "Sinh viên HVNH",
        senderAvatar: "SV",
        content: content.trim(),
        timestamp: timestampStr,
        status: "sent",
        type: mediaUrl ? "image" : "text",
        attachments: mediaUrl
          ? [{ id: `att-${Date.now()}`, type: "image", url: mediaUrl, name: "Photo" }]
          : undefined,
      };

      // Append to message feed
      setMessagesMap((prev) => ({
        ...prev,
        [activeConversationId]: [...(prev[activeConversationId] || []), newMsg],
      }));

      // Update snippet in conversation list
      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConversationId
            ? {
                ...c,
                lastMessageSnippet: content.trim() || "[Hình ảnh]",
                lastMessageTime: "Vừa xong",
              }
            : c
        )
      );

      // Simulate recipient response after 1.5s
      setTimeout(() => {
        setMessagesMap((prev) => {
          const currentList = prev[activeConversationId] || [];
          return {
            ...prev,
            [activeConversationId]: currentList.map((m) =>
              m.id === newMsgId ? { ...m, status: "seen" } : m
            ),
          };
        });
      }, 1500);
    },
    [activeConversationId]
  );

  return {
    conversations: filteredConversations,
    activeConversation,
    activeMessages,
    selectConversation,
    searchQuery,
    setSearchQuery,
    showDetailsPanel,
    toggleDetailsPanel,
    sendMessage,
    currentUserId: CURRENT_USER_ID,
    mobileView,
    setMobileView,
  };
}
