# Chapter 2 — Example 03: Parameterizing the build with `ARG`

This example builds the same Python development image as
[`chapter_2/02`](../02), but with one important difference: the values
that were previously hard-coded (`python-dev`, `3.12.11`, the `ruff`
version, etc.) are now declared as **build-time arguments** with the
`ARG` instruction.

This README focuses on **what `ARG` does, why you'd use it, and how to
work with it** — not on the rest of the Dockerfile, which is the same
as `chapter_2/02`.

---

## 1. What changed compared to `chapter_2/02`

```diff
  FROM ubuntu:22.04
+
+ ARG PYTHON_VER="3.12.11"
+ ARG UV_VER="0.11.16"
+ ARG RUFF_VER="0.15.12"
+ ARG VENV_NAME="python-dev"

  RUN apt-get update && apt-get install -y --no-install-recommends \
          curl ca-certificates \
      && rm -rf /var/lib/apt/lists/*

- RUN curl -LsSf https://astral.sh/uv/install.sh | sh
- RUN curl -LsSf https://astral.sh/ruff/install.sh | sh
+ RUN curl -LsSf https://astral.sh/uv/$UV_VER/install.sh | sh
+ RUN curl -LsSf https://astral.sh/ruff/$RUFF_VER/install.sh | sh

  RUN mkdir settings
  COPY install_uv.sh requirements.txt settings/
- RUN bash ./settings/install_uv.sh python-dev 3.12.11
+ RUN bash ./settings/install_uv.sh $VENV_NAME $PYTHON_VER
```

Four values are now parameters:

| `ARG`         | Default      | Used in                                                                |
| ------------- | ------------ | ---------------------------------------------------------------------- |
| `PYTHON_VER`  | `3.12.11`    | Python version passed to `uv venv` via `install_uv.sh`.                |
| `UV_VER`      | `0.11.16`    | Pinned version of `uv` downloaded from `https://astral.sh/uv/<ver>/`.  |
| `RUFF_VER`    | `0.15.12`    | Pinned version of `ruff` downloaded from `https://astral.sh/ruff/<ver>/`. |
| `VENV_NAME`   | `python-dev` | Folder name for the virtual environment under `/opt/<VENV_NAME>`.       |

---

## 2. What `ARG` does

`ARG` declares a **build-time variable**. Its scope is:

- **Available only during `docker build`** (inside `RUN`, `COPY`, `ADD`,
  and string interpolation in other instructions).
- **Not available in the running container.** Once the image is built,
  `ARG` values are gone unless you explicitly promote them to `ENV`
  (more on that below).
- **Lasts from the line it is declared until the end of the build stage**
  (or the next `FROM` in a multi-stage build, where it would have to be
  re-declared).

Syntax:

```dockerfile
ARG NAME              # no default — must be passed via --build-arg
ARG NAME="default"    # has a default, can be overridden
```

### `ARG` vs `ENV` — a common point of confusion

