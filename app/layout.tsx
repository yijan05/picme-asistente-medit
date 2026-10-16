import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'PicMe · Asistente UCundinamarca',
  description: 'Explora el MEDIT y la Declaración Persona Transhumana con fuentes, ejemplos y criterio propio. Proyecto académico PicMe.',
  icons: { icon: '/favicon.svg' },
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="es"><body>{children}</body></html>;
}
