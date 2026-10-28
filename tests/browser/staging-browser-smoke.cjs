'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

// Public, read-only QA: no authentication, POST, purchases or /go/ visits.
const origin = 'https://lowcost-europa.duckdns.org';
const out = path.resolve('qa-artifacts');
const slugs = ['cavitacao-rf-vacuum-corpo',
  'hydrodermoabrasao-aqua-facial-multifuncoes',
  'pressoterapia-vacuum-drenagem', 'hifu',
  'diodo-laser-remocao-tatuagens-pigmentacao'];
const pages = [{ name: 'home', url: '/' }].concat(
  slugs.map((name) => ({ name, url: '/products/' + name + '/' })),
  [{ name: 'search', url: '/pesquisar/?q=HIFU' }]);
const devices = [{ name: 'desktop', width: 1440, height: 900, mobile: false },
  { name: 'mobile-emulated', width: 390, height: 844, mobile: true }];
const report = { origin, when: new Date().toISOString(), checks: [], errors: [], warnings: [] };
fs.mkdirSync(out, { recursive: true });
const fail = (scope, err) => report.errors.push({
  scope, message: String(err.message || err).slice(0, 600),
});

async function guardChecks(context) {
  const robots = await context.request.get(origin + '/robots.txt', { timeout: 25000 });
  assert.equal(robots.status(), 200);
  assert.match(await robots.text(), /Disallow:\s*\//i);
  const js = await context.request.get(
    origin + '/static/storefront/product-images.js', { timeout: 25000 });
  assert.equal(js.status(), 200);
  assert.match(await js.text(), /data-product-image/);
  const owner = await context.request.get(
    origin + '/painel/', { maxRedirects: 0, timeout: 25000 });
  assert.equal(owner.status(), 302, 'anonymous owner panel must redirect');
  report.checks.push({ scope: 'http', status: 'PASS',
    robots: 'Disallow: /', imageJs: 200, anonymousOwner: 302 });
}

async function photoChecks(page, scope) {
  const images = page.locator('img[data-product-image]');
  const count = await images.count();
  const samples = [];
  for (let i = 0; i < Math.min(count, scope.endsWith(':hifu') ? 10 : 5); i++) {
    const img = images.nth(i);
    await img.scrollIntoViewIfNeeded({ timeout: 10000 });
    await img.evaluate((el) => new Promise((done) => {
      if (el.complete) return done();
      let settled = false;
      const end = () => { if (!settled) { settled = true; done(); } };
      el.addEventListener('load', end, { once: true });
      el.addEventListener('error', end, { once: true });
      setTimeout(end, 5000);
    }));
    const v = await img.evaluate((el) => {
      const wrapper = el.parentElement;
      const warning = wrapper.querySelector('[data-image-quality]');
      const fallback = wrapper.querySelector('[data-image-fallback]');
      return { https: el.src.startsWith('https://'), complete: el.complete,
        width: el.naturalWidth, height: el.naturalHeight,
        lowResolutionWarning: Boolean(warning && !warning.hidden),
        errorFallback: Boolean(fallback && !fallback.hidden) };
    });
    assert.equal(v.https, true, 'HTTPS image: ' + scope);
    if (v.complete && v.width > 0 && v.height > 0
        && (v.width < 360 || v.height < 270)) {
      assert.equal(v.lowResolutionWarning, true, 'small image label: ' + scope);
    }
    if (v.complete && (!v.width || !v.height))
      assert.equal(v.errorFallback, true, 'broken image fallback: ' + scope);
    if (!v.complete)
      report.warnings.push({ scope, detail: 'supplier image still loading' });
    samples.push(v);
  }
  return { count, samples };
}

async function publicPage(page, item, device) {
  const scope = device.name + ':' + item.name;
  const res = await page.goto(origin + item.url,
    { waitUntil: 'domcontentloaded', timeout: 35000 });
  assert.ok(res, 'no response in ' + scope);
  assert.equal(res.status(), 200, 'HTTP 200: ' + scope);
  assert.match(res.headers()['x-robots-tag'] || '', /noindex/i);
  assert.equal(await page.locator('main#conteudo').count(), 1);
  assert.equal(await page.locator('main h1').count(), 1);
  assert.match(await page.locator('meta[name="robots"]').getAttribute('content'),
    /noindex/i);
  assert.equal(await page.locator('script[src*="product-images.js"]').count(), 1);
  const size = await page.evaluate(() =>
    ({ screen: innerWidth, full: document.documentElement.scrollWidth }));
  assert.ok(size.full - size.screen <= 12,
    'horizontal overflow ' + (size.full - size.screen) + 'px in ' + scope);
  const links = await page.locator('a[href*="/go/"]').evaluateAll(
    (els) => els.map((el) => el.getAttribute('href')));
  assert.ok(links.every((href) => /^\/go\/\d+\/$/.test(href)),
    'unexpected affiliate URL in ' + scope);
  const photos = await photoChecks(page, scope);
  // html uses smooth scrolling: force the real initial viewport before capturing.
  await page.evaluate(() => {
    document.documentElement.style.scrollBehavior = 'auto';
    document.body.style.scrollBehavior = 'auto';
    window.scrollTo({ top: 0, behavior: 'instant' });
  });
  await page.waitForFunction(() => window.scrollY === 0, null, { timeout: 5000 });
  await page.screenshot({ path: path.join(out, item.name + '-' + device.name + '.png'),
    fullPage: true, animations: 'disabled' });
  if (item.name === 'home') {
    const finder = page.locator('.search-form--hero input[name="q"]');
    assert.equal(await finder.count(), 1, 'global search present on home');
    assert.equal(await finder.isVisible(), true, 'home search accessible');
    const target = await finder.evaluate((el) => el.form.action);
    assert.equal(new URL(target).pathname, '/pesquisar/');
  } else {
    const explorer = page.locator('[data-catalog-explorer]');
    if (await explorer.count()) {
      const cardCount = await explorer.locator('[data-offer-card]').count();
      assert.ok(cardCount > 0, 'explorer has published cards');
      await explorer.locator('[data-explorer-search]').fill('never-found-ux-test-92874');
      assert.equal(
        await explorer.locator('[data-offer-card]:visible').count(), 0,
        'search hides cards without changing publication state'
      );
      assert.equal(await explorer.locator('[data-explorer-empty]').isVisible(), true);
      await explorer.locator('[data-explorer-reset]').click();
      assert.equal(
        await explorer.locator('[data-offer-card]:visible').count(), cardCount,
        'reset restores every original offer'
      );
      const first = explorer.locator('[data-compare-toggle]').first();
      assert.equal(await first.isVisible(), true);
      await first.click();
      assert.equal(await first.getAttribute('aria-pressed'), 'true');
      assert.equal(await explorer.locator('[data-compare-panel]').isVisible(), true);
      await explorer.locator('[data-compare-clear]').click();
      assert.equal(await first.getAttribute('aria-pressed'), 'false');
      assert.equal(await explorer.locator('[data-compare-panel]').isVisible(), false);
      await explorer.locator('[data-explorer-budget]').selectOption('500');
      assert.match(await explorer.locator('[data-currency-notice]').textContent(), /EUR/);
      await explorer.locator('[data-explorer-sort]').selectOption('price-asc');
      assert.equal(await explorer.locator('[data-currency-notice]').count(), 1);
      await explorer.locator('[data-explorer-reset]').click();
    }
  }
  if (device.mobile && item.name === 'home') {
    await page.locator('.nav-menu summary').click();
    assert.equal(await page.locator('.nav-menu').evaluate((el) => el.open), true);
    await page.locator('.site-nav a').filter({ hasText: 'Produtos' }).click();
    assert.match(page.url(), /#familias$/);
  }
  report.checks.push({ scope, status: 'PASS',
    overflow: size.full - size.screen, affiliateLinks: links.length, photos });
  console.log('BROWSER_QA_OK ' + scope + ' images=' + photos.count
    + ' overflow=' + (size.full - size.screen) + ' affiliateLinks=' + links.length);
}

async function run() {
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    for (const device of devices) {
      const context = await browser.newContext({
        viewport: { width: device.width, height: device.height },
        isMobile: device.mobile, hasTouch: device.mobile,
        locale: 'pt-PT', ignoreHTTPSErrors: false });
      if (!device.mobile)
        try { await guardChecks(context); } catch (err) { fail('http-guards', err); }
      for (const item of pages) {
        const page = await context.newPage();
        const scope = device.name + ':' + item.name;
        page.on('pageerror', (err) => fail(scope + ':javascript', err));
        try { await publicPage(page, item, device); }
        catch (err) { fail(scope, err); }
        finally { await page.close(); }
      }
      await context.close();
    }
  } catch (err) { fail('browser', err); }
  finally {
    if (browser) await browser.close();
    report.status = report.errors.length ? 'FAIL' : 'PASS';
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(report, null, 2));
    console.log('BROWSER_QA_RESULT=' + report.status
      + ' checks=' + report.checks.length + ' errors=' + report.errors.length);
    for (const err of report.errors)
      console.error('BROWSER_QA_ERROR ' + err.scope + ': ' + err.message);
    process.exitCode = report.errors.length ? 1 : 0;
  }
}
run();