"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import CreatePostCard from "@/components/post/CreatePostCard";
import CreatePostModal from "@/components/post/CreatePostModal";
import PostCard from "@/components/post/PostCard";
import { useCreatePost } from "@/hooks/useCreatePost";
import { Post } from "@/types/post";

const initialSeedPosts: Post[] = [
  {
    id: "seed-1",
    author: {
      id: "bav-official",
      name: "Học viện Ngân Hàng",
      avatar: "/assets/logo.png",
      isVerified: true,
    },
    content: "TUYỂN SINH CHƯƠNG TRÌNH TIẾN SĨ UWE BRISTOL CẤP BẰNG QUỐC TẾ. Đăng ký nhận thông tin tư vấn tại phòng Đào tạo HVNH.",
    createdAt: "1 giờ trước",
    category: "general",
    privacy: "public",
    media: [
      {
        id: "media-1",
        type: "image",
        url: "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=900&q=80",
      },
    ],
    likesCount: 142,
    commentsCount: 28,
    isLiked: false,
  },
  {
    id: "seed-2",
    author: {
      id: "user-2",
      name: "Abdul Quayyum",
      avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80",
      isVerified: true,
    },
    content: "Tìm bạn ở ghép chung cư mini gần Học viện Ngân hàng ngõ 12 Chùa Bộc, ưu tiên sinh viên HVNH.",
    createdAt: "2 giờ trước",
    category: "roommate",
    privacy: "public",
    media: [
      {
        id: "media-2",
        type: "image",
        url: "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=900&q=80",
      },
    ],
    likesCount: 45,
    commentsCount: 12,
    isLiked: true,
  },
];

export default function HomePage() {
  const [checked, setChecked] = useState(false);
  const [posts, setPosts] = useState<Post[]>([]);
  const router = useRouter();

  const handlePostCreated = (newPost: Post) => {
    setPosts((prev) => [newPost, ...prev]);
  };

  const createPostState = useCreatePost(handlePostCreated);

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
    return <main className="home-loading" aria-label="Đang tải trang chủ" />;

  return (
    <main className="home-page-single-column">
      <div className="home-content-full">
        <section className="home-welcome">
          <p>Cộng đồng HVNH</p>
          <h1>Chào mừng trở lại</h1>
          <span>Khám phá những tin tức và bài đăng mới nhất trong trường hôm nay.</span>
        </section>

        <div className="home-layout">
          <section className="home-feed" aria-label="Bài viết mới">
            {/* MODULE A: Feed Header Create Post Card */}
            <CreatePostCard onOpenModal={createPostState.openModal} />

            {/* Dynamically Created Posts */}
            {posts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}

            {/* Initial Seed Posts with Interactive PostCard */}
            {initialSeedPosts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </section>

          <aside className="home-side-panel">
            <h2>Khám phá cộng đồng HVNH</h2>
            <p>
              Tham gia các nhóm chuyên biệt theo chủ đề: Pass lại đồ dùng, Tìm nhà trọ/Ghép phòng, và Sự kiện sinh viên.
            </p>
            <Link href="/market" className="btn btn-primary btn-block">
              Xem các nhóm
            </Link>
          </aside>
        </div>
      </div>

      {/* MODULE A: Create Post Full Modal */}
      <CreatePostModal postState={createPostState} />
    </main>
  );
}
