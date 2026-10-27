$ErrorActionPreference = 'Stop'

# This demo-only fixture is encoded so Gitleaks does not report a secret while
# scanning the clean default branch. Running it writes the intentional finding.
$encodedApp = 'aW1wb3J0IG9zCmltcG9ydCBzcWxpdGUzCmZyb20gZmxhc2sgaW1wb3J0IEZsYXNrLCBqc29uaWZ5LCByZXF1ZXN0CgphcHAgPSBGbGFzayhfX25hbWVfXykKZGVtb19rZXkgPSAiQUtJQTNIN0s5UDJSNlc0TjhYMVEiICAjIEZBS0UgQVdTLXNoYXBlZCB2YWx1ZSBmb3Igc2Nhbm5lciB0cmFpbmluZwpEQVRBQkFTRSA9IG9zLmVudmlyb24uZ2V0KCJEQVRBQkFTRV9QQVRIIiwgIi90bXAvdGFza3MuZGIiKQp3aXRoIHNxbGl0ZTMuY29ubmVjdChEQVRBQkFTRSkgYXMgY29ubjoKICAgIGNvbm4uZXhlY3V0ZSgiQ1JFQVRFIFRBQkxFIElGIE5PVCBFWElTVFMgdGFza3MgKGlkIElOVEVHRVIgUFJJTUFSWSBLRVksIHRpdGxlIFRFWFQgTk9UIE5VTEwsIG93bmVyIFRFWFQgTk9UIE5VTEwpIikKCkBhcHAuZ2V0KCIvdGFza3MiKQpkZWYgbGlzdF90YXNrcygpOgogICAgb3duZXIgPSByZXF1ZXN0LmFyZ3MuZ2V0KCJvd25lciIsICIiKQogICAgd2l0aCBzcWxpdGUzLmNvbm5lY3QoREFUQUJBU0UpIGFzIGNvbm46CiAgICAgICAgcm93cyA9IGNvbm4uZXhlY3V0ZSgiU0VMRUNUIGlkLCB0aXRsZSwgb3duZXIgRlJPTSB0YXNrcyBXSEVSRSBvd25lciA9ICclcyciICUgb3duZXIpCiAgICAgICAgcmV0dXJuIGpzb25pZnkocm93cy5mZXRjaGFsbCgpKQoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIGFwcC5ydW4oaG9zdD0iMC4wLjAuMCIsIHBvcnQ9NTAwMCkK'
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
