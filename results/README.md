<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# results

Machine-readable experiment outputs. `results/exploratory/` holds exploratory runs only (never findings); confirmatory results would go to `results/EXP-NNN/` after the owner's freeze. Each run has a result file (`runs/`, schema `echo.result.v1`) and a manifest (`manifests/`). Large raw outputs go to `results/raw/` (git-ignored).
