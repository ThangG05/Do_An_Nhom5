import type {Metadata} from "next";
import {Be_Vietnam_Pro} from "next/font/google";
import Navbar from "@/components/ui/Navbar";
import AuthGuard from "@/components/auth/AuthGuard";
import {DialogProvider} from "@/components/ui/DialogProvider";
import "./globals.css";
import "@/styles/pages/home.css";import "@/styles/pages/profile.css";import "@/styles/pages/groups.css";import "@/styles/pages/notifications.css";import "@/styles/pages/info.css";
import "@/styles/post-polish.css";import "@/styles/post-actions.css";import "@/styles/comment-actions.css";import "@/styles/modern-system.css";import "@/styles/polish-final.css";import "@/styles/not-found.css";
import "@/styles/pages/assistant.css";
import "@/styles/ai-pet.css";
import "@/styles/ai-answer.css";
import "@/styles/auth-polish.css";
import "@/styles/ai-input-focus.css";
import "@/styles/user-experience.css";

const appFont=Be_Vietnam_Pro({subsets:["latin","vietnamese"],weight:["400","500","600","700"],variable:"--font-app",display:"swap"});
export const metadata:Metadata={title:"HVNH Hub - Cộng đồng sinh viên Học viện Ngân hàng",description:"Nền tảng cộng đồng dành cho sinh viên HVNH: trao đổi đồ dùng, tìm trọ, sự kiện, học tập và nhắn tin thời gian thực."};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="vi" className={appFont.variable} data-scroll-behavior="smooth"><body className={appFont.className}><DialogProvider><a className="skip-link" href="#main-content">Bỏ qua điều hướng</a><Navbar/><div className="app-main-body-content" id="main-content"><AuthGuard>{children}</AuthGuard></div></DialogProvider></body></html>}
