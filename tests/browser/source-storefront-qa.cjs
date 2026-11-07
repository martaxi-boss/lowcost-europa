"use strict";

// Browser QA for current PR source on an isolated Django server.
// No external images, no real affiliate redirect, no database outside CI.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const origin = "http://127.0.0.1:8787";
const out = path.resolve("qa-artifacts/source-browser");
const widths = [360, 390, 430, 1440];
const report = { origin, widths, checks: [], errors: [], warnings: [] };
fs.mkdirSync(out, { recursive: true });

async function verify(page, name, width) {
  const overflow = await page.evaluate(() =>
    Math.max(0, document.documentElement.scrollWidth - window.innerWidth));
  assert.ok(overflow <= 12, name + " @" + width + "px horizontal overflow: " + overflow);
  assert.equal(await page.locator("main#conteudo").count(), 1);
  assert.equal(await page.locator("main h1").count(), 1);
  assert.match(await page.locator('meta[name="robots"]').getAttribute("content"),
    /noindex/);
  report.checks.push({ page: name, width, overflow, status: "PASS" });
}

async function main() {
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    for (const width of widths) {
      const mobile = width < 760;
      const context = await browser.newContext({
        viewport: { width, height: 844 },
        isMobile: mobile,
        hasTouch: mobile,
        locale: "pt-PT",
        reducedMotion: "reduce",
      });
      const page = await context.newPage();
      const errors = [];
      page.on("pageerror", e => errors.push(e.message));

      let res = await page.goto(origin + "/", { waitUntil: "networkidle" });
      assert.equal(res.status(), 200);
      await verify(page, "home", width);
      assert.equal(await page.locator(".product-card").count(), 5);
      assert.match(await page.locator("h1").innerText(), /Equipamentos de estética/);
      assert.match(await page.locator(".family-index").innerText(), /HIFU profissional/);
      if (width === 390 || width === 1440) {
        await page.screenshot({
          path: path.join(out, "home-" + width + ".png"),
          fullPage: true,
          animations: "disabled",
        });
      }

      res = await page.goto(origin + "/products/hifu-profissional/",
        { waitUntil: "networkidle" });
      assert.equal(res.status(), 200);
      await verify(page, "detail", width);
      assert.equal(await page.locator("[data-offer-card]").count(), 4);
      assert.equal(await page.locator("[data-compare-dock]").isVisible(), false);
      assert.equal(await page.locator("[data-compare-panel]").isVisible(), false);
      const controls = page.locator("[data-compare-toggle]");
      assert.equal(await controls.count(), 4);
      assert.equal(await controls.first().isVisible(), true);
      await controls.nth(0).click();
      assert.equal(await controls.nth(0).getAttribute("aria-pressed"), "true");
      assert.equal(await page.locator("[data-compare-dock]").isVisible(), true);
      assert.equal(await page.locator("[data-compare-panel]").isVisible(), true);
      assert.match(await page.locator("[data-compare-dock-count]").innerText(), /1 de 3/);
      await controls.nth(1).click();
      await controls.nth(2).click();
      assert.match(await page.locator("[data-compare-dock-count]").innerText(), /3 de 3/);
      await controls.nth(3).click();
      assert.equal(await page.locator("[data-compare-results] article").count(), 3);
      assert.match(await page.locator("[data-compare-message]").innerText(),
        /Limite de três/);
      await page.locator("[data-compare-show]").click();
      assert.equal(await page.evaluate(() =>
        document.activeElement?.hasAttribute("data-compare-heading")), true);
      await page.locator("[data-compare-clear]").click();
      assert.equal(await page.locator("[data-compare-dock]").isVisible(), false);
      assert.equal(await page.locator("[data-compare-panel]").isVisible(), false);
      await page.locator("[data-explorer-budget]").selectOption("500");
      assert.equal(await page.locator("[data-offer-card]:visible").count(), 1);
      await page.locator("[data-explorer-reset]").click();
      assert.equal(await page.locator("[data-offer-card]:visible").count(), 4);
      await page.locator("[data-explorer-search]").fill("term-not-found-928");
      assert.equal(await page.locator("[data-offer-card]:visible").count(), 0);
      assert.equal(await page.locator("[data-explorer-empty]").isVisible(), true);
      await page.locator("[data-explorer-reset]").click();
      if (width === 390 || width === 1440) {
        // A full-page shot must start at document top, otherwise a sticky header
        // is captured midway through the page after test interactions.
        await page.evaluate(() => {
          document.documentElement.style.scrollBehavior = "auto";
          document.body.style.scrollBehavior = "auto";
          window.scrollTo({ top: 0, behavior: "instant" });
        });
        await page.waitForFunction(() => window.scrollY === 0);
        await page.screenshot({
          path: path.join(out, "detail-" + width + ".png"),
          fullPage: true,
          animations: "disabled",
        });
      }

      res = await page.goto(origin + "/pesquisar/?q=hifu",
        { waitUntil: "networkidle" });
      assert.equal(res.status(), 200);
      await verify(page, "search", width);
      assert.match(await page.locator("main").innerText(), /HIFU profissional/i);
      assert.equal(errors.length, 0, "JavaScript errors @" + width + ": " + errors.join("; "));
      await page.close();
      await context.close();
    }
  } catch (e) {
    report.errors.push(String(e.stack || e));
  } finally {
    if (browser) await browser.close();
    report.status = report.errors.length ? "FAIL" : "PASS";
    fs.writeFileSync(path.join(out, "result.json"), JSON.stringify(report, null, 2));
    console.log("SOURCE_BROWSER_QA_RESULT=" + report.status);
    console.log("SOURCE_BROWSER_QA_CHECKS=" + report.checks.length);
    for (const e of report.errors) console.error(e);
    if (report.errors.length) process.exitCode = 1;
  }
}
main();
