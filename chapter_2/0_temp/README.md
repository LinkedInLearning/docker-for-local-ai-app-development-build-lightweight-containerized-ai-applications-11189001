# Chapter 2 — `0_temp`: Dockerfile best-practice tweaks

This folder is a variant of [`chapter_2/02`](../02) with three small but
important best-practice changes applied:

1. A **`.dockerignore`** file.
2. An explicit **`ENV PATH=...`** line so `uv` and `ruff` are always on `PATH`.
3. An explicit **`WORKDIR /app`** so the build has a predictable, non-root
   working directory.

Everything else (`install_uv.sh`, `requirements.txt`, the build/run flow)
is identical to `chapter_2/02`. This README focuses only on the diffs and
why they are an improvement.

---

## 1. `.dockerignore`

### What is it?

`.dockerignore` is to `docker build` what `.gitignore` is to `git`.
When you run `docker build .`, Docker bundles **the entire build context**
(every file in `.`) and sends it to the Docker daemon before the build
starts. The daemon then uses that bundle as the source for `COPY` and
`ADD` instructions.

`.dockerignore` tells Docker which files to **exclude** from that bundle.

### Why it matters

Without a `.dockerignore`, three things go wrong:

| Problem                               | Cause                                                                                               |
| ------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Slow builds                           | The whole `.git/`, `node_modules/`, `__pycache__/`, etc. is copied to the daemon on every build.    |
| Cache busted unnecessarily            | A change to *any* unrelated file in the context can invalidate `COPY . .` layers downstream.        |
| Secret leaks                          | `COPY . .` happily copies `.env`, `*.pem`, and `secrets/` into image layers — even if later removed. |

The last point is the most dangerous: anyone who pulls your image can
unpack the layers and recover those files.

### What we exclude here

The file in this folder excludes:

- **Version control:** `.git`, `.gitignore`, `.github`
- **IDE / editor metadata:** `.idea`, `.vscode`, `*.swp`, `*.swo`
- **Python build artifacts:** `__pycache__`, `*.pyc`, `*.egg-info`,
  `.venv`, `venv`, `dist`, `build`
