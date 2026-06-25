import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Home from "./page";

describe("Home", () => {
  it("renders the app name as a heading", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { name: /what to watch/i }),
    ).toBeTruthy();
  });
});
