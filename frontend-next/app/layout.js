import "./globals.css";

export const metadata = {
  title: "CureGenix",
  description: "Quantum-Assisted Molecular Analysis",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
