import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Калькасыз қазақ тілі (@kalkastop) - Telegram Archive",
  description:
    "Толық мұрағат: Назгүл Қожабектің 'Калькасыз қазақ тілі' Telegram каналындағы барлық жазбалар, фотолар мен бейнелер.",
  openGraph: {
    title: "Калькасыз қазақ тілі (@kalkastop) - Telegram Archive",
    description:
      "Назгүл Қожабектің 'Калькасыз қазақ тілі' каналының 4,400+ жазбасы бар толық веб-архиві.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="kk" className="scroll-smooth">
      <body className="min-h-screen selection:bg-telegram/20 selection:text-telegram-dark">
        {children}
      </body>
    </html>
  );
}
