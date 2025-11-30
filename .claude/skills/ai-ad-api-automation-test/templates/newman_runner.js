/**
 * Newman API Test Runner
 *
 * Reference: sanbercode-api-automation-boilerplate
 * https://github.com/jfrelis/sanbercode-api-automation-boilerplate
 *
 * SoT Alignment:
 * - API_SOT.md v9.0 (API endpoints)
 * - STATE_MACHINE.md v2.6 (state transitions)
 * - ERROR_CODES_SOT.md v2.1 (error codes)
 *
 * Usage:
 *   node newman_runner.js [collection] [environment]
 *
 * Examples:
 *   node newman_runner.js daily_report_api.json local.json
 *   API_BASE_URL=http://localhost:8000 node newman_runner.js
 */

const newman = require("newman");
const path = require("path");

// ============================================================
// Configuration
// ============================================================

const args = process.argv.slice(2);
const collectionFile = args[0] || "api_collection.json";
const environmentFile = args[1] || "local.json";

const rootDir = path.resolve(__dirname, "../..");
const collectionsDir = path.join(rootDir, "collections");
const environmentsDir = path.join(rootDir, "environments");
const reportsDir = path.join(rootDir, "reports");

const config = {
  // Collection path
  collection: path.join(collectionsDir, collectionFile),

  // Environment path (optional)
  environment: path.join(environmentsDir, environmentFile),

  // Reporters
  reporters: ["cli", "htmlextra", "json"],

  reporter: {
    // HTML Extra Reporter Configuration
    htmlextra: {
      export: path.join(reportsDir, `${path.basename(collectionFile, ".json")}_report.html`),
      title: "AI Ad Spend API Test Report",
      browserTitle: "API Tests - AI Ad Spend",
      showOnlyFails: false,
      noSyntaxHighlighting: false,
      testPaging: true,
      logs: true,
      omitRequestBodies: false,
      omitResponseBodies: false,
      showEnvironmentData: true,
      showGlobalData: true,
      skipHeaders: ["Authorization"], // Hide sensitive headers
      timezone: "Asia/Shanghai",
    },

    // JSON Reporter for CI integration
    json: {
      export: path.join(reportsDir, `${path.basename(collectionFile, ".json")}_report.json`),
    },
  },

  // Environment variable overrides
  envVar: [
    {
      key: "BASE_URL",
      value: process.env.API_BASE_URL || "http://localhost:8000",
    },
    {
      key: "API_VERSION",
      value: process.env.API_VERSION || "v1",
    },
  ],

  // Timeout settings (milliseconds)
  timeout: {
    request: 30000, // 30 seconds per request
    script: 30000,  // 30 seconds per script
  },

  // Iteration settings
  iterationCount: 1,

  // Delay between requests (milliseconds)
  delayRequest: 100,

  // Bail on first failure (useful for debugging)
  bail: process.env.BAIL_ON_FAILURE === "true",

  // Ignore SSL errors (for local development)
  insecure: process.env.NODE_ENV !== "production",
};

// ============================================================
// Runner
// ============================================================

console.log("\n========================================");
console.log("  AI Ad Spend API Test Runner");
console.log("========================================");
console.log(`Collection: ${collectionFile}`);
console.log(`Environment: ${environmentFile}`);
console.log(`Base URL: ${config.envVar[0].value}`);
console.log("----------------------------------------\n");

newman.run(config, function (err, summary) {
  if (err) {
    console.error("\n[ERROR] Newman run failed:");
    console.error(err);
    process.exit(1);
  }

  // ============================================================
  // Results Summary
  // ============================================================

  const stats = summary.run.stats;
  const failures = summary.run.failures || [];

  console.log("\n========================================");
  console.log("  Test Results Summary");
  console.log("========================================");
  console.log(`Total Requests: ${stats.requests.total}`);
  console.log(`  - Pending:  ${stats.requests.pending}`);
  console.log(`  - Failed:   ${stats.requests.failed}`);
  console.log("");
  console.log(`Total Tests: ${stats.tests.total}`);
  console.log(`  - Passed:   ${stats.tests.total - stats.tests.failed}`);
  console.log(`  - Failed:   ${stats.tests.failed}`);
  console.log("");
  console.log(`Total Assertions: ${stats.assertions.total}`);
  console.log(`  - Passed:   ${stats.assertions.total - stats.assertions.failed}`);
  console.log(`  - Failed:   ${stats.assertions.failed}`);
  console.log("----------------------------------------");

  // Pass Rate
  const passRate = stats.tests.total > 0
    ? ((stats.tests.total - stats.tests.failed) / stats.tests.total * 100).toFixed(2)
    : 0;
  console.log(`\nPass Rate: ${passRate}%`);

  // ============================================================
  // Failed Tests Details
  // ============================================================

  if (failures.length > 0) {
    console.log("\n========================================");
    console.log("  Failed Tests");
    console.log("========================================");

    failures.forEach((failure, index) => {
      console.log(`\n[${index + 1}] ${failure.source.name || "Unknown Test"}`);
      console.log(`    Error: ${failure.error.message || failure.error.name}`);
      if (failure.error.test) {
        console.log(`    Test:  ${failure.error.test}`);
      }
      if (failure.at) {
        console.log(`    At:    ${failure.at}`);
      }
    });

    console.log("\n----------------------------------------");
  }

  // ============================================================
  // Report Locations
  // ============================================================

  console.log("\n========================================");
  console.log("  Reports Generated");
  console.log("========================================");
  console.log(`HTML: ${config.reporter.htmlextra.export}`);
  console.log(`JSON: ${config.reporter.json.export}`);
  console.log("----------------------------------------\n");

  // ============================================================
  // Exit Code
  // ============================================================

  if (stats.tests.failed > 0 || stats.assertions.failed > 0) {
    console.log("[RESULT] Some tests failed. See reports for details.\n");
    process.exit(1);
  } else {
    console.log("[RESULT] All tests passed!\n");
    process.exit(0);
  }
});
