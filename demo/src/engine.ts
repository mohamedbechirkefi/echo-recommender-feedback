// SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
// Browser port of the ECHO session loop (src/echo/simulate.py, policies.py,
// choice.py, preferences.py, vectors.py, metrics.py). Simulation only.
//
// Faithfulness: given the same random inputs (catalogue, initial tastes,
// policy keys, exploration flags and choice uniforms), this port reproduces
// the Python engine's slates and choices exactly and its preferences and
// metrics within 1e-9 (engine.test.ts, fixture from
// scripts/m5_exploratory_engine_traces.py). The sandbox draws those random
// inputs from its own generator (mulberry32 with Box-Muller normals), not
// from NumPy's PCG64, so a sandbox seed does not reproduce any research seed.

export type Policy = "RAND" | "POP" | "SIM" | "MMR" | "EXPLORE";
export type UpdateRule = "consumed" | "exposure" | "bounded";
export const POLICIES: Policy[] = ["RAND", "POP", "SIM", "MMR", "EXPLORE"];
export const UPDATE_RULES: UpdateRule[] = ["consumed", "exposure", "bounded"];

export interface Params {
  nTracks: number;
  dim: number;
  nClusters: number;
  nUsers: number;
  nSteps: number;
  slateSize: number;
  tau: number;
  warmupSteps: number;
  mmrLambda: number;
  exploreEpsilon: number;
  boundedThreshold: number;
  skipUtility: number;
}

export interface Arm {
  policy: Policy;
  preferenceModel: "fixed" | "adaptive";
  updateRule: UpdateRule;
  eta: number;
  profile: "estimated" | "oracle";
}

export interface Catalogue {
  emb: Float64Array; // N x d, unit rows
  cluster: Int32Array; // N
  basePop: Float64Array; // N
}

/** The engine's four random streams; calls arrive in step order. */
export interface RandomSource {
  keys(t: number): Float64Array; // U x N
  flags(t: number): Float64Array; // U x k
  choiceU(t: number): Float64Array; // U
}

export interface Metrics {
  drift_rad: number;
  homogenisation: number;
  discovery: number;
  novelty_bits: number;
  diversity_ild: number;
  relevance_initial: number;
  relevance_current: number;
  exposure_gini: number;
  skip_rate: number;
  drift_per_accept_rad: number;
}

export interface SessionOut {
  slates: Int32Array[]; // per step, U x k
  choices: Int32Array[]; // per step, U (track index or -1 for a skip)
  finalPrefs: Float64Array; // U x d
  driftRad: Float64Array; // U
  metrics: Metrics;
  /** Preference path (T + 1 entries of U x d) when requested. */
  path: Float64Array[] | null;
}

export class EngineError extends Error {}

export function validateParams(p: Params, arm: Arm): void {
  const int = (v: number, lo: number, name: string) => {
    if (!Number.isInteger(v) || v < lo) throw new EngineError(`${name} must be an integer >= ${lo}`);
  };
  int(p.nTracks, 2, "nTracks");
  int(p.dim, 2, "dim");
  int(p.nClusters, 1, "nClusters");
  int(p.nUsers, 2, "nUsers");
  int(p.nSteps, 1, "nSteps");
  int(p.slateSize, 2, "slateSize");
  int(p.warmupSteps, 0, "warmupSteps");
  if (!(p.tau > 0)) throw new EngineError("tau must be > 0");
  if (!(arm.eta >= 0 && arm.eta <= 1)) throw new EngineError("eta must lie in [0, 1]");
  if (!(p.exploreEpsilon >= 0 && p.exploreEpsilon <= 1)) throw new EngineError("epsilon must lie in [0, 1]");
  if (!(p.mmrLambda > 0 && p.mmrLambda <= 1)) throw new EngineError("mmr lambda must lie in (0, 1]");
  if ((arm.preferenceModel === "fixed") !== (arm.eta === 0)) throw new EngineError("fixed preferences need eta 0");
  if (p.nSteps > p.nTracks - p.slateSize) throw new EngineError("the candidate pool could be exhausted");
}

function dot(a: Float64Array, ai: number, b: Float64Array, bi: number, d: number): number {
  let s = 0;
  for (let j = 0; j < d; j++) s += a[ai + j] * b[bi + j];
  return s;
}

