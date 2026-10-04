import { redirect } from "next/navigation";

/**
 * The former marketplace mixed real feed rows with local-only actions. Keep
 * old bookmarks valid while sending users to the real moderated group flow.
 */
export default function MarketCommunityPage() {
  redirect("/groups");
}
