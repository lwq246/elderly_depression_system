import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Screening Console",
  description: "Elderly depression screening — room console and nurse dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
