// SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
import { useEffect, useRef, useState } from "react";
import { ArmDrift, ContrastForest, DriftCurves, TasteMapSvg } from "./charts";
import { fmtEstimate, fmtInterval, loadResults, ResultsError, TASTE_POLICIES, type Estimate, type Results } from "./results";
import { Sandbox } from "./Sandbox";
import { HeroRecord, NeedleDial } from "./Record";

type State = { kind: "loading" } | { kind: "error"; message: string } | { kind: "ready"; results: Results };

export function App() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    loadResults()
      .then((results) => setState({ kind: "ready", results }))
      .catch((e: unknown) =>
        setState({ kind: "error", message: e instanceof ResultsError ? e.message : "results could not be loaded" }),
      );
  }, []);

  return (
    <>
      <a className="skip" href="#main">Skip to content</a>
      <SiteNav />
      <main id="main">
        <header className="hero" id="top">
          <div className="wrap hero-grid">
            <div className="hero-text">
              <h1>Can recommendation policies change exposure and simulated taste rather than simply reflect it?</h1>
              <p className="answer">
                Within this model, the direction of simulated taste change is not a property of the policy alone; it
                depends on the update rule, the update rate and the catalogue geometry.
              </p>
              <p className="byline">
                Mohamed Bechir Kefi, independent researcher. A pre-registered simulation study of music
                recommendation; preprint draft, not peer-reviewed. Simulated preference change is not evidence of
                human persuasion.
              </p>
            </div>
            <HeroRecord />
          </div>
        </header>
        <div className="wrap">
          {state.kind === "loading" && <p role="status">Loading the published results.</p>}
          {state.kind === "error" && (
            <div role="alert" className="panel error">
              <h2>Results unavailable</h2>
              <p>The published results file failed validation, so no numbers are shown.</p>
              <p><code>{state.message}</code></p>
            </div>
          )}
          {state.kind === "ready" && <Published r={state.results} />}
          <Sandbox />
        </div>
      </main>
      <footer className="site">
        <div className="wrap foot-grid">
          <div className="foot-brand">
            <img src="brand/echo-lockup-reversed.svg" alt="ECHO" width="126" height="42" />
            <p>Mohamed Bechir Kefi, independent researcher. Licence: ECHO Source-Available Non-Commercial Research License v1.0.</p>
          </div>
          <ul className="foot-links" aria-label="Links">
            <li><a href="https://github.com/mohamedbechirkefi/echo-recommender-feedback">Repository on GitHub</a></li>
            <li><a href="https://github.com/mohamedbechirkefi/echo-recommender-feedback/blob/main/research/paper/manuscript.md">Manuscript (preprint draft)</a></li>
            <li><a href="https://labs.kefimohamedbechir.workers.dev">All labs</a></li>
          </ul>
          <div className="foot-notes">
            <p>
              Runs offline after the first load. No data about visitors is collected, stored or sent anywhere. Simulated
              preference change is not evidence of human persuasion. No audio is played or distributed; the record
              imagery is a visual metaphor.
            </p>
            <p>
              AI assistance: an AI system (Claude, Anthropic) assisted with research engineering, analysis code,
              drafting and this page as a disclosed research and development assistant. It is not an author.
            </p>
            <p>
              Typefaces: Bodoni Moda (Owen Earl) and Source Serif 4 (Frank Grie&szlig;hammer, Adobe), both under the SIL
              Open Font License 1.1, self-hosted. Motion stops when your system asks for reduced motion.
            </p>
          </div>
        </div>
      </footer>
    </>
  );
}

const NAV: [string, string][] = [
  ["key-result", "Key result"], ["overview", "Overview"], ["results", "Results"], ["taste-map", "Taste map"],
  ["assumptions", "Assumptions"], ["method", "Method and limitations"], ["sandbox", "Sandbox"],
];

