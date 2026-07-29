import { expect, test } from "@playwright/test";

test.describe("FA-FR-001 ATE Dashboard", () => {
  test("dashboard renders ingestion navigation", async ({ page }) => {
    await page.goto("/overview");
    await expect(page.getByText("Semiconductor Failure Analysis Overview")).toBeVisible();
    await expect(page.getByRole("link", { name: "Ingestion" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Datasets" })).toBeVisible();
  });

  test("upload page requires STIL and tester logs before Analyze", async ({ page }) => {
    await page.goto("/upload");
    await expect(page.getByText("FA-FR-001 Data Ingestion")).toBeVisible();
    await expect(page.getByText("Upload Semiconductor Dataset")).toBeVisible();
    await expect(page.getByTestId("stil-dropzone")).toBeVisible();
    await expect(page.getByTestId("log-dropzone")).toBeVisible();
    await expect(page.getByTestId("analyze-button")).toBeDisabled();
    await expect(
      page.getByText(/Analyze stays disabled until both STIL and tester logs/i),
    ).toBeVisible();
  });

  test("overview page exposes analysis KPI section", async ({ page }) => {
    await page.goto("/overview");
    await expect(page.getByText("Semiconductor Failure Analysis Overview")).toBeVisible();
    await expect(page.getByText("Analysis KPIs")).toBeVisible();
    await expect(
      page.getByText(/populate live KPI cards from the backend pipeline/i),
    ).toBeVisible();
  });

  test("history page shows analysis history table", async ({ page }) => {
    await page.goto("/history");
    await expect(page.getByText("Analysis History")).toBeVisible();
    await expect(page.getByTestId("analysis-history")).toBeVisible();
  });

  test("overview exposes workbench sections when execution context exists", async ({ page }) => {
    await page.goto("/overview");
    await expect(page.getByText("Semiconductor Failure Analysis Overview")).toBeVisible();
    await expect(page.getByText("Analysis KPIs")).toBeVisible();
  });

  test("pattern detection dashboard exposes enterprise analysis views", async ({ page }) => {
    await page.goto("/patterns");
    await expect(page.getByText("Failure Pattern Detection")).toBeVisible();
    await expect(page.getByText("Pattern Frequency")).toBeVisible();
    await expect(page.getByText("Confidence Score")).toBeVisible();
    await expect(page.getByText("Benchmark Dashboard")).toBeVisible();
    await expect(page.getByRole("button", { name: /Run Detection/ })).toBeVisible();
  });

  test("failure rate dashboard exposes analytics and computation controls", async ({ page }) => {
    await page.goto("/failure-rates");
    await expect(page.getByText("Failure Rate Computation")).toBeVisible();
    await expect(page.getByText("Pattern Failure Summary")).toBeVisible();
    await expect(page.getByText("Failure Trend Charts")).toBeVisible();
    await expect(page.getByText("Benchmark Dashboard")).toBeVisible();
    await expect(page.getByRole("button", { name: /Run Computation/ })).toBeVisible();
  });

  test("recurrence dashboard exposes historical and hotspot analytics", async ({ page }) => {
    await page.goto("/recurrence");
    await expect(page.getByText("Recurring Failure Identification")).toBeVisible();
    await expect(page.getByText("Pattern Frequency")).toBeVisible();
    await expect(page.getByText(/Hotspot Heatmap/)).toBeVisible();
    await expect(page.getByText("Engineering Recommendation")).toBeVisible();
    await expect(page.getByText("Evaluation Benchmark Metrics")).toBeVisible();
    await expect(
      page.getByRole("button", { name: /Run Recurrence Analysis/ }),
    ).toBeVisible();
  });

  test("correlation dashboard exposes matrix graph trends and recommendations", async ({ page }) => {
    await page.goto("/correlation");
    await expect(page.getByText("Failure-to-Pattern Correlation")).toBeVisible();
    await expect(page.getByText("Failure-to-Pattern Correlation Matrix")).toBeVisible();
    await expect(page.getByText(/Pattern Relationship Graph/)).toBeVisible();
    await expect(page.getByText("Confidence Score Dashboard")).toBeVisible();
    await expect(page.getByText(/Engineering Recommendation/)).toBeVisible();
    await expect(page.getByRole("button", { name: /Run Correlation/ })).toBeVisible();
  });

  test("die analysis dashboard exposes wafer map controls and recommendations", async ({
    page,
  }) => {
    await page.goto("/die-analysis");
    await expect(page.getByText("Die-Level Failure Analysis")).toBeVisible();
    await expect(page.getByText(/Wafer Map/)).toBeVisible();
    await expect(page.getByText("Failure Density")).toBeVisible();
    await expect(page.getByText("Die Health Scores")).toBeVisible();
    await expect(page.getByText("Density Trends")).toBeVisible();
    await expect(page.getByText("Evaluation Benchmark Metrics")).toBeVisible();
    await expect(page.getByText(/Engineering Recommendation/)).toBeVisible();
    await expect(page.getByRole("button", { name: /Run Die Analysis/ })).toBeVisible();
    await expect(page.getByRole("link", { name: "Die Analysis" })).toBeVisible();
  });

  test("wafer analysis dashboard exposes wafer map controls and recommendations", async ({
    page,
  }) => {
    await page.goto("/wafer-analysis");
    await expect(page.getByText("Wafer-Level Failure Analysis")).toBeVisible();
    await expect(page.getByText(/Wafer Map/)).toBeVisible();
    await expect(page.getByText("Wafer Yield")).toBeVisible();
    await expect(page.getByText("Radial Distribution")).toBeVisible();
    await expect(page.getByText("Edge vs Center Failure Rates")).toBeVisible();
    await expect(page.getByText("Wafer Health Scores")).toBeVisible();
    await expect(page.getByText("Evaluation Benchmark Metrics")).toBeVisible();
    await expect(page.getByText(/Engineering Recommendation/)).toBeVisible();
    await expect(page.getByRole("button", { name: /Run Wafer Analysis/ })).toBeVisible();
    await expect(page.getByRole("link", { name: "Wafer Analysis" })).toBeVisible();
  });

  test("fault prediction dashboard exposes AI prediction controls and analytics", async ({
    page,
  }) => {
    await page.goto("/fault-prediction");
    await expect(page.getByText("AI Fault Type Prediction")).toBeVisible();
    await expect(page.getByText("Confidence Score Dashboard")).toBeVisible();
    await expect(page.getByText("Ranked Prediction Table")).toBeVisible();
    await expect(page.getByText("Engineering Explanation Panel")).toBeVisible();
    await expect(page.getByText("Prediction Trend · Historical Comparison")).toBeVisible();
    await expect(page.getByText("Feedback Submission Panel")).toBeVisible();
    await expect(page.getByText("Evaluation Benchmark Metrics")).toBeVisible();
    await expect(page.getByRole("button", { name: /Run Prediction/ })).toBeVisible();
    await expect(page.getByRole("link", { name: "Fault Prediction" })).toBeVisible();
  });

  test("reports dashboard exposes decision support and export views", async ({ page }) => {
    await page.goto("/reports");
    await expect(page.getByText("Reporting & Decision Support Dashboard")).toBeVisible();
    await expect(page.getByText("Executive Summary Cards")).toBeVisible();
    await expect(page.getByText("Engineering Summary Panels")).toBeVisible();
    await expect(page.getByText("Benchmark Dashboard")).toBeVisible();
    await expect(page.getByText("AI Prediction Summary")).toBeVisible();
    await expect(page.getByText("Recommendations Panel")).toBeVisible();
    await expect(page.getByText("Template selector")).toBeVisible();
    await expect(page.getByText("Export Panel")).toBeVisible();
    await expect(page.getByText("Report History Table")).toBeVisible();
    await expect(page.getByRole("button", { name: /Generate Report/ })).toBeVisible();
    await expect(page.getByRole("link", { name: "Reports" })).toBeVisible();
  });

  test("login page renders sign-in form", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
  });

  test("settings page is reachable", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByText("Application Settings")).toBeVisible();
    await expect(page.getByTestId("settings-form")).toBeVisible();
  });

  test("system health page shows health cards", async ({ page }) => {
    await page.goto("/system-health");
    await expect(page.getByText("System Health")).toBeVisible();
    await expect(page.getByTestId("system-health")).toBeVisible();
  });

  test("audit page exposes filters", async ({ page }) => {
    await page.goto("/audit");
    await expect(page.getByText("Audit Logs")).toBeVisible();
    await expect(page.getByLabel("Search audit logs")).toBeVisible();
  });

  test("storage page renders table", async ({ page }) => {
    await page.goto("/storage");
    await expect(page.getByText("Dataset Storage")).toBeVisible();
    await expect(page.getByTestId("storage-table")).toBeVisible();
  });
});
