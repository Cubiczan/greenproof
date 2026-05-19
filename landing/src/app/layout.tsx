import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "GreenVerify AI — AI-Powered Carbon Credit Verification & Trading",
  description:
    "GreenVerify combines Alibaba Cloud Qwen LLM with Portaldot blockchain to bring trust, transparency, and AI intelligence to the voluntary carbon market.",
  keywords: [
    "carbon credits",
    "blockchain",
    "AI verification",
    "Portaldot",
    "Qwen LLM",
    "green",
    "sustainability",
    "decentralized marketplace",
  ],
  openGraph: {
    title: "GreenVerify AI",
    description:
      "AI-Powered Carbon Credit Verification & Trading on Portaldot",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} antialiased`}
    >
      <body className="min-h-screen flex flex-col">{children}</body>
    </html>
  );
}
