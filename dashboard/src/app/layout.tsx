import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { UploadToastStack } from "@/components/upload/UploadToastStack";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { UploadProvider } from "@/contexts/UploadContext";
import "./globals.css";
import "@/styles/globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ATE Intelligence Platform",
  description: "Enterprise ATE Intelligence Platform for yield optimization and analytics",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} dark h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col font-sans">
        <QueryProvider>
          <ThemeProvider>
            <UploadProvider>
              {children}
              <UploadToastStack />
            </UploadProvider>
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
