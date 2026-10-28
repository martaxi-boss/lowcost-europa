'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { normalizeText, readPrice, comparePrices, withinBudget } = require(
  '../../apps/storefront/static/storefront/catalog-explorer.js'
);

test('search is accent-insensitive, case-insensitive and safe for empty input', () => {
  assert.equal(normalizeText('  Ácido HÍFU 7D '), 'acido hifu 7d');
  assert.equal(normalizeText(''), '');
  assert.equal(normalizeText(null), '');
});

test('only factual valid prices and currencies can be ordered', () => {
  assert.deepEqual(readPrice('399.90', 'EUR'), { amount: 399.9, currency: 'EUR' });
  assert.deepEqual(readPrice('19,90', 'eur'), { amount: 19.9, currency: 'EUR' });
  assert.equal(readPrice('', 'EUR'), null);
  assert.equal(readPrice('unknown', 'EUR'), null);
  assert.equal(readPrice('-3', 'EUR'), null);
  assert.equal(readPrice('5', ''), null);
  assert.equal(readPrice('Infinity', 'EUR'), null);
});

test('amount sort does not convert unrelated currencies or fabricate missing prices', () => {
  const eur = readPrice('70', 'EUR');
  const eur2 = readPrice('40', 'EUR');
  const usd = readPrice('10', 'USD');
  assert.equal(comparePrices(eur, eur2, 'asc'), 30);
  assert.equal(comparePrices(eur, eur2, 'desc'), -30);
  assert.ok(comparePrices(eur2, usd, 'asc') < 0);
  assert.ok(comparePrices(usd, eur, 'desc') > 0);
  assert.equal(comparePrices(null, eur, 'asc'), 1);
  assert.equal(comparePrices(eur, null, 'asc'), -1);
});

test('budget filter never guesses conversions or hides unknown price without request', () => {
  const eur = readPrice('499', 'EUR');
  const usd = readPrice('200', 'USD');
  assert.equal(withinBudget(eur, ''), true);
  assert.equal(withinBudget(eur, '500'), true);
  assert.equal(withinBudget(eur, '1000'), true);
  assert.equal(withinBudget(eur, '499'), true);
  assert.equal(withinBudget(eur, '200'), false);
  assert.equal(withinBudget(usd, '500'), false);
  assert.equal(withinBudget(null, '500'), false);
  assert.equal(withinBudget(null, 'unknown'), true);
  assert.equal(withinBudget(eur, 'unknown'), false);
  assert.equal(withinBudget(null, ''), true);
});