| Aspect                          | `ARG`                                       | `ENV`                                          |
| ------------------------------- | ------------------------------------------- | ---------------------------------------------- |
| Available during build          | Yes                                         | Yes                                            |
| Available at container runtime  | **No**                                      | Yes (set in the image's environment)            |
| Overridable at build time       | Yes — `docker build --build-arg NAME=...`   | No (you'd change the Dockerfile or override at runtime with `-e`) |
| Overridable at run time         | No                                          | Yes — `docker run -e NAME=value`               |
| Stored in image metadata        | No (only the *fact that an `ARG` exists* is recorded — values are not) | Yes                                            |

Rule of thumb:

- Use `ARG` for things that affect **how the image is built**
  (versions, feature flags, build-only credentials).
- Use `ENV` for things the **running application needs** (`PATH`,
  `LANG`, app config defaults).
- Use both if a value is needed at build *and* at run time:
  ```dockerfile
  ARG APP_VER=1.2.3
  ENV APP_VER=$APP_VER
  ```

---

## 3. Building the image

### 3.1 With the defaults

If the defaults work for you, build it just like any other image:

```bash
cd chapter_2/03
docker build -t rkrispin/chapter_2:v0.3.0 .
```

The image is produced using `PYTHON_VER=3.12.11`, `UV_VER=0.11.16`,
`RUFF_VER=0.15.12`, `VENV_NAME=python-dev`.

### 3.2 Overriding one or more `ARG`s

Use `--build-arg <NAME>=<VALUE>` once per argument you want to change:

```bash
docker build \
    --build-arg PYTHON_VER=3.11.9 \
    --build-arg RUFF_VER=0.13.0 \
    -t rkrispin/chapter_2:py3.11 \
    .
```

Things to know:

- The `=` is required (`--build-arg PYTHON_VER 3.11.9` does **not** work).
- Quoting is shell-level. Use quotes when the value has spaces or `$`s.
- If you misspell an `ARG` name (e.g. `--build-arg PYHON_VER=3.11.9`),
  Docker will warn `[Warning] One or more build-args ... were not
  consumed` and **continue with the default**. Watch for that line.

### 3.3 Pulling an `ARG` from your shell environment

If you omit the value, Docker reads it from your shell:

```bash
export PYTHON_VER=3.13.0
docker build --build-arg PYTHON_VER -t rkrispin/chapter_2:py3.13 .
```

This is handy in CI where versions come from environment variables.

### 3.4 Required (no-default) `ARG`s

If you declare an `ARG` without a default:

```dockerfile
ARG GIT_SHA
```

…and don't pass `--build-arg GIT_SHA=...`, the variable expands to an
empty string. There is no built-in "fail if missing" — if you need that,
add a guard inside a `RUN`:

```dockerfile
ARG GIT_SHA
RUN test -n "$GIT_SHA" || (echo "GIT_SHA must be set"; exit 1)
```

---

## 4. Verifying the `ARG`s were applied

`ARG` values are **not** stored in the final image, so you can't
`docker inspect` them directly. Instead, look at the build history:

```bash
docker history --no-trunc rkrispin/chapter_2:v0.3.0 | grep -E "uv/|ruff/|install_uv"
```

You should see lines containing the resolved versions, e.g.
`https://astral.sh/uv/0.11.16/install.sh` and
`bash ./settings/install_uv.sh python-dev 3.12.11`.

You can also verify the runtime tool versions inside a container:

```bash
docker run --rm rkrispin/chapter_2:v0.3.0 \
    bash -lc 'uv --version && ruff --version'
```

(`bash -lc` is used because this Dockerfile relies on
`~/.local/bin/env` being sourced for `uv`/`ruff` to be on `PATH`.)

---

## 5. Common gotchas

### 5.1 `ARG` before `FROM` is special

`ARG` declared **before** the first `FROM` is only usable in the `FROM`
line itself. To reuse it later, redeclare it after `FROM`:

```dockerfile
ARG UBUNTU_TAG=22.04
FROM ubuntu:${UBUNTU_TAG}

ARG UBUNTU_TAG          # bring it back into scope
RUN echo "Built on Ubuntu ${UBUNTU_TAG}"
```

### 5.2 `ARG` does not persist across stages

In a multi-stage build, each `FROM` starts a fresh scope. Re-declare any
`ARG` you need in each stage that uses it.

### 5.3 Don't put secrets in `ARG`

Although `ARG` values aren't kept as a runtime env var, the **command
that used them is recorded in the image's layer history** and visible
via `docker history`. Anyone who pulls the image can read it.

For build-time secrets (API tokens, SSH keys), use BuildKit's
`--secret` flag instead:

```bash
docker build --secret id=mytoken,src=./token.txt ...
```

```dockerfile
RUN --mount=type=secret,id=mytoken \
    curl -H "Authorization: Bearer $(cat /run/secrets/mytoken)" ...
```

### 5.4 Cache busting

Changing an `ARG` value (via `--build-arg`) invalidates the cache for
every subsequent layer that *uses* that `ARG`. Order your Dockerfile so
the `ARG`s most likely to change appear **after** layers you want to
keep cached.

---

## 6. When to reach for `ARG`

Good fits:

- Pinning versions of tools or base images (`PYTHON_VER`, `UV_VER`).
- Building variants of the same image from one Dockerfile (CPU vs. GPU,
  dev vs. prod, different Linux distros).
- Injecting build metadata (`GIT_SHA`, `BUILD_DATE`) for traceability.
- Toggling feature flags during the build (`INSTALL_DEBUG_TOOLS=true`).

When **not** to use `ARG`:

- For values the running container needs — use `ENV`.
- For secrets — use BuildKit `--secret` mounts.
- For values that change between every build *and* you want to cache
  the rest of the image — consider whether the value really needs to
  affect the build at all.
