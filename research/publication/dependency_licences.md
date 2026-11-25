<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Dependency licences (M6, 2026-11-25)

Sources: the installed `.venv` metadata (`importlib.metadata`, after `uv sync --frozen --all-groups --all-extras` from `uv.lock`) for Python, and `demo/node_modules/*/package.json` plus `demo/package-lock.json` (after `npm ci --prefer-offline`) for npm. Acceptable without comment: MIT, BSD, ISC, 0BSD, Zlib, Apache-2.0, PSF, MPL-2.0 or similarly permissive. Nothing here is redistributed by the repository: dependencies are installed from the lock files, and only the built demo bundle (`demo/dist/`, git-ignored) contains npm runtime code (react, react-dom, scheduler; all MIT).

**Flags: none.** Two notes: (1) MPL-2.0 (hypothesis, lightningcss) is file-level copyleft and applies only if those files are modified and distributed; both are development or build tools, used unmodified. (2) The numpy 2.2.6 macOS wheel bundles OpenBLAS and LAPACK (BSD-3-Clause), the GCC runtime library (GPL-3.0 with the GCC Runtime Library Exception, which permits use from non-GPL code), and lapack-lite, dragon4, libdivide, Meson, spin and tempita (BSD, MIT, Zlib, Apache-2.0), as listed in its `LICENSE.txt`.

## Python (8 installed distributions)

| Package | Version | Kind | Licence (metadata) |
|---|---|---|---|
| numpy | 2.2.6 | runtime | BSD-3-Clause (classifier "BSD License"; bundled libraries above) |
| pytest | 8.3.5 | development | MIT |
| hypothesis | 6.131.9 | development | MPL-2.0 |
| attrs | 26.1.0 | development (via hypothesis) | MIT |
| sortedcontainers | 2.4.0 | development (via hypothesis) | Apache-2.0 |
| iniconfig | 2.3.1 | development (via pytest) | MIT |
| packaging | 26.3 | development (via pytest) | Apache-2.0 OR BSD-2-Clause |
| pluggy | 1.7.0 | development (via pytest) | MIT |

The PDF toolchain (pandoc 3.6.3, GPL-2.0-or-later; the typst Python package, Apache-2.0) and Node.js are shared tools outside the repository, invoked as programs and not distributed; the licences named here are as commonly published upstream and are unverified in this session.

## npm (demo, 84 lock entries, 53 installed on macOS arm64)

Runtime (bundled into `demo/dist/`):

| Package | Version | Licence |
|---|---|---|
| react | 19.3.1 | MIT |
| react-dom | 19.3.1 | MIT |
| scheduler | 0.28.0 | MIT |

Build and test only:

| Licence | Packages |
|---|---|
| MIT | @jridgewell/sourcemap-codec 1.6.0, @oxc-project/types 0.156.0, @rolldown/binding-darwin-arm64 1.2.19, @rolldown/pluginutils 1.1.1, @standard-schema/spec 1.1.0, @types/chai 5.2.3, @types/deep-eql 4.0.2, @types/estree 1.0.11, @types/react 19.3.0, @types/react-dom 19.3.0, @vitejs/plugin-react 6.1.2, @vitest/expect, mocker, pretty-format, runner, snapshot, spy, utils 4.1.12, assertion-error 2.0.1, chai 6.3.0, convert-source-map 2.0.0, csstype 3.2.4, es-module-lexer 2.3.2, estree-walker 3.0.3, fdir 6.5.0, fsevents 2.3.3, magic-string 0.30.21, nanoid 3.3.20, obug 2.2.1, pathe 2.0.3, picomatch 4.0.7, postcss 8.5.33, rolldown 1.2.19, stackback 0.0.2, std-env 4.3.0, tinybench 2.9.0, tinyexec 1.4.0, tinyglobby 0.2.17, tinyrainbow 3.2.0, vite 8.3.5, vitest 4.1.12, why-is-node-running 2.3.0 |
| Apache-2.0 | detect-libc 2.1.2, expect-type 1.4.0, typescript 5.9.3 |
| ISC | picocolors 1.1.1, siginfo 2.0.0 |
| BSD-3-Clause | source-map-js 1.2.4 |
| MPL-2.0 | lightningcss 1.33.0, lightningcss-darwin-arm64 1.33.0 |

Optional platform packages in the lock file and not installed on this machine (licence from the lock file): the other 15 @rolldown/binding-* and the other 10 lightningcss-* platform builds (MIT and MPL-2.0), @emnapi/core, @emnapi/runtime, @emnapi/wasi-threads, @napi-rs/wasm-runtime, @tybys/wasm-util (MIT) and tslib (0BSD).
