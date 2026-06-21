import type { ReactElement, ReactNode } from "react";
import { describe, expect, it } from "vitest";
import RootLayout, { metadata } from "./layout";

describe("RootLayout", () => {
  it("renders the passed children inside the document body", () => {
    const html = RootLayout({ children: "hi" }) as ReactElement<{
      children: ReactElement<{ children: ReactNode }>;
    }>;
    expect(html.type).toBe("html");
    const body = html.props.children;
    expect(body.type).toBe("body");
    expect(body.props.children).toBe("hi");
  });

  it("exposes the page title as metadata", () => {
    expect(metadata.title).toBe("What to Watch");
  });
});
