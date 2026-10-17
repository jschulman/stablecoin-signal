const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {summarize} = require('../docs/rails.js');
const data = JSON.parse(fs.readFileSync(new URL('../data/rails/evidence.json', `file://${__filename}`)));

test('static source works without generated runtime with explicit coverage counts', () => {
  const result = summarize(data, '2026-11-17');
  assert.equal(result.stage_counts['limited-production'], 3);
  assert.equal(result.stage_counts['recurring-production'], 0);
  assert.equal(result.category_counts['payment-settlement'], 1);
  assert.equal(result.category_counts['securities-collateral'], 1);
  assert.equal(result.overdue_reviews, 3);
  assert.equal(result.records[0].review_due, '2026-11-16');
  assert.equal(result.records[0].volume.value, null);
});

test('static renderer rejects unsupported production claims', () => {
  const changed = structuredClone(data);
  changed.records[0].stage = 'recurring-production';
  assert.throws(() => summarize(changed, '2026-09-25'), /Unsupported recurring/);
});

test('review overdue boundary and paused stage are not promoted by time', () => {
  assert.equal(summarize(data, '2026-11-16').overdue_reviews, 0);
  assert.equal(summarize(data, '2026-11-17').overdue_reviews, 3);
  const changed = structuredClone(data);
  changed.records[0].stage = 'paused';
  assert.equal(summarize(changed, '2030-01-01').stage_counts.paused, 1);
});
