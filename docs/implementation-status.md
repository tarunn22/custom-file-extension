# File Monitor Extension Implementation Status

## Overview

This document records the work completed to prepare, validate, sign, and upload the Dynatrace File Monitor Extension Framework 2.0 extension.

Version 1.1.0 was uploaded successfully to the Dynatrace environment configured for this project. Version 1.1.1 has since been rebuilt and signed locally; its tenant validation and upload are still pending. No API token or private-key contents are included in this document.

## Environment

- Project: `cffileextension`
- Python environment: `.venv`
- Dynatrace CLI: `dt-cli` version `1.6.21`
- Python Extensions SDK CLI: `dt-sdk`
- Dynatrace API endpoint configured locally in `.env`: `[redacted]`
- Local credentials file: `.env`

The `.env` file is ignored by Git. The API token is stored only locally and is intentionally omitted from this report.

## Completed Work

### 1. Local credentials setup

Created `.env` with the Dynatrace environment URL and API token. Added `.env` to `.gitignore` so the credentials file is not committed.

Files:

- `.env`
- `.gitignore`

### 2. Python environment setup

The existing `.venv` did not contain `pip`. The environment was repaired with `ensurepip`, then the project was installed in editable mode.

Completed commands:

```powershell
.\.venv\Scripts\python.exe -m ensurepip --upgrade
.\.venv\Scripts\python.exe -m pip install -e .
```

The extension entry point was smoke-tested successfully:

```powershell
.\.venv\Scripts\python.exe -m file_monitor --help
```

### 3. Dynatrace CLI setup

Installed `dt-cli` into the project virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install dt-cli
```

Verified the CLI reports version `1.6.21`.

The Python Extensions SDK CLI `dt-sdk` was also available in the environment and was used for the final build because it packages Python wheels and extension assets correctly.

### 4. Certificate generation

Generated a local certificate authority and developer signing certificate using blank passphrases.

Generated files:

- `ca.pem`: public CA certificate for Dynatrace registration
- `ca.key`: private CA key
- `developer.pem`: developer certificate
- `developer.key`: developer private key
- `developer-certkey.pem`: fused developer certificate and private key used by the modern signing workflow

Private key files are excluded by the repository’s existing certificate/key ignore rules. Private keys must never be uploaded to Dynatrace or committed to Git.

The public CA certificate was registered in Dynatrace before the final upload.

### 5. Extension manifest migration

The original manifest used legacy Python and activation configuration fields. Dynatrace validation required the current Extensions 2.0 structure, so `extension/extension.yaml` was updated to:

- Use Python runtime metadata with module `file_monitor`.
- Use Python `local` and `remote` activation paths.
- Point both activation paths to `activationSchema.json`.
- Raise `minDynatraceVersion` to `1.285`, matching the documented Python Extensions 2.0 baseline.
- Add required list and details screen settings.
- Add required chart counts and current graph-chart configuration.
- Continue referencing the bundled dashboard at `dashboards/overview.json`.

### 6. Activation schema

Added `extension/activationSchema.json` and aligned it with the SDK-generated schema format.

The schema now includes:

- File endpoint type with `file_path` and `count_lines` fields.
- Endpoint summary pattern based on `{file_path}`.
- `pythonRemote` and `pythonLocal` types.
- List configuration for monitored endpoints.
- Local and remote activation properties.

### 7. Python package build contents

The final SDK build packages the extension with:

- `extension.yaml`
- `activationSchema.json`
- `dashboards/overview.json`
- `lib/file_monitor-1.1.1-py3-none-any.whl`
- `lib/dt_extensions_sdk-1.10.2-py3-none-any.whl`

### 8. Dashboard packaging

The manifest referenced `dashboards/overview.json`, but the initial package did not include that file. The dashboard was copied into `extension/dashboards/overview.json` so the SDK build includes it at the expected archive path.

### 9. Build and signing

The supported SDK build workflow was used with the fused developer certificate:

```powershell
$env:PATH = "$PWD\.venv\Scripts;$env:PATH"
.\.venv\Scripts\dt-sdk.exe build . --private-key .\developer-certkey.pem
```

The previously uploaded signed package was:

```text
dist\custom_file-monitor-1.1.0.zip
```

### 10. Remote validation and upload

The signed package was validated successfully against the Dynatrace environment:

```powershell
.\.venv\Scripts\dt.exe ext validate .\dist\custom_file-monitor-1.1.0.zip \
  --tenant-url <environment-url> \
  --api-token <api-token>
