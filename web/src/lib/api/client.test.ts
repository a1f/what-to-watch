import { describe, expect, it, vi } from "vitest";
import { createApiClient } from "./client";

describe("createApiClient", () => {
  it("GETs /health and returns the parsed body", async () => {
    const fakeFetch = vi.fn(
      async () =>
        new Response(JSON.stringify({ status: "ok", database: "up" }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
    ) as unknown as typeof fetch;

    const client = createApiClient("http://api.test", fakeFetch);
    const { data, error } = await client.GET("/health");

    expect(error).toBeUndefined();
    expect(fakeFetch).toHaveBeenCalledOnce();
    expect(data).toEqual({ status: "ok", database: "up" });
  });
});
