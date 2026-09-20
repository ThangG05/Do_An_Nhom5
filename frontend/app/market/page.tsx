"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import GroupHeader from "@/components/group/GroupHeader";
import MarketCardMatrix from "@/components/group/MarketCardMatrix";
import HousingCardMatrix from "@/components/group/HousingCardMatrix";
import EventsCardMatrix from "@/components/group/EventsCardMatrix";
import CreatePostModal from "@/components/post/CreatePostModal";
import { useCommunityGroup } from "@/hooks/useCommunityGroup";
import { useCreatePost } from "@/hooks/useCreatePost";
import { useDialog } from "@/components/ui/DialogProvider";

export default function MarketCommunityPage() {
  const router = useRouter();
  const dialog = useDialog();

  const communityState = useCommunityGroup();
  const createPostState = useCreatePost();

  const handleMessageSeller = (sellerName: string) => {
    router.push("/messages");
  };

  const handleContactLandlord = (name: string, phone: string) => {
    dialog.notify({title:`Liên hệ ${name}`,message:phone,tone:'default'});
  };

  return (
    <main className="group-community-page-full">
      <div className="group-content-wrapper-full">
        {/* Group Header & Navigation Tabs */}
        <GroupHeader
          data={communityState.headerData}
          activeTab={communityState.activeTab}
          onTabChange={communityState.setActiveTab}
          onToggleJoin={() => router.push("/groups")}
          onOpenCreateModal={() => {
            if (communityState.activeTab === "market")
              createPostState.openModal("market");
            else if (communityState.activeTab === "room")
              createPostState.openModal("roommate");
            else if (communityState.activeTab === "event")
              createPostState.openModal("event");
            else createPostState.openModal();
          }}
        />

        {/* Dynamic Card Matrix Views */}
        <div className="group-content-area" style={{ marginTop: "24px" }}>
          {communityState.loading && <p className="live-empty">Đang tải dữ liệu cộng đồng…</p>}
          {communityState.error && (
            <div className="admin-error">
              <span>{communityState.error}</span>
              <button type="button" onClick={() => void communityState.refetch()}>Thử lại</button>
            </div>
          )}
          {communityState.activeTab === "market" && (
            <MarketCardMatrix
              items={communityState.marketItems}
              searchQuery={communityState.searchQuery}
              onSearchChange={communityState.setSearchQuery}
              conditionFilter={communityState.marketConditionFilter}
              onConditionFilterChange={communityState.setMarketConditionFilter}
              statusFilter={communityState.marketStatusFilter}
              onStatusFilterChange={communityState.setMarketStatusFilter}
              onToggleSold={communityState.toggleSoldStatus}
              onMessageSeller={handleMessageSeller}
            />
          )}

          {communityState.activeTab === "room" && (
            <HousingCardMatrix
              items={communityState.roomItems}
              searchQuery={communityState.searchQuery}
              onSearchChange={communityState.setSearchQuery}
              statusFilter={communityState.roomStatusFilter}
              onStatusFilterChange={communityState.setRoomStatusFilter}
              onContactLandlord={handleContactLandlord}
            />
          )}

          {communityState.activeTab === "event" && (
            <EventsCardMatrix
              items={communityState.eventItems}
              searchQuery={communityState.searchQuery}
              onSearchChange={communityState.setSearchQuery}
              onToggleStatus={communityState.toggleEventStatus}
            />
          )}
        </div>
      </div>

      {/* Create Post Modal Triggered from Group */}
      <CreatePostModal postState={createPostState} />
    </main>
  );
}