```

The package was then uploaded successfully:

```powershell
.\.venv\Scripts\dt.exe ext upload .\dist\custom_file-monitor-1.1.0.zip \
  --tenant-url <environment-url> \
  --api-token <api-token>
```

Dynatrace reported:

```text
Extension validation successful!
Extension upload successful!
```

Those remote validation and upload results apply to version 1.1.0. The current version 1.1.1 package was rebuilt and signed locally after OneAgent reported a signature-check failure for version 1.1.0. Its `extension.zip` and `extension.zip.sig` entries are present, its manifest reports version 1.1.1, and the developer certificate verifies against the local CA certificate. Version 1.1.1 has not yet been validated or uploaded to Dynatrace.

```text
dist\custom_file-monitor-1.1.1.zip
```

## Current Important Files

- [`.env`](../.env): local environment URL and API token; ignored by Git.
- [`.gitignore`](../.gitignore): ignores credentials, certificates, build outputs, and virtual environments.
- [`extension/extension.yaml`](../extension/extension.yaml): extension manifest.
- [`extension/activationSchema.json`](../extension/activationSchema.json): monitoring configuration schema.
- [`extension/dashboards/overview.json`](../extension/dashboards/overview.json): bundled dashboard definition.
- [`activation_config.json`](../activation_config.json): local testing configuration.
- [`dist/custom_file-monitor-1.1.0.zip`](../dist/custom_file-monitor-1.1.0.zip): previously uploaded package.
- [`dist/custom_file-monitor-1.1.1.zip`](../dist/custom_file-monitor-1.1.1.zip): current locally rebuilt and signed package; tenant validation/upload pending.

## Remaining Work

First validate and upload `dist\custom_file-monitor-1.1.1.zip` to Dynatrace, using the CA certificate that issued its developer signing certificate in the tenant's extension-certificate trust settings. Then confirm OneAgent downloads version 1.1.1 without a signature error. Do not copy the CA certificate into the OneAgent host certificate directory or upload signing private keys. Once the package is accepted, create or update the monitoring configuration:

1. Open Dynatrace Hub and locate **File Monitor** under managed/custom extensions.
2. Create a monitoring configuration for the uploaded extension.
3. Select the execution context appropriate for the deployment:
   - OneAgent for local file monitoring on hosts.
   - ActiveGate for remote execution where supported.
4. Add one or more file paths and choose whether line counts should be collected.
5. Assign the configuration to the intended host, host group, or ActiveGate group.
6. Activate the configuration.
7. Confirm that the extension reports metrics such as:
   - `custom.file.exists`
   - `custom.file.size_bytes`
   - `custom.file.age_seconds`
   - `custom.file.line_count`
   - `custom.file.change_age_seconds`
   - `custom.file.mode`
8. Confirm the bundled dashboard is available and displays data.

## Security Follow-Up

The API token was supplied during this session and should be treated as exposed. Revoke it and create a replacement token with only the permissions required for extension validation/upload. Update the local `.env` with the replacement token without committing the file.

The certificate private keys remain local. Keep `ca.key`, `developer.key`, `developer.pem`, and `developer-certkey.pem` private and backed up securely if future rebuilds are required.

## Current Status

**Build:** Version 1.1.1 complete  
**Signing:** Version 1.1.1 complete; local CA chain verified  
**Remote validation:** Version 1.1.0 successful; version 1.1.1 pending  
**Upload:** Version 1.1.0 successful; version 1.1.1 pending  
**OneAgent signature issue:** Pending verification with version 1.1.1  
**Monitoring configuration and activation:** Pending  