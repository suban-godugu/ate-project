import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const API = process.env.PLAYWRIGHT_API_URL ?? "http://localhost:8000/api/v1";
const FIXTURE = path.resolve(__dirname, "../../backend/tests/fixtures/sample.stdf");

test.describe("Critical path", () => {
  test.beforeEach(() => {
    test.skip(
      process.env.E2E_LIVE !== "1",
      "Set E2E_LIVE=1 with dashboard (:3000), API (:8000), and ARQ worker running"
    );
    test.skip(!fs.existsSync(FIXTURE), "STDF fixture missing — run backend/scripts/build_stdf_fixture.py");
  });

  test("login → upload → dashboard data → approve recommendation", async ({ page, request }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill("alex@verilumen.ai");
    await page.getByLabel("Password").fill("changeme123");
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL("**/dashboard**", { timeout: 30_000 });

    const token = await page.evaluate(() => localStorage.getItem("verilumen_access_token"));
    expect(token).toBeTruthy();

    const raw = fs.readFileSync(FIXTURE);
    const presign = await request.post(`${API}/uploads/presign`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        file_name: "sample.stdf",
        size: raw.length,
        kind: "data",
        module: "scan-chain",
      },
    });
    expect(presign.ok()).toBeTruthy();
    const { job_id, upload_url } = await presign.json();

    const put = await request.put(upload_url, {
      headers: { "Content-Type": "application/octet-stream" },
      data: raw,
    });
    expect(put.ok()).toBeTruthy();

    const crypto = await import("node:crypto");
    const checksum = crypto.createHash("sha256").update(raw).digest("hex");
    const complete = await request.post(`${API}/uploads/${job_id}/complete`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { checksum_sha256: checksum },
    });
    expect(complete.ok()).toBeTruthy();

    let status = "Parsing";
    for (let i = 0; i < 90 && status !== "Completed"; i++) {
      const jobRes = await request.get(`${API}/uploads/${job_id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      status = (await jobRes.json()).job?.status ?? status;
      if (status === "Failed") break;
      await page.waitForTimeout(2000);
    }
    expect(status).toBe("Completed");

    await page.goto("/dashboard/scan-chain");
    await expect(page.getByText(/scan chain/i).first()).toBeVisible({ timeout: 30_000 });

    await page.goto("/dashboard/recommendation-analysis");
    await page.getByRole("tab", { name: /pattern agent/i }).click();

    const approve = page.getByRole("button", { name: /approve/i }).first();
    await expect(approve).toBeVisible({ timeout: 30_000 });
    await approve.click();
    await expect(page.getByText(/approved/i).first()).toBeVisible({ timeout: 15_000 });
  });
});
