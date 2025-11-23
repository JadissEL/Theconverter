import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TheConverter - Universal Media Converter",
  description: "Convert any audio or video file to any format with intelligent detection and high-speed processing",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