function normaliseInto(v: Float64Array, d: number, out: Float64Array, oi: number): void {
  let s = 0;
  for (let j = 0; j < d; j++) s += v[j] * v[j];
  const n = Math.sqrt(s);
  if (!(n >= 1e-12) || !Number.isFinite(n)) throw new EngineError("cannot normalise a zero-norm or non-finite vector");
  for (let j = 0; j < d; j++) out[oi + j] = v[j] / n;
}

/** Indices of the k highest scores among non-excluded entries; ties go to the lower index. */
export function topK(scores: Float64Array, excluded: Uint8Array, k: number): number[] {
  const idx: number[] = [];
  for (let i = 0; i < scores.length; i++) if (!excluded[i]) idx.push(i);
  if (idx.length < k) throw new EngineError("candidate pool smaller than the slate size");
  idx.sort((a, b) => (scores[b] - scores[a]) || a - b);
  return idx.slice(0, k);
}

/** RAND: the k smallest random keys among non-excluded entries. */
export function randSlate(keys: Float64Array, excluded: Uint8Array, k: number): number[] {
  const idx: number[] = [];
  for (let i = 0; i < keys.length; i++) if (!excluded[i]) idx.push(i);
  if (idx.length < k) throw new EngineError("candidate pool smaller than the slate size");
  idx.sort((a, b) => (keys[a] - keys[b]) || a - b);
  return idx.slice(0, k);
}

function mmrSlate(rel: Float64Array, X: Float64Array, d: number, excluded: Uint8Array, k: number, lam: number): number[] {
  const n = rel.length;
  const blocked = excluded.slice();
  const maxsim = new Float64Array(n);
  const out: number[] = [];
  for (let j = 0; j < k; j++) {
    let best = -1;
    let bestScore = -Infinity;
    for (let i = 0; i < n; i++) {
      if (blocked[i]) continue;
      const s = j === 0 ? rel[i] : lam * rel[i] - (1.0 - lam) * maxsim[i];
      if (best < 0 || s > bestScore) {
        best = i;
        bestScore = s;
      }
    }
    if (best < 0) throw new EngineError("candidate pool smaller than the slate size");
    out.push(best);
    blocked[best] = 1;
    for (let i = 0; i < n; i++) {
      const s = dot(X, best * d, X, i * d, d);
      maxsim[i] = j === 0 ? s : Math.max(maxsim[i], s);
    }
  }
  return out;
}

function exploreSlate(simOrder: number[], rndOrder: number[], flags: Float64Array, fi: number, k: number, eps: number): number[] {
  const used = new Set<number>();
  const pos = { r: 0, s: 0 };
  const out: number[] = [];
  for (let j = 0; j < k; j++) {
    const isRand = flags[fi + j] < eps;
    const next = () => {
      const v = isRand ? rndOrder[pos.r++] : simOrder[pos.s++];
      if (v === undefined) throw new EngineError("exploration order exhausted");
      return v;
    };
    let item = next();
    while (used.has(item)) item = next();
    used.add(item);
    out.push(item);
  }
  return out;
}

/** Angle 2 asin(||a_hat - b_hat|| / 2) between two rows (vectors.angle). */
function angleRows(A: Float64Array, ai: number, B: Float64Array, bi: number, d: number): number {
  const ua = new Float64Array(d);
  const ub = new Float64Array(d);
  normaliseInto(A.subarray(ai, ai + d), d, ua, 0);
  normaliseInto(B.subarray(bi, bi + d), d, ub, 0);
  let s = 0;
  for (let j = 0; j < d; j++) s += (ua[j] - ub[j]) ** 2;
  const c = Math.sqrt(s) / 2;
  return 2 * Math.asin(Math.min(1, Math.max(0, c)));
}

function meanPairwiseCosine(P: Float64Array, U: number, d: number): number {
  const u = new Float64Array(U * d);
  for (let i = 0; i < U; i++) normaliseInto(P.subarray(i * d, i * d + d), d, u, i * d);
  let total = 0;
  let trace = 0;
  for (let a = 0; a < U; a++) {
    for (let b = 0; b < U; b++) {
      const g = dot(u, a * d, u, b * d, d);
      total += g;
      if (a === b) trace += g;
    }
  }
  return (total - trace) / (U * (U - 1));
}

