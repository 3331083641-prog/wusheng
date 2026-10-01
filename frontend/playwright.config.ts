import { defineConfig } from "@playwright/test";
const outputDirectory = process.env.WUSHENG_PLAYWRIGHT_OUTPUT_DIR || "test-results";
export default defineConfig({
  testDir: "tests",
  timeout: 90000,
  workers: 1,
  fullyParallel: false,
  outputDir: outputDirectory,
  reporter: [["list"], ["json", { outputFile: `${outputDirectory}/ui-test-results.json` }]],
  use: {
    baseURL: process.env.WUSHENG_TEST_BASE_URL || "http://127.0.0.1:5173",
    headless: true,
    channel: "msedge",
    viewport: { width: 1440, height: 900 },
    launchOptions: process.env.WUSHENG_EDGE_PATH
      ? { executablePath: process.env.WUSHENG_EDGE_PATH }
      : undefined,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});
