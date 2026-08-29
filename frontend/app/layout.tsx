import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "HVNH Hub",
    description: "Cộng đồng sinh viên Học viện Ngân hàng",
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="vi">
            <body>{children}</body>
        </html>
    );
}
