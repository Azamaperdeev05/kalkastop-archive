import type { Metadata, Viewport } from "next";
import "./globals.css";

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#09090b" },
  ],
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  metadataBase: new URL("https://web-tau-ten-13.vercel.app"),
  title: {
    default: "Калькасыз қазақ тілі (@kalkastop) - Назгүл Қожабек | Толық мұрағат",
    template: "%s | Калькасыз қазақ тілі (@kalkastop)",
  },
  description:
    "Назгүл Қожабектің 'Калькасыз қазақ тілі' Telegram-арнасының 4 459 жазбадан тұратын толық веб-мұрағаты. Қазақ тіліндегі калька сөздер мен тіркестер, олардың табиғи баламалары, лексика мен тіл тазалығы.",
  applicationName: "Калькасыз қазақ тілі",
  authors: [{ name: "Назгүл Қожабек", url: "https://t.me/kalkastop" }],
  generator: "Next.js",
  keywords: [
    "калькасыз қазақ тілі",
    "калька сөздер",
    "назгүл қожабек",
    "қазақ тілі",
    "тіл тазалығы",
    "қазақша дұрыс сөйлеу",
    "қазақ тілінің сөздігі",
    "қазақша баламалар",
    "kalkastop",
    "telegram archive",
    "назгуль кожабек",
    "кальки в казахском языке",
    "правильный казахский язык",
    "казахский язык без калек",
  ],
  referrer: "origin-when-cross-origin",
  creator: "Назгүл Қожабек",
  publisher: "Калькасыз қазақ тілі (@kalkastop)",
  category: "Education & Linguistics",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  alternates: {
    canonical: "/",
    languages: {
      "kk-KZ": "/",
      kk: "/",
      "x-default": "/",
    },
  },
  openGraph: {
    title: "Калькасыз қазақ тілі (@kalkastop) - Назгүл Қожабек | Толық мұрағат",
    description:
      "Қазақ тіліндегі орысша калька сөздерді түзетуге арналған 4 459 жазба, фото және бейнелердің толық онлайн сөздік-мұрағаты.",
    url: "https://web-tau-ten-13.vercel.app",
    siteName: "Калькасыз қазақ тілі",
    locale: "kk_KZ",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Калькасыз қазақ тілі (@kalkastop) - Назгүл Қожабек",
    description:
      "Қазақ тіліндегі калька сөздер мен олардың дұрыс баламалары бойынша 4 459 жазба.",
    creator: "@kalkastop",
  },
  verification: {
    google: "google6b11bbffd33748dd",
    other: {
      "google-site-verification": [
        "google6b11bbffd33748dd",
        "google6b11bbffd33748dd.html",
        "6b11bbffd33748dd",
      ],
    },
  },
  robots: {
    index: true,
    follow: true,
    nocache: false,
    googleBot: {
      index: true,
      follow: true,
      noimageindex: false,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  other: {
    "geo.region": "KZ",
    "geo.placename": "Kazakhstan",
    "geo.position": "48.0196;66.9237",
    ICBM: "48.0196, 66.9237",
    "content-language": "kk",
    target: "all",
    audience: "all",
    coverage: "Kazakhstan",
    rating: "general",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Global Structured Data (GEO / LLM / Search Engines)
  const structuredDataWebSite = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "@id": "https://web-tau-ten-13.vercel.app/#website",
    url: "https://web-tau-ten-13.vercel.app",
    name: "Калькасыз қазақ тілі",
    alternateName: [
      "kalkastop",
      "Калькасыз қазақ тілі архиві",
      "Назгүл Қожабек - Калькасыз қазақ тілі",
    ],
    description:
      "Назгүл Қожабектің қазақ тіліндегі калька сөздерді түзетуге арналған @kalkastop арнасының толық мұрағаты.",
    inLanguage: "kk-KZ",
    publisher: {
      "@type": "Person",
      name: "Назгүл Қожабек",
      jobTitle: "Журналист, тіл жанашыры, автор",
      sameAs: ["https://t.me/kalkastop"],
    },
    potentialAction: {
      "@type": "SearchAction",
      target: {
        "@type": "EntryPoint",
        urlTemplate:
          "https://web-tau-ten-13.vercel.app/?q={search_term_string}",
      },
      "query-input": "required name=search_term_string",
    },
  };

  const structuredDataAuthor = {
    "@context": "https://schema.org",
    "@type": "Person",
    name: "Назгүл Қожабек",
    jobTitle: "Журналист, тіл жанашыры, 'Калькасыз қазақ тілі' авторы",
    nationality: {
      "@type": "Country",
      name: "Kazakhstan",
    },
    knowsAbout: [
      "Қазақ тілі",
      "Калька сөздер",
      "Тіл мәдениеті",
      "Стилистика",
      "Лексикология",
    ],
    sameAs: ["https://t.me/kalkastop"],
  };

  return (
    <html lang="kk" className="scroll-smooth">
      <head>
        <meta httpEquiv="content-language" content="kk" />
        <meta name="geo.region" content="KZ" />
        <meta name="geo.placename" content="Kazakhstan" />
        <meta name="geo.position" content="48.0196;66.9237" />
        <meta name="ICBM" content="48.0196, 66.9237" />
        <meta
          name="google-site-verification"
          content="google6b11bbffd33748dd"
        />
        <meta
          name="google-site-verification"
          content="6b11bbffd33748dd"
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(structuredDataWebSite),
          }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(structuredDataAuthor),
          }}
        />
      </head>
      <body className="min-h-screen selection:bg-telegram/20 selection:text-telegram-dark">
        {children}
      </body>
    </html>
  );
}
