"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ConversationList from "@/components/chat/ConversationList";
import ChatWorkspace from "@/components/chat/ChatWorkspace";
import ChatDetailsPanel from "@/components/chat/ChatDetailsPanel";
import { useMessenger } from "@/hooks/useMessenger";

export default function MessagesPage() {
  const [checked, setChecked] = useState(false);
  const router = useRouter();

  const messengerState = useMessenger();

  useEffect(() => {
    if (
      window.sessionStorage.getItem("hvnh-hub-mock-authenticated") !== "true"
    ) {
      router.replace("/login");
      return;
    }
    setChecked(true);
  }, [router]);

  if (!checked)
    return <main className="home-loading" aria-label="Đang tải tin nhắn" />;

  return (
    <main className="messenger-page-full-canvas">
      <div
        className={`messenger-3col-workspace ${
          messengerState.mobileView === "chat" ? "mobile-view-chat" : "mobile-view-list"
        }`}
      >
        {/* Column 1: Conversation List (Left) */}
        <ConversationList
          conversations={messengerState.conversations}
          activeConversationId={messengerState.activeConversation?.id || ""}
          onSelectConversation={messengerState.selectConversation}
          searchQuery={messengerState.searchQuery}
          onSearchChange={messengerState.setSearchQuery}
        />

        {/* Column 2: Chat Workspace (Center) */}
        {messengerState.activeConversation && (
          <ChatWorkspace
            activeConversation={messengerState.activeConversation}
            messages={messengerState.activeMessages}
            currentUserId={messengerState.currentUserId}
            onSendMessage={messengerState.sendMessage}
            onToggleDetailsPanel={messengerState.toggleDetailsPanel}
            showDetailsPanel={messengerState.showDetailsPanel}
            onBackMobile={() => messengerState.setMobileView("list")}
          />
        )}

        {/* Column 3: Chat Details Panel (Right Collapsible) */}
        {messengerState.showDetailsPanel && messengerState.activeConversation && (
          <ChatDetailsPanel
            conversation={messengerState.activeConversation}
            onClose={messengerState.toggleDetailsPanel}
          />
        )}
      </div>
    </main>
  );
}