export function gini(values: ArrayLike<number>): number {
  const x = Array.from(values).sort((a, b) => a - b);
  const n = x.length;
  let total = 0;
  let w = 0;
  for (let i = 0; i < n; i++) {
    total += x[i];
    w += (i + 1) * x[i];
  }
  if (n === 0 || total === 0) throw new EngineError("gini undefined");
  return (2.0 * w) / (n * total) - (n + 1.0) / n;
}

export interface Hooks {
  recordPath?: boolean;
  /** Called after each step; return false to stop (cancellation). */
  onStep?: (t: number) => boolean;
}

/** Runs a session synchronously; returns null if hooks.onStep asked to stop. */
export function runSession(p: Params, arm: Arm, cat: Catalogue, initial: Float64Array, rnd: RandomSource, hooks: Hooks = {}): SessionOut | null {
  const it = session(p, arm, cat, initial, rnd, hooks.recordPath ?? false);
  for (;;) {
    const r = it.next();
    if (r.done) return r.value;
    if (hooks.onStep && hooks.onStep(r.value) === false) return null;
  }
}

/** The session loop as a generator: yields after each step so a caller can pause or cancel. */
export function* session(p: Params, arm: Arm, cat: Catalogue, initial: Float64Array, rnd: RandomSource, recordPath = false): Generator<number, SessionOut, void> {
  validateParams(p, arm);
  const { nUsers: U, nTracks: N, dim: d, nClusters: K, slateSize: k, nSteps: T } = p;
  const X = cat.emb;
  let popSum = 0;
  for (let i = 0; i < N; i++) popSum += cat.basePop[i];
  const selfInfo = new Float64Array(N);
  for (let i = 0; i < N; i++) selfInfo[i] = -Math.log2(cat.basePop[i] / popSum);

  let P = initial.slice();
  const consumed: Uint8Array[] = Array.from({ length: U }, () => new Uint8Array(N));
  const consumedSum = new Float64Array(U * d);
  const accepted = new Int32Array(U);
  const skips = new Int32Array(U);
  const clustersSeen: Uint8Array[] = Array.from({ length: U }, () => new Uint8Array(K));
  const noveltySum = new Float64Array(U);
  const rel0 = new Float64Array(U);
  const relt = new Float64Array(U);
  let ildSum = 0;
  const impressions = new Float64Array(N);
  const counts = new Float64Array(N);
  const slates: Int32Array[] = [];
  const choices: Int32Array[] = [];
  const path: Float64Array[] | null = recordPath ? [P.slice()] : null;
  const personalised = arm.policy === "SIM" || arm.policy === "MMR" || arm.policy === "EXPLORE";

  for (let t = 0; t < T; t++) {
    const keys = rnd.keys(t);
    const flags = rnd.flags(t);
    const cu = rnd.choiceU(t);
    const slate: number[][] = [];
    for (let u = 0; u < U; u++) slate.push(randSlate(keys.subarray(u * N, u * N + N), consumed[u], k));
    if (arm.policy === "POP") {
      const pop = new Float64Array(N);
      for (let i = 0; i < N; i++) pop[i] = counts[i] + cat.basePop[i];
      for (let u = 0; u < U; u++) slate[u] = topK(pop, consumed[u], k);
    } else if (personalised) {
      const prof = new Float64Array(U * d);
      const use: number[] = [];
      for (let u = 0; u < U; u++) {
        let valid = true;
        if (arm.profile === "oracle") {
          prof.set(P.subarray(u * d, u * d + d), u * d);
        } else {
          let s = 0;
          for (let j = 0; j < d; j++) s += consumedSum[u * d + j] ** 2;
          const nrm = Math.sqrt(s);
          valid = accepted[u] > 0 && nrm > 1e-12;
          if (valid) for (let j = 0; j < d; j++) prof[u * d + j] = consumedSum[u * d + j] / nrm;
        }
        if (valid && t >= p.warmupSteps) use.push(u);
      }
      let depth = 2 * k;
      if (arm.policy === "EXPLORE") {
        for (const u of use) {
          let pool = 0;
          for (let i = 0; i < N; i++) if (!consumed[u][i]) pool++;
          depth = Math.min(depth, pool);
        }
      }
      for (const u of use) {
        const rel = new Float64Array(N);
        for (let i = 0; i < N; i++) rel[i] = dot(prof, u * d, X, i * d, d);
        if (arm.policy === "SIM") slate[u] = topK(rel, consumed[u], k);
        else if (arm.policy === "MMR") slate[u] = mmrSlate(rel, X, d, consumed[u], k, p.mmrLambda);
        else {
          const simOrder = topK(rel, consumed[u], depth);
          const rndOrder = randSlate(keys.subarray(u * N, u * N + N), consumed[u], depth);
          slate[u] = exploreSlate(simOrder, rndOrder, flags, u * k, k, p.exploreEpsilon);
        }
      }
    }

    const slateOut = new Int32Array(U * k);
    const choiceOut = new Int32Array(U);
    const chosenEmb = new Float64Array(U * d);
    const slateMean = new Float64Array(U * d);
    const acc = new Uint8Array(U);
    for (let u = 0; u < U; u++) {
      const s = slate[u];
      for (let j = 0; j < k; j++) {
        if (consumed[u][s[j]]) throw new EngineError("candidate exclusion violated");
        slateOut[u * k + j] = s[j];
        impressions[s[j]] += 1;
      }
      let ild = 0;
      let pairs = 0;
      for (let a = 0; a < k; a++) {
        for (let b = a + 1; b < k; b++) {
          ild += 1.0 - dot(X, s[a] * d, X, s[b] * d, d);
          pairs++;
        }
      }
      ildSum += ild / pairs;
      for (let j = 0; j < d; j++) {
        let m = 0;
        for (let a = 0; a < k; a++) m += X[s[a] * d + j];
        slateMean[u * d + j] = m / k;
      }
      // Choice: softmax over cos / tau plus a skip option; inverse-CDF sampling.
      const logits = new Float64Array(k + 1);
      for (let j = 0; j < k; j++) logits[j] = dot(P, u * d, X, s[j] * d, d) / p.tau;
      logits[k] = p.skipUtility / p.tau;
      let mx = -Infinity;
      for (const l of logits) mx = Math.max(mx, l);
      let z = 0;
      const e = new Float64Array(k + 1);
      for (let j = 0; j <= k; j++) {
        e[j] = Math.exp(logits[j] - mx);
        z += e[j];
      }
      let cum = 0;
      let pick = 0;
      for (let j = 0; j <= k; j++) {
        cum = j === k ? 1.0 : cum + e[j] / z;
        if (cum <= cu[u]) pick++;
      }
      const ok = pick < k;
      acc[u] = ok ? 1 : 0;
      if (ok) {
        const item = s[pick];
        choiceOut[u] = item;
        for (let j = 0; j < d; j++) chosenEmb[u * d + j] = X[item * d + j];
        let r0 = 0;
        let rt = 0;
        for (let j = 0; j < d; j++) {
          r0 += initial[u * d + j] * X[item * d + j];
          rt += P[u * d + j] * X[item * d + j];
        }
        rel0[u] += r0;
        relt[u] += rt;
        noveltySum[u] += selfInfo[item];
        clustersSeen[u][cat.cluster[item]] = 1;
        consumed[u][item] = 1;
        for (let j = 0; j < d; j++) consumedSum[u * d + j] += X[item * d + j];
        accepted[u] += 1;
      } else {
        choiceOut[u] = -1;
        skips[u] += 1;
      }
    }
    for (let u = 0; u < U; u++) if (acc[u]) counts[choiceOut[u]] += 1;

    if (arm.preferenceModel === "adaptive" && arm.eta > 0) {
      const next = P.slice();
      const tmp = new Float64Array(d);
      for (let u = 0; u < U; u++) {
        let on: boolean;
        let target: Float64Array;
        if (arm.updateRule === "consumed") {
          on = acc[u] === 1;
          target = chosenEmb;
        } else if (arm.updateRule === "exposure") {
          on = true;
          target = slateMean;
        } else {
          on = acc[u] === 1 && dot(P, u * d, chosenEmb, u * d, d) > p.boundedThreshold;
          target = chosenEmb;
        }
        if (!on) continue;
        for (let j = 0; j < d; j++) tmp[j] = (1.0 - arm.eta) * P[u * d + j] + arm.eta * target[u * d + j];
        normaliseInto(tmp, d, next, u * d);
      }
      P = next;
    }
    for (const v of P) if (!Number.isFinite(v)) throw new EngineError(`non-finite preference at step ${t}`);
    slates.push(slateOut);
    choices.push(choiceOut);
    if (path) path.push(P.slice());
    yield t;
  }

  const drift = new Float64Array(U);
  for (let u = 0; u < U; u++) drift[u] = angleRows(initial, u * d, P, u * d, d);
  let nHas = 0;
  const overAccepting = (num: Float64Array) => {
    let s = 0;
    nHas = 0;
    for (let u = 0; u < U; u++) {
      if (accepted[u] > 0) {
        s += num[u] / accepted[u];
        nHas++;
      }
    }
    return nHas === 0 ? NaN : s / nHas;
  };
  const mean = (a: ArrayLike<number>) => {
    let s = 0;
    for (let i = 0; i < a.length; i++) s += a[i];
    return s / a.length;
  };
  let seen = 0;
  for (let u = 0; u < U; u++) for (let c = 0; c < K; c++) seen += clustersSeen[u][c];
  const metrics: Metrics = {
    drift_rad: mean(drift),
    homogenisation: meanPairwiseCosine(P, U, d) - meanPairwiseCosine(initial, U, d),
    discovery: seen / U / K,
    novelty_bits: overAccepting(noveltySum),
    diversity_ild: ildSum / (U * T),
    relevance_initial: overAccepting(rel0),
    relevance_current: overAccepting(relt),
    exposure_gini: gini(impressions),
    skip_rate: mean(skips) / T,
    drift_per_accept_rad: overAccepting(drift),
  };
  return { slates, choices, finalPrefs: P, driftRad: drift, metrics, path };
}

