// SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
// The browser port against the Python research engine. Fixture:
// src/fixtures/engine_fixture.json, written by
// scripts/m5_exploratory_engine_traces.py (exploratory, seed 950000).
// Tolerance: slates and choices identical; preferences, per-listener drift and
// every metric within 1e-9 absolute.
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import {
  CALIBRATED_WEIGHTS,
  CALIBRATED_ZIPF_S,
  POLICIES,
  runSession,
  sandboxRandom,
  sandboxWorld,
  type Arm,
  type Params,
  type RandomSource,
} from "./engine";

const TOL = 1e-9;
const fx = JSON.parse(readFileSync("src/fixtures/engine_fixture.json", "utf8"));
const flat = (a: unknown): number[] => (Array.isArray(a) ? a.flatMap(flat) : [a as number]);

const params: Params = {
  nTracks: fx.params.n_tracks,
  dim: fx.params.dim,
  nClusters: fx.params.n_clusters,
  nUsers: fx.params.n_users,
  nSteps: fx.params.n_steps,
  slateSize: fx.params.slate_size,
  tau: fx.params.tau,
  warmupSteps: fx.params.warmup_steps,
  mmrLambda: fx.params.mmr_lambda,
  exploreEpsilon: fx.params.explore_epsilon,
  boundedThreshold: fx.params.bounded_threshold,
  skipUtility: fx.params.skip_utility,
};
const catalogue = {
  emb: Float64Array.from(flat(fx.catalogue.embeddings)),
  cluster: Int32Array.from(fx.catalogue.cluster),
  basePop: Float64Array.from(fx.catalogue.base_pop),
};
const initial = Float64Array.from(flat(fx.initial_prefs));
const fixtureRandom = (): RandomSource => ({
  keys: (t) => Float64Array.from(flat(fx.keys[t])),
  flags: (t) => Float64Array.from(flat(fx.flags[t])),
  choiceU: (t) => Float64Array.from(fx.choice_u[t]),
});

describe("engine port reproduces the Python engine on the fixture", () => {
  it("covers nine arms", () => expect(fx.runs.length).toBe(9));
  for (const run of fx.runs) {
    const a = run.arm;
    const arm: Arm = { policy: a.policy, preferenceModel: a.preference_model, updateRule: a.update_rule, eta: a.eta, profile: a.profile };
    it(`${a.policy} / ${a.preference_model} / ${a.update_rule} / eta ${a.eta} / ${a.profile}`, () => {
      const out = runSession(params, arm, catalogue, initial, fixtureRandom())!;
      expect(out.slates.map((s) => Array.from(s))).toEqual(run.slates.map((s: number[][]) => s.flat()));
      expect(out.choices.map((c) => Array.from(c))).toEqual(run.choices);
      const fp = flat(run.final_prefs);
      fp.forEach((v, i) => expect(Math.abs(out.finalPrefs[i] - v)).toBeLessThan(TOL));
      run.drift_rad.forEach((v: number, i: number) => expect(Math.abs(out.driftRad[i] - v)).toBeLessThan(TOL));
      for (const [name, v] of Object.entries(run.metrics as Record<string, number>)) {
        expect(Math.abs((out.metrics as unknown as Record<string, number>)[name] - v), name).toBeLessThan(TOL);
      }
    });
  }
});

describe("sandbox world", () => {
  const p: Params = { ...params, nTracks: 120, nClusters: 16, nUsers: 8, nSteps: 30, slateSize: 10 };
  it("is deterministic for a seed and uses the frozen calibration", () => {
    const w1 = sandboxWorld(3, p);
    const w2 = sandboxWorld(3, p);
    expect(Array.from(w1.catalogue.emb)).toEqual(Array.from(w2.catalogue.emb));
    expect(CALIBRATED_WEIGHTS.length).toBe(16);
    expect(CALIBRATED_ZIPF_S).toBe(1.3065);
    const results = JSON.parse(readFileSync("public/data/results.json", "utf8"));
    expect(results.taste_map.config.cluster_weights).toEqual(CALIBRATED_WEIGHTS);
    expect(results.taste_map.config.zipf_s).toBe(CALIBRATED_ZIPF_S);
  });
  it("keeps drift exactly 0 under fixed preferences for every policy (negative control)", () => {
    const w = sandboxWorld(5, p);
    for (const policy of POLICIES) {
      const out = runSession(p, { policy, preferenceModel: "fixed", updateRule: "consumed", eta: 0, profile: "estimated" }, w.catalogue, w.initial, sandboxRandom(5, p))!;
      expect(out.metrics.drift_rad).toBe(0);
    }
  });
  it("stops when the step hook asks (cancellation)", () => {
    const w = sandboxWorld(5, p);
    const out = runSession(p, { policy: "SIM", preferenceModel: "adaptive", updateRule: "consumed", eta: 0.05, profile: "estimated" }, w.catalogue, w.initial, sandboxRandom(5, p), { onStep: (t) => t < 3 });
    expect(out).toBeNull();
  });
  it("rejects invalid parameters", () => {
    const w = sandboxWorld(5, p);
    expect(() => runSession({ ...p, nSteps: 200 }, { policy: "RAND", preferenceModel: "adaptive", updateRule: "consumed", eta: 0.05, profile: "estimated" }, w.catalogue, w.initial, sandboxRandom(5, p))).toThrow();
    expect(() => runSession(p, { policy: "RAND", preferenceModel: "adaptive", updateRule: "consumed", eta: 2, profile: "estimated" }, w.catalogue, w.initial, sandboxRandom(5, p))).toThrow();
  });
});
