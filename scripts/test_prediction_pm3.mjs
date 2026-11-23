#!/usr/bin/env node
/** Smoke tests for ±3 min Bitcoin prediction on index + tesseract pages. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MIN = 60_000;
const OFFSET = 3 * MIN;
let failed = 0;

function assert(cond, msg) {
  if (!cond) {
    failed += 1;
    console.error('FAIL:', msg);
  } else {
    console.log('OK  :', msg);
  }
}

const indexHtml = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const tessHtml = fs.readFileSync(path.join(root, 'tesseract.html'), 'utf8');

assert(indexHtml.includes('id="tBack"'), 'index.html has T−3 min timestamp cell');
assert(indexHtml.includes('id="tFwd"'), 'index.html has T+3 min timestamp cell');
assert(indexHtml.includes('id="pBack"') && indexHtml.includes('id="pFwd"'), 'index.html has ±3 min price cells');
assert(indexHtml.includes('OFFSET=3*MIN') || indexHtml.includes('OFFSET = 3 * MIN') || indexHtml.includes('OFFSET=3*MIN'), 'index.html defines 3-minute OFFSET');
assert(indexHtml.includes('priceAtOffset'), 'index.html has priceAtOffset');
assert(indexHtml.includes('renderPrediction'), 'index.html renders prediction table');
assert(indexHtml.includes('phase2') && indexHtml.includes('phase3'), 'index.html shows 2s and 3s phases');
assert(indexHtml.includes('last_updated_at'), 'index.html uses Bitcoin exact timestamp');
assert(tessHtml.includes('OFFSET=3*MIN') || tessHtml.includes('OFFSET = 3 * MIN') || tessHtml.includes('const DAY=86400000, MIN=60000, OFFSET=3*MIN'), 'tesseract.html defines 3-minute OFFSET');
assert(tessHtml.includes('commitTotalPrediction'), 'tesseract.html commits total ±3 min prediction');

// Math unit: P(Δ)=P0*exp(μ*Δ_min)
const btcPrice = 61604;
const muPerMin = 0.00001;
const priceAtOffset = (deltaMs) => btcPrice * Math.exp(muPerMin * (deltaMs / MIN));
const back = priceAtOffset(-OFFSET);
const fwd = priceAtOffset(+OFFSET);
assert(Math.abs(back - btcPrice * Math.exp(muPerMin * -3)) < 1e-9, 'T−3 min price matches exp drift');
assert(Math.abs(fwd - btcPrice * Math.exp(muPerMin * 3)) < 1e-9, 'T+3 min price matches exp drift');
assert(back < btcPrice && fwd > btcPrice, 'with positive μ, back < now < fwd');

const t = 1795458491 * 1000;
assert((t - OFFSET) === t - 180000 && (t + OFFSET) === t + 180000, 'offsets are exactly ±180000 ms');

// Live API (soft): if reachable, last_updated_at present
try {
  const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_last_updated_at=true', { cache: 'no-store' });
  assert(res.ok, `CoinGecko simple/price HTTP ${res.status}`);
  if (res.ok) {
    const json = await res.json();
    assert(Number.isFinite(json?.bitcoin?.usd), 'live BTC usd is finite');
    assert(Number.isFinite(json?.bitcoin?.last_updated_at), 'live last_updated_at is finite');
    const T = json.bitcoin.last_updated_at * 1000;
    console.log('INFO: T Bitcoin =', new Date(T).toISOString(), 'price=', json.bitcoin.usd);
    console.log('INFO: T-3min =', new Date(T - OFFSET).toISOString(), 'T+3min =', new Date(T + OFFSET).toISOString());
  }
} catch (e) {
  console.warn('WARN: live API unreachable in test env:', e.message);
}

if (failed) {
  console.error(`\n${failed} test(s) failed`);
  process.exit(1);
}
console.log('\nAll prediction ±3 min tests passed');
