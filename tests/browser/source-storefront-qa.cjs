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
      const cardMetrics = await page.locator(".section--surface .card-grid").evaluate(
        element => ({ width: element.clientWidth, scrollWidth: element.scrollWidth })
      );
      if (mobile) {
        assert.ok(cardMetrics.scrollWidth > cardMetrics.width,
          "Mobile product cards should be swipeable at " + width + "px");
      } else {
        assert.ok(cardMetrics.scrollWidth <= cardMetrics.width + 12,
          "Desktop product cards should fit their grid");
      }
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
      const mainLink = page.locator('.offer-cta a[href^="/go/"]').first();
      assert.equal(await mainLink.getAttribute("target"), "_blank",
        "External offer link requests a new browser tab without changing /go/");
      assert.match(await mainLink.getAttribute("rel"), /noopener/);
      assert.equal(await page.locator("[data-affiliate-copy]").count(), 1,
        "Only Owner-supplied links expose the original URL to copy");
      assert.equal(await page.locator("[data-affiliate-share-button]").count(), 1,
        "Only Owner-supplied links offer direct sharing of the original URL");
      if (width === 390) {
        const copyPanel = page.locator("[data-affiliate-copy]").first();
        await context.grantPermissions(["clipboard-read", "clipboard-write"], { origin });
        await copyPanel.locator("summary").click();
        const exact = "https://s.click.aliexpress.com/e/_OwnerBrowserFixture";
        assert.equal(await copyPanel.locator("[data-affiliate-copy-value]").inputValue(),
          exact, "Owner URL must not be regenerated or normalized");
        const shareButton = page.locator("[data-affiliate-share-button]");
        // Mock only the system Share UI; capture the actual argument sent by
        // the storefront and verify it is the owner's original literal link.
        await page.evaluate(() => {
          Object.defineProperty(navigator, "share", {
            configurable: true,
            value: async payload => { window.__capturedShare = payload; },
          });
        });
        const productTitle = "HIFU profissional - equipamento demonstrativo 1";
        const productId = "browser-qa-1-1";
        assert.equal(await shareButton.getAttribute("data-share-product-title"), productTitle);
        assert.equal(await shareButton.getAttribute("data-share-product-id"), productId);
        assert.match(await page.locator("[data-affiliate-actions] > p.meta").first().innerText(),
          /Produto a partilhar.*HIFU profissional.*browser-qa-1-1/);
        await shareButton.click();
        const description = "Produto Low Cost Europa: " + productTitle
          + "\nAliExpress ID: " + productId;
        assert.deepEqual(await page.evaluate(() => window.__capturedShare), {
          title: productTitle + " | Low Cost Europa",
          text: description,
          url: exact,
        }, "Mobile share must identify the correct product while keeping the original URL");
        assert.match(await page.locator("[data-affiliate-share-status]").innerText(),
          /enviados para partilha/i);
        await page.evaluate(() => {
          Object.defineProperty(navigator, "share", { configurable: true, value: undefined });
        });
        await shareButton.click();
        await page.waitForFunction(() => document.querySelector(
          "[data-affiliate-share-status]")?.textContent?.includes("copiada"));
        assert.equal(await page.evaluate(() => navigator.clipboard.readText()),
          description + "\n" + exact,
          "Share fallback must copy the exact product identity and untouched owner URL");
        assert.match(await page.locator("[data-affiliate-share-status]").innerText(),
          /copiada/i);
        report.checks.push({ page: "owner-affiliate-native-share-and-fallback",
          width, status: "PASS" });
        await copyPanel.locator("[data-affiliate-copy-button]").click();
        // Clipboard API is asynchronous; wait for the visible status announcement.
        await copyPanel.locator("[data-affiliate-copy-status]").waitFor({ state: "visible" });
        assert.match(await copyPanel.locator("[data-affiliate-copy-status]").innerText(),
          /copiado/i);
        assert.equal(await page.evaluate(() => navigator.clipboard.readText()), exact,
          "Clipboard must contain the exact original Owner short link");
        await copyPanel.locator("summary").click();
        report.checks.push({ page: "owner-affiliate-mobile-copy", width, status: "PASS" });
      }
      assert.equal(await page.locator(".whatsapp-float").isVisible(), !mobile,
        "Fixed contact button must not obscure mobile product filters");
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
      assert.equal(
        await page.locator(".compare-panel__actions a").first().getAttribute("target"),
        "_blank", "Compare CTA must also request a new tab"
      );
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

    // Verify language negotiation in a real mobile browser against the
    // existing Django source, with all five public category links intact.
    const languageCases = [
      { locale: "pt-PT", code: "pt-pt", heading: /Escolhas mais claras\./ },
      { locale: "es-ES", code: "es", heading: /Decisiones más claras\./ },
      { locale: "en-GB", code: "en", heading: /Clearer choices\./ },
      { locale: "fr-FR", code: "fr", heading: /Des choix plus clairs\./ },
      { locale: "de-DE", code: "de", heading: /Klarere Entscheidungen\./ },
    ];
    for (const { locale, code, heading } of languageCases) {
      const context = await browser.newContext({
        viewport: { width: 390, height: 844 },
        isMobile: true,
        hasTouch: true,
        locale,
        extraHTTPHeaders: { "Accept-Language": locale + ","
          + locale.slice(0, 2) + ";q=0.9" },
        reducedMotion: "reduce",
      });
      const page = await context.newPage();
      const pageErrors = [];
      page.on("pageerror", e => pageErrors.push(e.message));
      let res = await page.goto(origin + "/", { waitUntil: "networkidle" });
      assert.equal(res.status(), 200);
      await verify(page, "language:" + code, 390);
      assert.equal(await page.locator("html").getAttribute("lang"), code);
      assert.match(await page.locator("main h1").innerText(), heading);
      assert.equal(await page.locator(".family-index a").count(), 5);
      assert.equal(await page.locator(".product-card").count(), 5);
      assert.equal(await page.locator("main #familias").count(), 1);
      await page.screenshot({
        path: path.join(out, "home-lang-" + code + ".png"),
        fullPage: true, animations: "disabled",
      });

      // A language choice must override the browser locale on this device.
      if (code === "es") {
        await page.locator("#lang-footer").selectOption("fr");
        await page.locator("#idioma button[type=submit]").click();
        await page.waitForURL(origin + "/");
        assert.equal(await page.locator("html").getAttribute("lang"), "fr");
        assert.match(await page.locator("main h1").innerText(),
          /Des choix plus clairs/);
        const cookie = await context.cookies();
        assert.equal(cookie.find(c => c.name === "lowcost_language")?.value, "fr");
        report.checks.push({ page: "manual-language", width: 390, status: "PASS" });
      }
      assert.equal(pageErrors.length, 0, "Locale " + locale + ": " + pageErrors.join("; "));
      await context.close();
    }

    // Browser-only verification of the optional Android experiment.
    // This does NOT claim that Telegram WebView or Android native-app attribution
    // can be simulated by a Chromium user-agent override.
    const affiliateMobileCases = [
      { label: "telegram-android", userAgent:
        "Mozilla/5.0 (Linux; Android 13; Redmi Note 11) AppleWebKit/537.36 " +
        "(KHTML, like Gecko) Chrome/125.0 Mobile Safari/537.36 Telegram-Android/11.0",
        trial: true, shouldTrial: true },
      { label: "android-chrome", userAgent:
        "Mozilla/5.0 (Linux; Android 13; Redmi Note 11) AppleWebKit/537.36 " +
        "(KHTML, like Gecko) Chrome/125.0 Mobile Safari/537.36",
        trial: true, shouldTrial: true },
      { label: "telegram-default", userAgent:
        "Mozilla/5.0 (Linux; Android 13; Redmi Note 11) AppleWebKit/537.36 " +
        "(KHTML, like Gecko) Chrome/125.0 Mobile Safari/537.36 Telegram-Android/11.0",
        trial: false, shouldTrial: false },
      { label: "telegram-ios", userAgent:
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) " +
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Telegram-iOS/11.0",
        trial: true, shouldTrial: false },
    ];
    for (const c of affiliateMobileCases) {
      const context = await browser.newContext({
        viewport: { width: 390, height: 844 },
        isMobile: true, hasTouch: true, userAgent: c.userAgent,
        locale: "pt-PT", reducedMotion: "reduce",
      });
      const page = await context.newPage();
      const url = origin + "/products/hifu-profissional/" +
        (c.trial ? "?teste_chrome=1" : "");
      const res = await page.goto(url, { waitUntil: "networkidle" });
      assert.equal(res.status(), 200);
      const ownerLink = page.locator("[data-affiliate-browser-trial]");
      assert.equal(await ownerLink.count(), 1);
      const original = await page.locator("[data-affiliate-copy-value]").inputValue();
      assert.equal(original, "https://s.click.aliexpress.com/e/_OwnerBrowserFixture");
      const href = await ownerLink.getAttribute("href");
      if (c.shouldTrial) {
        assert.ok(href.startsWith("intent://s.click.aliexpress.com/e/_OwnerBrowserFixture#Intent;"),
          c.label + " must preserve the entire owner shortlink in the opt-in intent");
        assert.match(href, /package=com\.android\.chrome;/);
        const fallback = href.match(/S\.browser_fallback_url=([^;]+);end$/);
        assert.ok(fallback, "Intent must contain a safe original URL fallback");
        assert.equal(decodeURIComponent(fallback[1]), original,
          "Fallback must remain the byte-for-byte original Owner shortlink");
        assert.equal(await ownerLink.getAttribute("target"), null);
        assert.equal(await ownerLink.getAttribute("data-chrome-trial-active"), "true");
        assert.equal(await page.locator('.offer-cta a[href^="/go/"]').count(), 3,
          "Non-owner offerings must retain their existing /go/ links");
      } else {
        assert.match(href, /^\/go\/[0-9]+\/$/,
          "Without an eligible opt-in, the original /go/ must be unchanged");
        assert.equal(await ownerLink.getAttribute("target"), "_blank");
        assert.equal(await ownerLink.getAttribute("data-chrome-trial-active"), null);
        assert.equal(await page.locator('.offer-cta a[href^="/go/"]').count(), 4);
      }
      report.checks.push({
        page: "telegram-android-affiliate-chrome-trial:" + c.label,
        width: 390, status: "PASS",
      });
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
