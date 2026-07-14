# Chapter 5 · Lesson 3 — Securing Production Images Demo Runbook

> Recording guide for the security demo. The full lesson `README.md` /
> `script_c5_l3.md` / slides are authored separately; this file is the hands-on
> steps to run on screen. It follows the Lesson 2 demo style (before → after).

Demo asset files in this folder:

| File | Role |
| ---- | ---- |
| `Dockerfile_Query.insecure` | the "before" — root user, baked secret, extra tools |
| `Dockerfile_Query` | the "after" — pinned/slim, minimal surface, non-root, no baked secret |
| `requirements-query.txt` | the query-service dependency set |
| `.dockerignore` | keeps secrets and junk out of the build context |
| `query_cli.py` | runnable entry point (`--check` / `--whoami` / `--secret-check`, all offline) |

All commands run from the **repository root** (the build context must contain
`rag/`). The `OPENAI_API_KEY` values shown are fake placeholders.

## 1. Build the insecure image (the "before")

```bash
docker build -f chapter_5/l3/Dockerfile_Query.insecure -t rag-query:insecure .
```

## 2. Build the hardened image (the "after")

```bash
docker build -f chapter_5/l3/Dockerfile_Query -t rag-query:0.1.0 .
```

## 3. Least privilege — non-root

```bash
docker run --rm rag-query:insecure --whoami
# running as: root (uid=0 ...)  -> WARNING: running as root

docker run --rm rag-query:0.1.0 --whoami
# running as: appuser (uid=10001 ...)  -> non-root
```

## 4. No secrets in layers — prove the leak, then the fix

```bash
# The insecure image baked the key into a layer — it's right there in history:
docker history --no-trunc rag-query:insecure | grep -i openai_api_key

# The hardened image has no baked key — this returns nothing:
docker history --no-trunc rag-query:0.1.0 | grep -i openai_api_key || echo "no secret in layers"

# Inject the key at runtime instead (value stays in the env, never in a layer):
export OPENAI_API_KEY="sk-demo-injected-at-runtime"
docker run --rm -e OPENAI_API_KEY rag-query:0.1.0 --secret-check
# OPENAI_API_KEY is set (length ...) — injected at runtime.
```

## 5. Minimal surface — scan, fix, re-scan

```bash
# Scan both and compare CVE counts / installed packages.
docker scout quickview rag-query:insecure
docker scout quickview rag-query:0.1.0
# or: trivy image --severity HIGH,CRITICAL rag-query:insecure

# The hardened image drops curl/vim/git and the build toolchain, so it carries
# fewer packages and a smaller CVE surface. Bump the base/deps, rebuild, re-scan.
```

## 6. Tighten at runtime (defense in depth)

```bash
docker run --rm --read-only --cap-drop ALL rag-query:0.1.0 --check
# Still imports and runs the query stack, with a read-only fs and no capabilities.
```

## Talking points while recording

- **Least privilege**: the insecure image runs as root; the hardened one drops to
  `appuser` (uid 10001). `--whoami` makes it visible.
- **No secrets in layers**: `docker history` exposes the baked key in the "before"
  image — anyone who pulls it gets the secret. The "after" injects it at runtime.
- **Minimal surface**: multi-stage + slim + no extra tools = fewer packages, so
  the scanner has less to flag. Pin the base by **digest** for reproducibility.
- **Scan → fix → re-scan** is the habit, not a one-time check.
- `.dockerignore` must live at the **build-context root** to take effect — keeping
  `.env`/keys out of the context is the security reason it matters here.