function SiteNav() {
  const [active, setActive] = useState("");
  const [bar, setBar] = useState<{ x: number; w: number } | null>(null);
  const links = useRef<Record<string, HTMLAnchorElement | null>>({});
  useEffect(() => {
    if (typeof IntersectionObserver === "undefined") return;
    const vis = new Set<string>();
    const io = new IntersectionObserver((es) => {
      for (const e of es) { if (e.isIntersecting) vis.add(e.target.id); else vis.delete(e.target.id); }
      setActive(NAV.find(([id]) => vis.has(id))?.[0] ?? "");
    }, { rootMargin: "-30% 0px -60% 0px" });
    const watch = () => NAV.forEach(([id]) => { const el = document.getElementById(id); if (el) io.observe(el); });
    watch();
    const mo = new MutationObserver(watch);
    mo.observe(document.getElementById("main") ?? document.body, { childList: true, subtree: true });
    return () => { io.disconnect(); mo.disconnect(); };
  }, []);
  useEffect(() => {
    const a = links.current[active];
    setBar(a ? { x: a.offsetLeft, w: a.offsetWidth } : null);
  }, [active]);
  return (
    <header className="site">
      <div className="wrap navbar">
        <a className="brand" href="#top" aria-label="ECHO, back to the top">
          <img src="brand/echo-lockup.svg" alt="" width="96" height="32" />
        </a>
        <nav aria-label="Sections">
          <div className="navtrack">
            {NAV.map(([id, label]) => (
              <a key={id} href={`#${id}`} ref={(el) => { links.current[id] = el; }} aria-current={active === id ? "location" : undefined}>{label}</a>
            ))}
            <span className="nav-ind" aria-hidden="true" style={bar ? { transform: `translateX(${bar.x}px) scaleX(${bar.w / 100})`, opacity: 1 } : { opacity: 0 }} />
          </div>
        </nav>
      </div>
    </header>
  );
}

const byLabel = (r: Results, exp: string, start: string): Estimate => {
  const e = r.experiments.find((x) => x.id === exp)?.estimates.find((x) => x.label.startsWith(start));
  if (!e) throw new ResultsError(`${exp}: missing estimate "${start}"`);
  return e;
};
const pair = (e: Estimate) => `${fmtEstimate(e)} ${fmtInterval(e)}`;