// ---------------------------------------------------------------------------
// Sandbox random inputs (not NumPy's generator; see the header).

export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function normalGen(rng: () => number): () => number {
  let spare: number | null = null;
  return () => {
    if (spare !== null) {
      const s = spare;
      spare = null;
      return s;
    }
    let u = 0;
    while (u === 0) u = rng();
    const v = rng();
    const r = Math.sqrt(-2 * Math.log(u));
    spare = r * Math.sin(2 * Math.PI * v);
    return r * Math.cos(2 * Math.PI * v);
  };
}

/** FMA-fitted cluster weights and Zipf exponent of experiments/EXP-002/config.json (frozen). */
export const CALIBRATED_WEIGHTS = [
  0.02814, 0.002203, 0.011566, 0.026763, 0.011141, 0.003956, 0.04544, 0.285256, 0.000376, 0.002804, 0.191823,
  0.056956, 0.00696, 0.072854, 0.21423, 0.039531,
];
export const CALIBRATED_ZIPF_S = 1.3065;

/** Seeds for the four streams, derived from one sandbox seed. */
function streamSeed(seed: number, stream: number): number {
  return (Math.imul(seed >>> 0, 0x9e3779b1) ^ Math.imul(stream + 1, 0x85ebca6b)) >>> 0;
}

