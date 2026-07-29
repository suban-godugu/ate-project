import type { Metadata } from "next";
import { DM_Sans, Space_Grotesk } from "next/font/google";
import { Providers } from "@/components/providers/Providers";
import "./globals.css";

const display = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
});

const body = DM_Sans({
  subsets: ["latin"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "Scan Debug Recommendation Agent · COMPTY",
  description: "Scan Debug Recommendation Agent — VERILUMEN ATE Yield Optimization",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${body.variable} antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
