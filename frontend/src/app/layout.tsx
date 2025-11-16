import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Research Assistant Tool',
  description: 'AI-powered research assistant for gathering and analyzing information',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
