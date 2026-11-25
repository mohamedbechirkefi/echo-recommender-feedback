// SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { ResultsError, validateResults } from "./results";

const good = () => JSON.parse(readFileSync("public/data/results.json", "utf8"));

describe("validateResults", () => {
  it("accepts the exported results file", () => {
    expect(validateResults(good()).experiments.length).toBeGreaterThan(0);
  });
  it("rejects a wrong schema name", () => {
    expect(() => validateResults({ ...good(), schema: "other" })).toThrow(ResultsError);
  });
  it("rejects an unsupported major version", () => {
    expect(() => validateResults({ ...good(), schema_version: "2.0.0" })).toThrow(ResultsError);
  });
  it("rejects a missing estimate", () => {
    const r = good();
    delete r.experiments[0].estimates?.[0]?.estimate;
    if (r.experiments[0].estimates.length === 0) r.experiments[0].title = 7;
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a non-finite number", () => {
    const r = good();
    r.experiments[0].estimates = [{ label: "x", estimate: "NaN", ci_low: null, ci_high: null, ci_level: null, unit: "" }];
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a half-open interval", () => {
    const r = good();
    r.experiments[0].estimates = [{ label: "x", estimate: 1, ci_low: 0, ci_high: null, ci_level: 0.95, unit: "" }];
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a malformed source hash", () => {
    expect(() => validateResults({ ...good(), sources: [{ path: "a", sha256: "zz" }] })).toThrow(ResultsError);
  });
  // ECHO extensions fail closed too.
  it("rejects a missing taste map", () => {
    const r = good();
    delete r.taste_map;
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a taste-map path with a non-number", () => {
    const r = good();
    r.taste_map.policies.SIM.listeners[0].path[3] = [0, "x"];
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a taste map not labelled exploratory", () => {
    const r = good();
    r.taste_map.label = "published result";
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a contrast chart with a dropped row", () => {
    const r = good();
    r.contrast_chart.pop();
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects an unknown display source", () => {
    const r = good();
    r.experiments[1].estimates[0].display_source = "elsewhere";
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects an estimate without its manuscript text", () => {
    const r = good();
    r.experiments[1].estimates[0].display = null;
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects arm rows out of policy order", () => {
    const r = good();
    r.arm_drift["EXP-004"].reverse();
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("keeps every registered experiment, including the exploratory one", () => {
    const ids = validateResults(good()).experiments.map((e) => e.id);
    expect(ids).toEqual(["EXP-001", "EXP-002", "EXP-003", "EXP-004"]);
  });
});
