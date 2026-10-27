# Focusboard | Project Report

## Executive summary

Focusboard is a responsive, single-workspace task manager built with Flask, SQLite, and browser-native JavaScript. The project pairs a usable application with a GitHub Actions security pipeline that scans secrets, dependencies, source code, and the built container, and generates a CycloneDX SBOM.

## Problem and objective

Small task lists are often stored in ad hoc notes with little structure. This project provides a focused local workspace with task status, priority, due dates, search, and lifecycle management. It also demonstrates how security controls can run automatically during code changes.

## Application design

- **Interface:** responsive dashboard, status filters, task counts, search, task editor, and due-date indicators.
- **API:** JSON endpoints for task listing, creation, partial updates, and deletion, plus a health endpoint.
- **Storage:** SQLite with schema constraints, transaction handling, write-ahead logging, and configurable database location.
- **Runtime:** Flask served directly for local development or through Gunicorn in a non-root Docker container.

## Security design

All SQL data values use bound parameters. API payloads are type-checked and length-limited, task fields and enum values are allowlisted, request bodies have a size limit, and the browser interface inserts user-provided text through safe DOM text APIs. The service sends a restrictive Content Security Policy and standard browser security headers. Dependencies are pinned in `requirements.txt`.

The application is single-workspace and does not implement user authentication. It is intended for local portfolio evaluation and should not be exposed to the public internet or used to store sensitive information.

## CI/CD security gates

| Control | Purpose | Gate behavior |
|---|---|---|
| Gitleaks | Detect committed credentials | Secret finding fails the job |
| Trivy filesystem | Inspect dependency vulnerabilities | HIGH/CRITICAL finding fails the job |
| SonarQube Cloud | Analyze Python and evaluate configured quality gate | Quality gate failure fails the job |
| Trivy image | Scan the built Docker image | HIGH/CRITICAL finding fails the job |
| Syft | Generate CycloneDX inventory | Uploads SBOM as an Actions artifact |

The jobs run on pushes and pull requests. Workflow permissions default to read-only; the Gitleaks job receives scoped `pull-requests: write` permission so it can annotate detected secrets on pull requests. SonarQube Cloud uses the `SONAR_TOKEN` repository secret plus `SONAR_ORGANIZATION` and `SONAR_PROJECT_KEY` Actions variables. Missing configuration fails closed instead of skipping the quality gate; fork pull requests do not receive the secret.

## Reproduction and evidence

Install dependencies from `requirements.txt`, run Flask locally, and open `http://127.0.0.1:5000`. Docker instructions and API examples are in `README.md`. Push the fixed branch to observe the passing state. The `scripts/make-vulnerable.ps1` script creates an intentionally insecure branch for scanner demonstration; keep it isolated and never deploy it.

After publishing, attach genuine screenshots of the application and both Actions outcomes under `docs/images/`. Do not treat local behavior as proof of GitHub Actions results; the workflow requires the repository and SonarQube Cloud configuration described in the README.

## Tradeoffs and future work

Severity thresholds reduce noise compared with blocking every vulnerability, but scanner findings still need review. The pipeline depends on a live vulnerability database, so results may change over time. Natural next steps are authenticated multi-user support, automated migration/versioning, a deployment environment, and scheduled dependency updates; each would require its own threat review and security gates.
