# Focusboard Secure Task Manager

**Focusboard** is a responsive task manager built with Flask, SQLite, and browser JavaScript. It lets a single local user create, search, filter, edit, prioritize, complete, reopen, and delete tasks. The project also includes a GitHub Actions DevSecOps pipeline.

## Technologies

- Python 3.12, Flask, Gunicorn, SQLite
- HTML, CSS, and vanilla JavaScript
- Docker, GitHub Actions, Gitleaks, Trivy, SonarQube Cloud, and Syft

## Dataset

No external dataset is used. Tasks are entered by the user and stored in a local SQLite database. Set `DATABASE_PATH` to choose its location; otherwise the operating system's temporary directory is used.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app app run --host 127.0.0.1 --port 5000
```

Open <http://127.0.0.1:5000>. On macOS/Linux, activate `.venv/bin/activate` and run `flask --app app run --host 127.0.0.1 --port 5000`.

## Run with Docker

```sh
docker build -t focusboard .
docker run --rm -p 5000:5000 -e DATABASE_PATH=/tmp/tasks.db focusboard
```

## Security pipeline

Pushes and pull requests run Gitleaks, Trivy filesystem and container scans, and SonarQube Cloud analysis with a blocking quality gate. Trivy fails on HIGH/CRITICAL findings. Syft generates a CycloneDX SBOM artifact. Set the `SONAR_TOKEN` GitHub Actions secret and configure the SonarQube Cloud project before expecting the SAST job to pass.

The `vulnerable-demo` branch generator intentionally introduces scanner findings for portfolio review. Never deploy that branch. Focusboard has no authentication and is designed for local use only; do not expose it to the public internet or store sensitive data.

**GitHub repository:** <https://github.com/IRNCyber/DevSecOps>