- **OS junk:** `.DS_Store`, `Thumbs.db`
- **Logs / temp / caches:** `*.log`, `*.tmp`, `tmp`, `.cache`
- **Secrets:** `.env`, `.env.*`, `*.pem`, `*.key`, `*.crt`, `secrets`
- **Documentation:** `README.md`, `docs` (the build doesn't need them)

### Verifying it works

After a build, you can confirm the excluded files are not in the image:

```bash
docker run --rm rkrispin/chapter_2:v0.2.0 \
    sh -c 'ls -la /app && find / -name ".git" -o -name ".env" 2>/dev/null'
```

You should see nothing matching `.git` or `.env`.

---

## 2. `ENV PATH="/root/.local/bin:${PATH}"`

### What changed

```diff
  RUN curl -LsSf https://astral.sh/uv/install.sh | sh
  RUN curl -LsSf https://astral.sh/ruff/$RUFF_VER/install.sh | sh
+
+ ENV PATH="/root/.local/bin:${PATH}"
```

### Why it matters

The Astral installers drop their binaries into `/root/.local/bin/uv` and
`/root/.local/bin/ruff`. They also write a small shell snippet to
`/root/.local/bin/env` that prepends that directory to `PATH`. **But that
snippet only runs if a shell sources it** — which happens at interactive
login on the host, but **not** automatically inside a Docker `RUN` step
or when a container starts.

Without the `ENV PATH=...` line, you get this kind of footgun:

```bash
$ docker run --rm rkrispin/chapter_2:v0.1.0 uv --version
docker: Error response from daemon: failed to create task ...:
exec: "uv": executable file not found in $PATH
```

…because the default `PATH` in the container doesn't include
`/root/.local/bin`. You'd have to remember to either:

- run `bash -lc "uv --version"` (login shell, sources the env file), or
- prefix every command with `source ~/.local/bin/env &&`.

### How `ENV` fixes it

`ENV` writes the variable into the image's metadata. Every subsequent
`RUN` *and* every container started from the image inherits the
modified `PATH`. From the moment this line runs:

- `RUN bash ./settings/install_uv.sh ...` finds `uv` without sourcing
  anything.
- `docker run ... uv --version` works directly.
- `docker exec -it <container> ruff check .` works directly.

### Where to place it

Put `ENV PATH=...` **immediately after** the install steps that put files
in `/root/.local/bin`, so every later layer benefits. Putting it at the
top of the Dockerfile would also work, but right after the installers
makes the relationship between "I just installed something here" and
"now make it discoverable" obvious to anyone reading the file.

### Caveat about non-root users

`/root/.local/bin` only exists because `uv`/`ruff` were installed *as
root*. The moment you add `USER app` later, that path becomes useless
(and may not even be readable). For a multi-user / production image
you'd typically install the binaries into a system-wide location:

```dockerfile
ENV UV_INSTALL_DIR=/usr/local/bin
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
# No ENV PATH= line needed — /usr/local/bin is already on PATH.
```

---

## 3. `WORKDIR /app`

### What changed

```diff
- RUN mkdir settings
- COPY install_uv.sh requirements.txt settings/
- RUN bash ./settings/install_uv.sh $VENV_NAME $PYTHON_VER
+ WORKDIR /app
+ COPY install_uv.sh requirements.txt settings/
+ RUN bash ./settings/install_uv.sh $VENV_NAME $PYTHON_VER
```

### Why it matters

Without `WORKDIR`, every `RUN` and `COPY` runs against the container's
filesystem **root (`/`)**. Three problems with that:

1. **Pollutes `/`.** The previous Dockerfile ended up creating
   `/settings/` directly under root, mixing app files with system
   directories like `/etc`, `/var`, `/usr`. That makes the image harder
   to reason about.
2. **No persistence between layers.** People sometimes try `RUN cd /foo
   && do_something` — but `cd` is scoped to that `RUN` and is forgotten
   immediately. `WORKDIR` is the persistent equivalent.
3. **Brittle relative paths.** `bash ./settings/install_uv.sh` only
   works if the current directory is what you expect. With `WORKDIR
   /app` set explicitly, every contributor (and every later `RUN`,
   `COPY`, and runtime command) starts from the same place.

### Side benefits

- `RUN mkdir settings` is no longer needed — `COPY ... settings/`
  auto-creates the destination directory under `WORKDIR`.
- When you `docker run --rm -it <image>` and land in a shell, you start
  in `/app` instead of `/`, which is what most people expect.
- Bind mounts are easier to reason about: `-v $(pwd):/app` lines up
  cleanly with the `WORKDIR`.

### Conventions

Common `WORKDIR` choices and when to use them:

| Path           | When to use                                                           |
| -------------- | --------------------------------------------------------------------- |
| `/app`         | Application code (most popular default).                              |
| `/workspace`   | Dev containers (matches VS Code Dev Containers' default).             |
| `/opt/<name>`  | Long-lived installed software, not the project's own source code.     |
| `/srv/<name>`  | Service data (Linux FHS convention; less common in container land).   |

Avoid `/`, `/root`, `/tmp`, and `/home` for app code — they're either
conventionally reserved or ephemeral.

---

## 4. Building and running this variant

The build/run commands are the same as `chapter_2/02`, just from this
folder:

```bash
cd chapter_2/0_temp
docker build -t rkrispin/chapter_2:v0.2.0 .
docker run --rm -it rkrispin/chapter_2:v0.2.0 bash
```

Inside the container, the three improvements are visible:

```bash
pwd                       # /app   <- thanks to WORKDIR
which uv                  # /root/.local/bin/uv   <- thanks to ENV PATH
which ruff                # /root/.local/bin/ruff
ls /app                   # contains settings/   <- COPY landed here
ls /app/settings          # install_uv.sh, requirements.txt
```

And the build context is now lean — try:

```bash
docker build --progress=plain -t rkrispin/chapter_2:v0.2.0 . 2>&1 | head
```

The "transferring context" line should show only a few KB instead of
megabytes (the difference is everything `.dockerignore` excluded).
