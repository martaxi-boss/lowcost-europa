// Run with: node --test tests/js/product-images.test.cjs
// Pure built-in Node test runner: no browser, remote images or npm dependencies.
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const code = readFileSync(
  path.resolve(__dirname, "../../apps/storefront/static/storefront/product-images.js"),
  "utf8"
);

function makeImage({ width = 0, height = 0, complete = false, loading = "lazy", offer = true } = {}) {
  const listeners = {};
  const fallback = { hidden: true };
  const quality = { hidden: true };
  const classes = new Set([offer ? "offer-card__media" : "product-card__media"]);
  const container = {
    classList: {
      contains(name) { return classes.has(name); },
      add(name) { classes.add(name); },
    },
    querySelector(selector) {
      if (selector === "[data-image-fallback]") return fallback;
      if (selector === "[data-image-quality]") return quality;
      return null;
    },
  };
  const image = {
    naturalWidth: width,
    naturalHeight: height,
    complete,
    loading,
    hidden: false,
    style: {},
    parentElement: container,
    addEventListener(name, callback) { listeners[name] = callback; },
  };
  vm.runInNewContext(code, {
    document: { querySelectorAll(selector) {
      assert.equal(selector, "img[data-product-image]");
      return [image];
    } },
  });
  return { image, fallback, quality, classes, fire: (name) => listeners[name]() };
}

test("a not-yet-requested lazy image is never prematurely replaced", () => {
  const state = makeImage({ complete: true, width: 0, height: 0, loading: "lazy" });
  assert.equal(state.image.hidden, false);
  assert.equal(state.fallback.hidden, true);
  state.image.naturalWidth = 1080;
  state.image.naturalHeight = 1080;
  state.fire("load");
  assert.equal(state.image.hidden, false);
  assert.equal(state.quality.hidden, true);
});

test("a failed remote image is replaced by an honest placeholder", () => {
  const state = makeImage({ offer: false });
  state.fire("error");
  assert.equal(state.image.hidden, true);
  assert.equal(state.fallback.hidden, false);
  assert.equal(state.quality.hidden, true);
  assert.equal(state.classes.has("product-card__media--placeholder"), true);
});

test("small supplier images are labelled and not upscaled", () => {
  const state = makeImage({ width: 123, height: 123, complete: true });
  assert.equal(state.image.hidden, false);
  assert.equal(state.quality.hidden, false);
  assert.equal(state.image.style.maxWidth, "123px");
  assert.equal(state.image.style.maxHeight, "123px");
  assert.equal(state.fallback.hidden, true);
});

test("large images are shown without a warning", () => {
  const state = makeImage({ width: 1080, height: 1080, complete: true });
  assert.equal(state.image.hidden, false);
  assert.equal(state.quality.hidden, true);
  assert.equal(state.image.style.maxWidth, undefined);
});

test("already-failed eager images are shown as unavailable", () => {
  const state = makeImage({ width: 0, height: 0, complete: true, loading: "eager" });
  assert.equal(state.image.hidden, true);
  assert.equal(state.fallback.hidden, false);
});

test("a lazy image that later fails gets a placeholder on error", () => {
  const state = makeImage({ width: 0, height: 0, complete: true, loading: "lazy" });
  state.fire("error");
  assert.equal(state.image.hidden, true);
  assert.equal(state.fallback.hidden, false);
});
