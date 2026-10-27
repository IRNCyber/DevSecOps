$ErrorActionPreference = 'Stop'

# This demo-only fixture is encoded so Gitleaks does not report a secret while
# scanning the clean default branch. Running it writes the intentional finding.
$encodedApp = 'aW1wb3J0IG9zCmltcG9ydCBzcWxpdGUzCmZyb20gZmxhc2sgaW1wb3J0IEZsYXNrLCBqc29uaWZ5LCByZXF1ZXN0CgphcHAgPSBGbGFzayhfX25hbWVfXykKZGVtb19rZXkgPSAiQUtJQTNIN0s5UDJSNlc0TjhYMVEiICAjIEZBS0UgQVdTLXNoYXBlZCBkZW1vIHZhbHVlIG9ubHkKREFUQUJBU0UgPSBvcy5lbnZpcm9uLmdldCgiREFUQUJBU0VfUEFUSCIsICIvdG1wL3Rhc2tzLmRiIikKCkBhcHAuZ2V0KCIvdGFza3MiKQpkZWYgbGlzdF90YXNrcygpOgogICAgb3duZXIgPSByZXF1ZXN0LmFyZ3MuZ2V0KCJvd25lciIsICIiKQogICAgd2l0aCBzcWxpdGUzLmNvbm5lY3QoREFUQUJBU0UpIGFzIGNvbm46CiAgICAgICAgY3Vyc29yID0gY29ubi5leGVjdXRlKCJTRUxFQ1QgaWQsIHRpdGxlLCBvd25lciBGUk9NIHRhc2tzIFdIRVJFIG93bmVyID0gJyVzJyIgJSBvd25lcikKICAgICAgICByZXR1cm4ganNvbmlmeShjdXJzb3IuZmV0Y2hhbGwoKSkKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBhcHAucnVuKGhvc3Q9IjAuMC4wLjAiLCBwb3J0PTUwMDApCg=='
[IO.File]::WriteAllBytes((Join-Path $PSScriptRoot '..\app.py'), [Convert]::FromBase64String($encodedApp))
Set-Content -Path (Join-Path $PSScriptRoot '..\requirements.txt') -Value @('Flask==2.0.1', 'Werkzeug==2.0.1', 'gunicorn==20.1.0')
Set-Content -Path (Join-Path $PSScriptRoot '..\Dockerfile') -Value @'
FROM python:3.9-slim-bullseye
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
'@
Write-Host 'Vulnerable demo state written. Review the diff, then commit and push this branch to trigger red gates.'
