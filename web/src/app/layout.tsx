import type { Metadata } from "next";
import type { ReactElement, ReactNode } from "react";

export const metadata: Metadata = {
  title: "What to Watch",
  description: "A reminder-first movie and TV tracker.",
};

/** Root layout that frames every route with the shared html/body document shell. */
export default function RootLayout({
  children,
}: { children: ReactNode }): ReactElement {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
