import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Navbar from "@/components/ui/Navbar";
import "./globals.css";
import "@/styles/pages/home.css";
import "@/styles/pages/profile.css";
import "@/styles/pages/groups.css";
import "@/styles/pages/notifications.css";
import "@/styles/pages/info.css";

const inter = Inter({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "HVNH Hub - Cộng đồng sinh viên Học viện Ngân hàng",
  description:
    "Nền tảng cộng đồng đa chức năng dành riêng cho sinh viên HVNH: Pass đồ, Tìm trọ/Ghép phòng, Sự kiện, Nhắn tin thời gian thực.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi" className={inter.variable}>
      <body className={inter.className}>
        <Navbar />
        <div className="app-main-body-content">{children}</div>
      </body>
    </html>
  );
}

