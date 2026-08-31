"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import GroupHeader from "@/components/group/GroupHeader";
import MarketCardMatrix from "@/components/group/MarketCardMatrix";
import HousingCardMatrix from "@/components/group/HousingCardMatrix";
import EventsCardMatrix from "@/components/group/EventsCardMatrix";
import CreatePostModal from "@/components/post/CreatePostModal";
import { useCommunityGroup } from "@/hooks/useCommunityGroup";
import { useCreatePost } from "@/hooks/useCreatePost";

export default function MarketCommunityPage() {
  const [checked, setChecked] = useState(false);
  const router = useRouter();

  const communityState = useCommunityGroup();
  const createPostState = useCreatePost();

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
    return <main className="home-loading" aria-label="Đang tải trang hội nhóm" />;

  const handleMessageSeller = (sellerName: string) => {
    router.push("/messages");
  };

  const handleContactLandlord = (name: string, phone: string) => {
    alert(`Liên hệ chủ nhà/người cho thuê: ${name} (${phone})`);
  };

  return (
    <main className="group-community-page-full">
      <div className="group-content-wrapper-full">
        {/* Group Header & Navigation Tabs */}
        <GroupHeader
          data={communityState.headerData}
          activeTab={communityState.activeTab}
          onTabChange={communityState.setActiveTab}
          onToggleJoin={communityState.toggleJoinGroup}
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