function Published({ r }: { r: Results }) {
  const p2 = byLabel(r, "EXP-002", "SIM minus RAND drift (primary), 95");
  const p4 = byLabel(r, "EXP-004", "SIM minus RAND drift (primary, FMA), 95");
  const g2 = byLabel(r, "EXP-002", "SIM minus RAND exposure Gini");
  const g4 = byLabel(r, "EXP-004", "SIM minus RAND exposure Gini");
  const eq = byLabel(r, "EXP-003", "SIM minus RAND drift, bounded / 0.05 / estimated");
  const ex3 = r.experiments.find((x) => x.id === "EXP-003")!;
  const ex4 = r.experiments.find((x) => x.id === "EXP-004")!;
  return (
    <>
      <section id="key-result" aria-labelledby="h-key">
        <p className="tag tag-measured">Measured result</p>
        <h2 id="h-key">Taste as a needle angle</h2>
        <p>
          Drift is the angle between a listener's taste at the start and at the end of a session. Each record below
          draws the published mean drift of every policy as that angle, with its 95 % interval along the policy's own
          groove. On the synthetic catalogue SIM sits just short of RAND (SIM minus RAND {pair(p2)} rad); on the real
          FMA catalogue it sits beyond it ({pair(p4)} rad), the opposite sign.
        </p>
        <div className="dials">
          {(["EXP-002", "EXP-004"] as const).map((exp) => (
            <figure key={exp} className="dial-card">
              <figcaption className="dial-title">{exp === "EXP-002" ? "EXP-002, synthetic catalogue" : "EXP-004, real FMA catalogue"}</figcaption>
              <NeedleDial id={`dial-${exp}`} rows={r.arm_drift[exp]} title={exp === "EXP-002" ? "EXP-002, synthetic catalogue" : "EXP-004, real FMA catalogue"} />
              <ul className="dial-legend" aria-label={`${exp} policies, outer groove first`}>
                {r.arm_drift[exp].map((a) => (
                  <li key={a.policy}><span className={`key-swatch pol-${a.policy}`} aria-hidden="true" /> {a.policy} <span className="num">{a.display} {a.interval_display}</span></li>
                ))}
              </ul>
            </figure>
          ))}
        </div>
        <p className="note">
          Adaptive preferences, 10 seeds per policy, radians. Grooves run from RAND (outer) to EXPLORE (inner); the two
          needles are SIM and RAND. RAND itself moves simulated taste.
        </p>
      </section>

      <section id="overview" aria-labelledby="h-overview">
        <h2 id="h-overview">Overview</h2>
        <p className="status-label">{r.status_label}</p>
        <p className="lede">
          In a seeded simulation, listeners with adaptive preference vectors receive slates from five recommendation
          policies. The question is whether a personalised similarity policy (SIM) changes their end-of-session taste
          differently from uniform-random exposure (RAND), and whether it changes what they are exposed to.
        </p>
        <div className="cards">
          <div className="card">
            <p className="tag tag-measured">Measured result</p>
            <h3>Exposure changes</h3>
            <p>
              SIM concentrated exposure relative to RAND on both catalogues (exposure Gini difference {pair(g2)} synthetic,
              {" "}{pair(g4)} FMA). Descriptive, and largely expected for a personalised top-k policy.
            </p>
          </div>
          <div className="card">
            <p className="tag tag-measured">Measured result</p>
            <h3>Primary contrast: detectable</h3>
            <p>
              EXP-002: SIM minus RAND drift {pair(p2)} rad, so H0 was rejected; its practical size is unresolved.
            </p>
          </div>
          <div className="card">
            <p className="tag tag-measured">Measured result</p>
            <h3>Its direction does not hold</h3>
            <p>
              EXP-003 {ex3.verdict} (bounded rule at eta 0.05: {pair(eq)} rad). EXP-004 on real FMA tracks: {pair(p4)} rad,
              the opposite sign; {ex4.verdict.split("; ")[1]}.
            </p>
          </div>
        </div>
        <div className="panel legend-panel">
          <h3>How labels are used on this page</h3>
          <ul className="label-legend">
            <li><span className="tag tag-measured">Measured result</span> a number from the committed confirmatory runs, printed exactly as in the manuscript, with its interval.</li>
            <li><span className="tag tag-exploratory">Exploratory illustration</span> output of the Python research engine for an exploratory seed; it supports no claim.</li>
            <li><span className="tag tag-sandbox">Sandbox output</span> computed in your browser from your settings; never a research result.</li>
            <li><span className="tag tag-assumption">Assumption</span> a model parameter or judgement fixed in the frozen protocol, not a measurement.</li>
          </ul>
        </div>
        <div className="panel">
          <h3>Open items for the owner</h3>
          <ul>{r.owner_pending.map((x) => <li key={x}>{x}</li>)}</ul>
        </div>
      </section>

      <section id="results" aria-labelledby="h-results">
        <p className="tag tag-measured">Measured result</p>
        <h2 id="h-results">Published results</h2>
        <p className="note">
          These numbers come from the committed results at revision <code>{r.code_revision.slice(0, 7)}</code> (full
          hash <code>{r.code_revision}</code>). They are printed exactly as in the manuscript and are separate from
          anything the sandbox produces. Intervals are 95 % percentile bootstrap intervals over 10 seeds unless a row
          says otherwise.
        </p>
        <figure>
          <p className="scroll-hint">On a narrow screen, scroll the chart sideways to see the values column.</p>
          <div className="table-scroll" role="region" aria-label="Forest plot of SIM minus RAND drift contrasts" tabIndex={0}>
            <ContrastForest rows={r.contrast_chart} sesoi={r.sesoi_rad} />
          </div>
          <figcaption>
            <strong>Figure 1.</strong> SIM minus RAND difference in mean angular preference drift (radians, seed-paired,
            n = 10 seeds per row) with 95 % bootstrap intervals. The shaded band is the smallest effect size of interest,
            plus or minus {r.sesoi_rad} rad; diamonds mark the two cells that trigger the frozen withdrawal rule. In words:
            the primary contrast is negative on the synthetic catalogue, positive on the real catalogue, positive at eta
            0.01, and inside the band or positive under the bounded rule at eta 0.05. A "practically equivalent" cell is
            drawn with the same weight as any other. The two readings of "practically equivalent" in DEC-012 (band
            reading and label reading) give the same verdict for EXP-003 and EXP-004.
          </figcaption>
        </figure>
        <div className="figure-pair">
          {(["EXP-002", "EXP-004"] as const).map((exp) => (
            <figure key={exp}>
              <div className="table-scroll" role="region" aria-label={`${exp} per-policy drift`} tabIndex={0}>
                <ArmDrift rows={r.arm_drift[exp]} title={exp === "EXP-002" ? "EXP-002, synthetic: mean drift (rad)" : "EXP-004, FMA: mean drift (rad)"} />
              </div>
              <figcaption>
                <strong>{exp === "EXP-002" ? "Figure 2a." : "Figure 2b."}</strong> Mean drift per policy, adaptive
                preferences, 95 % bootstrap intervals over 10 seeds:{" "}
                {r.arm_drift[exp].map((a) => `${a.policy} ${a.display} ${a.interval_display}`).join("; ")}. RAND itself
                moves simulated taste.
              </figcaption>
            </figure>
          ))}
        </div>

        <h3 className="sub">Every registered experiment</h3>
        {r.experiments.map((e) => (
          <article key={e.id} className="panel" aria-labelledby={`h-${e.id}`}>
            <h3 id={`h-${e.id}`}>
              {e.id}: {e.title}
            </h3>
            <p>
              <span className="badge">{e.status}</span>
            </p>
            <p><strong>Verdict under the frozen rule:</strong> {e.verdict}</p>
            {e.estimates.length > 0 && (
              <div className="table-scroll" role="region" aria-label={`${e.id} estimates`} tabIndex={0}>
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Quantity</th>
                      <th scope="col">Estimate</th>
                      <th scope="col">Interval</th>
                      <th scope="col">Unit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {e.estimates.map((x) => (
                      <tr key={x.label} className={x.kind === "exploratory" ? "exploratory" : undefined}>
                        <th scope="row">
                          {x.label}
                          {x.display_source === "supplementary" && <span className="meta"> (printed in Table S2)</span>}
                        </th>
                        <td>{fmtEstimate(x)}</td>
                        <td>
                          {fmtInterval(x)}
                          {x.ci_level !== null && x.ci_level !== 0.95 && <span className="meta"> (level {x.ci_level.toFixed(4)})</span>}
                        </td>
                        <td>{x.unit || "unitless"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {e.notes.map((n, i) => (
              <p key={i} className="note">{n}</p>
            ))}
            <p className="meta">
              Report: <code>{e.report_path}</code>
              {e.claim_ids.length > 0 ? <>. Claims: {e.claim_ids.join(", ")}</> : <>. No claim rests on this experiment.</>}
            </p>
          </article>
        ))}
      </section>

      <TasteMapSection r={r} />

      <section id="assumptions" aria-labelledby="h-assumptions">
        <p className="tag tag-assumption">Assumption</p>
        <h2 id="h-assumptions">Assumptions</h2>
        <p className="note">These values are fixed by the frozen protocol. They are modelling choices, not measurements; the withdrawal in EXP-003 shows that results depend on them.</p>
        <dl className="assumptions">
          {r.assumptions.map((a) => (
            <div key={a.name}>
              <dt>{a.name}</dt>
              <dd>
                {a.value} <span className="meta">({a.source})</span>
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <section id="method" aria-labelledby="h-method">
        <h2 id="h-method">Method and limitations</h2>
        <h3 className="sub">Method (manuscript section 4)</h3>
        <ul className="prose-list">
          {r.method.map((l, i) => (
            <li key={i}>{l}</li>
          ))}
        </ul>
        <h3 className="sub">Limitations and threats to validity (manuscript section 7)</h3>
        <ul className="prose-list">
          {r.limitations.map((l, i) => (
            <li key={i}>{l}</li>
          ))}
        </ul>
        <details>
          <summary>Source files and hashes</summary>
          <ul className="meta">
            {r.sources.map((s) => (
              <li key={s.path}>
                <code>{s.path}</code> <code>{s.sha256.slice(0, 12)}</code>
              </li>
            ))}
          </ul>
        </details>
      </section>
    </>
  );
}

function TasteMapSection({ r }: { r: Results }) {
  const t = r.taste_map;
  const [policy, setPolicy] = useState<string>("SIM");
  const [li, setLi] = useState(0);
  const shown = policy === "RAND" ? ["RAND"] : [policy, "RAND"];
  const paths = shown.map((p) => ({ policy: p, points: t.policies[p].listeners[li].path }));
  return (
    <section id="taste-map" aria-labelledby="h-taste">
      <p className="tag tag-exploratory">Exploratory illustration</p>
      <h2 id="h-taste">Taste map: how one listener's taste moves</h2>
      <p>
        One exploratory seed ({t.seed}) of the {t.setting}. Generated by <code>{t.generator}</code> with the Python
        research engine; stored in <code>{t.source}</code>. It shows the mechanism and supports no claim: one seed, no
        interval.
      </p>
      <div className="controls" role="group" aria-label="Taste map controls">
        <div className="toggle-group" role="group" aria-labelledby="tm-policy-label">
          <span id="tm-policy-label" className="group-label">Policy (compared with RAND)</span>
          <div className="buttons seg">
            {TASTE_POLICIES.map((p) => (
              <button key={p} type="button" className="toggle" aria-pressed={policy === p} onClick={() => setPolicy(p)}>{p}</button>
            ))}
            <span className="seg-ind" aria-hidden="true" style={{ width: `calc((100% - 8px) / ${TASTE_POLICIES.length})`, transform: `translateX(${Math.max(0, TASTE_POLICIES.indexOf(policy as never)) * 100}%)` }} />
          </div>
        </div>
        <label>
          Listener
          <select value={li} onChange={(e) => setLi(Number(e.target.value))}>
            {t.listeners.map((u, i) => <option key={u} value={i}>{u}</option>)}
          </select>
        </label>
      </div>
      <div className="figure-pair">
        <figure>
          <div className="map-wrap">
            <TasteMapSvg tracks={t.tracks} paths={paths}
              label={`Taste map, exploratory: ${t.tracks.length} catalogue tracks in a 2-D projection with listener ${t.listeners[li]}'s preference path under ${shown.join(" and ")}.`} />
          </div>
          <figcaption>
            <strong>Figure 3.</strong> Grey dots: the {t.tracks.length} tracks in the first two principal components of
            their 16-D embeddings (together {Math.round((t.projection.explained_variance_share[0] + t.projection.explained_variance_share[1]) * 100)} % of the variance, so distances are distorted).
            Lines: listener {t.listeners[li]}'s preference vector over {t.policies[policy].listeners[li].path.length - 1} steps,
            projected on the same axes; circle at the start, square at the end. <span className="key-swatch pol-RAND" aria-hidden="true" /> RAND
            {policy !== "RAND" && <> and <span className={`key-swatch pol-${policy}`} aria-hidden="true" /> {policy}</>}.
          </figcaption>
        </figure>
        <figure>
          <div className="table-scroll" role="region" aria-label="Exploratory drift curves" tabIndex={0}>
            <DriftCurves series={TASTE_POLICIES.map((p) => ({ policy: p, values: t.policies[p].mean_drift_by_step }))}
              label="Exploratory: mean angular drift in radians over 100 steps for the five policies, one seed, 200 listeners." />
          </div>
          <figcaption>
            <strong>Figure 4.</strong> Mean drift over the 200 simulated listeners of this one seed, by step, for all five
            policies (radians). Under every policy taste moves steadily away from its start; the published contrasts
            above compare how far.
          </figcaption>
        </figure>
      </div>
    </section>
  );
}
