import type { ReactNode } from "react";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "monospace", background: "#101410", color: "#d9e1d9", padding: 32 }}>
        {children}
      </body>
    </html>
  );
}
