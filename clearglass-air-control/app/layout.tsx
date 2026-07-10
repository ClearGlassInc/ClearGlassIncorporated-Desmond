import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import './globals.css';

export const metadata: Metadata = {
  title: 'ClearGlass Air Systems Control Surface',
  description: 'Quantum-neural smart glass air systems control surface prototype for ClearGlassInc Artemis.',
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
