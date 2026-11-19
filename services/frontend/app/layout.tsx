import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClinGraph",
  description: "Evidence-based clinical research assistant"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