/** Synthetic calibrated catalogue and listeners as in catalogue.py, drawn with the sandbox generator. */
export function sandboxWorld(seed: number, p: Params, spread = 0.1, weights = CALIBRATED_WEIGHTS, zipfS = CALIBRATED_ZIPF_S) {
  const { nTracks: N, dim: d, nClusters: K, nUsers: U } = p;
  if (weights.length !== K) throw new EngineError("cluster weights do not match nClusters");
  const rngC = mulberry32(streamSeed(seed, 0));
  const nC = normalGen(rngC);
  const centres = new Float64Array(K * d);
  const tmp = new Float64Array(d);
  for (let c = 0; c < K; c++) {
    for (let j = 0; j < d; j++) tmp[j] = nC();
    normaliseInto(tmp, d, centres, c * d);
  }
  const wsum = weights.reduce((a, b) => a + b, 0);
  const cluster = new Int32Array(N);
  const emb = new Float64Array(N * d);
  for (let i = 0; i < N; i++) {
    let r = rngC() * wsum;
    let c = 0;
    while (c < K - 1 && r >= weights[c]) {
      r -= weights[c];
      c++;
    }
    cluster[i] = c;
    for (let j = 0; j < d; j++) tmp[j] = centres[c * d + j] + spread * nC();
    normaliseInto(tmp, d, emb, i * d);
  }
  const ranks = Array.from({ length: N }, (_, i) => i + 1);
  for (let i = N - 1; i > 0; i--) {
    const j = Math.floor(rngC() * (i + 1));
    [ranks[i], ranks[j]] = [ranks[j], ranks[i]];
  }
  const raw = ranks.map((r) => r ** -zipfS);
  const rs = raw.reduce((a, b) => a + b, 0);
  const basePop = Float64Array.from(raw, (w) => (w * N) / rs);

  const rngL = mulberry32(streamSeed(seed, 1));
  const nL = normalGen(rngL);
  const initial = new Float64Array(U * d);
  for (let u = 0; u < U; u++) {
    const home = Math.floor(rngL() * K);
    for (let j = 0; j < d; j++) tmp[j] = centres[home * d + j] + spread * nL();
    normaliseInto(tmp, d, initial, u * d);
  }
  return { catalogue: { emb, cluster, basePop } as Catalogue, initial };
}

