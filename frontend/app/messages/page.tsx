"use client";

import { useState } from "react";

import ConversationList from "@/components/chat/ConversationList";
import ChatWorkspace from "@/components/chat/ChatWorkspace";
import ChatDetailsPanel from "@/components/chat/ChatDetailsPanel";
import { useMessenger } from "@/hooks/useMessenger";

export default function MessagesPage() {
  const messengerState = useMessenger();
  const [searchOpen,setSearchOpen]=useState(false);

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
          onStartConversation={messengerState.startConversation}
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
            realtimeEvent={messengerState.realtimeEvent}
            onSignal={messengerState.sendRealtime}
            searchOpen={searchOpen}
            onCloseSearch={()=>setSearchOpen(false)}
          />
        )}

        {/* Column 3: Chat Details Panel (Right Collapsible) */}
        {messengerState.showDetailsPanel && messengerState.activeConversation && (
          <ChatDetailsPanel
            conversation={messengerState.activeConversation}
            onClose={messengerState.toggleDetailsPanel}
            onSearch={()=>setSearchOpen(true)}
            onUpdateSettings={messengerState.updateSettings}
            onBlocked={messengerState.removeActiveConversation}
          />
        )}
      </div>
    </main>
  );
}
