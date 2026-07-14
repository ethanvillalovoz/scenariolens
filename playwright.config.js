const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "tests/browser",
  outputDir: "output/playwright/test-results",
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    browserName: "chromium",
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "python3 -m http.server 8131 --directory docs",
      url: "http://127.0.0.1:8131/demo/",
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
    },
    {
      command: "sh -c 'PYTHONPATH=src python3 -m scenariolens.cli export-synthetic --output /tmp/scenariolens-browser-synthetic.json && PYTHONPATH=src python3 -m scenariolens.cli run --input /tmp/scenariolens-browser-synthetic.json --format scenariolens-json --output /tmp/scenariolens-browser-run --max-scenarios 11 --top 6 && python3 -m http.server 8132 --directory /tmp/scenariolens-browser-run'",
      url: "http://127.0.0.1:8132/explorer/",
      reuseExistingServer: !process.env.CI,
      timeout: 60000,
    },
  ],
});
