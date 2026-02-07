import "./globals.css";

import { Space_Grotesk, Source_Serif_4 } from "next/font/google";

const displayFont = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["400", "600", "700"]
});

const bodyFont = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-sans",
  weight: ["400", "500", "600"]
});

export const metadata = {
  title: "SignalForge Admin",
  description: "Control panel for SignalForge automation"
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${displayFont.variable} ${bodyFont.variable}`}>
      <body className="min-h-screen bg-gradient-to-br from-fog via-white to-accentSoft/40">
        <div className="absolute inset-0 -z-10">
          <div className="absolute right-[-10%] top-[-20%] h-72 w-72 rounded-full bg-mint/30 blur-3xl" />
          <div className="absolute left-[-15%] bottom-[-10%] h-80 w-80 rounded-full bg-sea/20 blur-3xl" />
        </div>
        {children}
      </body>
    </html>
  );
}
