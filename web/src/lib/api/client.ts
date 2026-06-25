import createClient, { type Client } from "openapi-fetch";
import type { paths } from "./schema";

export type ApiClient = Client<paths>;

/** Single construction point for the typed API client so UI code never hand-writes request types. */
export function createApiClient(
  baseUrl: string,
  fetchImpl?: typeof fetch,
): ApiClient {
  return createClient<paths>({
    baseUrl,
    ...(fetchImpl ? { fetch: fetchImpl } : {}),
  });
}