/** Policy and choice streams; a fresh source with the same seed repeats them (common random numbers). */
export function sandboxRandom(seed: number, p: Params): RandomSource {
  const rp = mulberry32(streamSeed(seed, 3));
  const rc = mulberry32(streamSeed(seed, 2));
  const { nUsers: U, nTracks: N, slateSize: k } = p;
  return {
    keys: () => Float64Array.from({ length: U * N }, rp),
    flags: () => Float64Array.from({ length: U * k }, rp),
    choiceU: () => Float64Array.from({ length: U }, rc),
  };
}

/** First two principal axes of the rows (power iteration; largest loading positive). */
export function pca2(X: Float64Array, n: number, d: number): { mu: Float64Array; axes: Float64Array[] } {
  const mu = new Float64Array(d);
  for (let i = 0; i < n; i++) for (let j = 0; j < d; j++) mu[j] += X[i * d + j] / n;
  const C = new Float64Array(d * d);
  for (let i = 0; i < n; i++) {
    for (let a = 0; a < d; a++) {
      const xa = X[i * d + a] - mu[a];
      for (let b = 0; b < d; b++) C[a * d + b] += xa * (X[i * d + b] - mu[b]);
    }
  }
  const axes: Float64Array[] = [];
  for (let c = 0; c < 2; c++) {
    let v = Float64Array.from({ length: d }, (_, j) => 1 / Math.sqrt(d) + j * 1e-3);
    for (let it = 0; it < 500; it++) {
      const w = new Float64Array(d);
      for (let a = 0; a < d; a++) for (let b = 0; b < d; b++) w[a] += C[a * d + b] * v[b];
      for (const prev of axes) {
        let s = 0;
        for (let j = 0; j < d; j++) s += w[j] * prev[j];
        for (let j = 0; j < d; j++) w[j] -= s * prev[j];
      }
      let nrm = 0;
      for (const x of w) nrm += x * x;
      nrm = Math.sqrt(nrm);
      if (!(nrm > 0)) break;
      v = w.map((x) => x / nrm);
    }
    let big = 0;
    for (let j = 1; j < d; j++) if (Math.abs(v[j]) > Math.abs(v[big])) big = j;
    if (v[big] < 0) v = v.map((x) => -x);
    axes.push(v);
  }
  return { mu, axes };
}

export function project(row: Float64Array, ri: number, d: number, pc: { mu: Float64Array; axes: Float64Array[] }): [number, number] {
  const out: [number, number] = [0, 0];
  for (let c = 0; c < 2; c++) {
    let s = 0;
    for (let j = 0; j < d; j++) s += (row[ri + j] - pc.mu[j]) * pc.axes[c][j];
    out[c] = s;
  }
  return out;
}
