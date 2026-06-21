import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    include: ["web/src/**/*.{test,spec}.{ts,tsx}"],
    coverage: {
      provider: "v8",
      reporter: ["text"],
      include: ["web/src/**/*.{ts,tsx}"],
      exclude: [
        "web/src/**/*.{test,spec}.{ts,tsx}",
        "web/src/lib/api/schema.ts",
      ],
      thresholds: {
        statements: 100,
        functions: 100,
        lines: 100,
        branches: 75,
      },
    },
  },
});
