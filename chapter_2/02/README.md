# Chapter 2 — Example 02: Building a Python Dev Image with `uv` and `ruff`

## 1. What this Dockerfile does

This Dockerfile builds a lightweight Ubuntu-based image that contains a fully
configured Python development environment. The environment is built around
two tools from [Astral](https://astral.sh):

- **`uv`** — a fast, modern Python package and virtual-environment manager
  (a drop-in replacement for `pip` + `venv` + `pip-tools`).
- **`ruff`** — a fast Python linter and formatter.

At a high level the image is produced in three phases:

1. Start from `ubuntu:22.04` and install the OS-level prerequisites needed to
   download files over HTTPS (`curl` and `ca-certificates`).
2. Install `uv` and a pinned version of `ruff` from Astral's official install
   scripts.
3. Copy a helper script (`install_uv.sh`) and a `requirements.txt` into the
   image and run the helper to provision a Python virtual environment with the
   project's Python dependencies.

The result is an image suitable for use as a local Python development sandbox
(e.g. as the base of a VS Code Dev Container).

### Files used at build time

| File                | Purpose                                                                 |
| ------------------- | ----------------------------------------------------------------------- |
| `Dockerfile`        | Defines the image build steps.                                          |
| `install_uv.sh`     | Helper script that creates a `uv`-managed virtual environment.          |
| `requirements.txt`  | Python packages installed into the virtual environment (e.g. `pandas`). |

## 2. Line-by-line walkthrough of the Dockerfile

```dockerfile
FROM ubuntu:22.04
```
Use Ubuntu 22.04 (LTS) as the base image. It is small, well supported, and a
common starting point for Python images.

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
```
Install OS prerequisites:

- `curl` — needed to download the `uv` and `ruff` install scripts.
  (`ubuntu:22.04` does **not** ship with `curl` by default.)
- `ca-certificates` — needed for `curl` to validate HTTPS connections to
  `astral.sh`.
- `--no-install-recommends` keeps the layer small.
- `rm -rf /var/lib/apt/lists/*` removes the apt index cache so it is not
  baked into the image layer.

```dockerfile
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN curl -LsSf https://astral.sh/ruff/install.sh | sh
```
Download and execute Astral's official install scripts for `uv` and `ruff`.
Both binaries are placed in `/root/.local/bin/`. These URLs always install
the **latest** version — see [`chapter_2/03`](../03) for an example that
pins the versions using `ARG`.

`curl` flags:
- `-L` follow redirects
- `-s` silent (no progress bar)
- `-S` still show errors
- `-f` fail (non-zero exit) on HTTP errors

```dockerfile
RUN mkdir settings
```
Create a `settings/` folder at the working directory (`/`) that will hold the
helper script and requirements file.

```dockerfile
COPY install_uv.sh requirements.txt settings/
```
Copy the helper script and the Python requirements file from the build
context into the `settings/` folder inside the image.

```dockerfile
RUN bash ./settings/install_uv.sh python-dev 3.12.11
```
Run the helper script, passing the venv name (`python-dev`) and the Python
version (`3.12.11`) as positional arguments. The script sources
`~/.local/bin/env` (added by the `uv` installer) so that `uv` is on `PATH`,
and then it can be extended to create a virtual environment under
`/opt/python-dev` and install the contents of `requirements.txt` into it.

> Hard-coding the venv name and Python version inline keeps this example
> simple. To make these values configurable at build time, see
> [`chapter_2/03`](../03), which uses the `ARG` instruction.

## 3. Building the image

The build command from the chapter:

```bash
docker build . -f Dockerfile -t rkrispin/chapter_2:v0.1.0
```

Argument-by-argument:

| Part                              | Meaning                                                                                          |
| --------------------------------- | ------------------------------------------------------------------------------------------------ |
| `docker build`                    | Invoke the Docker build engine.                                                                  |
| `.`                               | The **build context** — the directory whose files Docker can `COPY`/`ADD` into the image.        |
| `-f Dockerfile`                   | Path to the Dockerfile. Optional here because `Dockerfile` is the default name in the context.   |
| `-t rkrispin/chapter_2:v0.1.0`    | Tag the resulting image as `<user>/<repo>:<version>`. Useful for pushing to a registry later.    |

Run it from inside this folder:

```bash
cd chapter_2/02
docker build . -f Dockerfile -t rkrispin/chapter_2:v0.1.0
```

### Overriding values at build time

This example hard-codes the venv name (`python-dev`) and Python version
(`3.12.11`) directly in the Dockerfile. If you want to change them, edit
the file and rebuild.

For a version of the same Dockerfile where these values are declared as
**build-time arguments** (`ARG`) and can be overridden with
`--build-arg PYTHON_VER=...` etc., see [`chapter_2/03`](../03).

### Forcing a clean build

If a cached layer is hiding a problem (e.g. a previously silently-failed
`curl | sh`), bypass the cache:

```bash
docker build --no-cache . -f Dockerfile -t rkrispin/chapter_2:v0.1.0
```

### Suggested improvements to the build command

The command as written works, but a few small additions make it more
robust and explicit:

1. **Pin the platform** when building on Apple Silicon for a Linux/amd64
   target (or vice versa):

   ```bash
   docker build --platform=linux/amd64 . -f Dockerfile -t rkrispin/chapter_2:v0.1.0
   ```

2. **Add a `latest` tag** alongside the version tag so the most recent
   build is easy to reference:

   ```bash
   docker build . -f Dockerfile \
       -t rkrispin/chapter_2:v0.1.0 \
       -t rkrispin/chapter_2:latest
   ```

3. **Drop `-f Dockerfile`** — it is redundant when the file is named
   `Dockerfile` and lives in the build context root:

   ```bash
   docker build -t rkrispin/chapter_2:v0.1.0 .
   ```

## 4. Viewing and inspecting the image

Once the build finishes, the image is stored in your local Docker image
store. Docker exposes several commands for listing and inspecting images
and the containers created from them.

> **Heads up:** `docker ps` lists **containers**, not images. The image
> equivalent is `docker images` (alias: `docker image ls`). Both are
> covered below.

### 4.1 List images on your machine

```bash
docker images
# or, equivalently
docker image ls
```

Typical output:

```
REPOSITORY            TAG       IMAGE ID       CREATED         SIZE
rkrispin/chapter_2    v0.1.0    a1b2c3d4e5f6   2 minutes ago   612MB
ubuntu                22.04     5e7d8f9a0b1c   3 weeks ago     77.9MB
```

Useful variations:

| Command                                                   | What it does                                                                                |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `docker images rkrispin/chapter_2`                        | Show only tags of this repository.                                                          |
| `docker images --filter "reference=rkrispin/chapter_2:*"` | Same, using the explicit `--filter` form (supports glob patterns).                          |
| `docker images -q`                                        | Print only image IDs (handy for piping into other commands).                                |
| `docker images --no-trunc`                                | Do not truncate the image ID and other long fields.                                         |
| `docker images --digests`                                 | Show the content-addressable digest (`sha256:...`) for each image — useful for pinning.     |

### 4.2 Inspect the full image metadata

`docker inspect` (or `docker image inspect`) prints all metadata Docker
stores about the image as JSON:

```bash
docker inspect rkrispin/chapter_2:v0.1.0
```

The output includes the image's ID, parent, created date, OS/architecture,
config (`Env`, `Cmd`, `Entrypoint`, `WorkingDir`, `Labels`), the list of
filesystem layer digests, and more.

You usually only care about a couple of fields, which `--format` makes
easy by accepting a Go template:

| Command                                                                                                   | What it returns                                  |
| --------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `docker inspect --format '{{.Os}}/{{.Architecture}}' rkrispin/chapter_2:v0.1.0`                           | Image OS and CPU arch (e.g. `linux/arm64`).      |
| `docker inspect --format '{{.Config.Cmd}}' rkrispin/chapter_2:v0.1.0`                                     | The default command set in the image.            |
| `docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' rkrispin/chapter_2:v0.1.0`           | Environment variables baked into the image.      |
| `docker inspect --format '{{.Size}}' rkrispin/chapter_2:v0.1.0`                                           | Image size in bytes.                             |
| `docker inspect --format '{{.RootFS.Layers}}' rkrispin/chapter_2:v0.1.0`                                  | List of filesystem layer digests.                |

### 4.3 See how the image was built (layer history)

`docker history` shows each layer that makes up the image, in build order,
along with the command that produced it and the size it added:

```bash
docker history rkrispin/chapter_2:v0.1.0
```

Typical output (truncated):

```
IMAGE          CREATED         CREATED BY                                      SIZE
a1b2c3d4e5f6   2 minutes ago   RUN bash ./settings/install_uv.sh ...           120MB
<missing>      2 minutes ago   COPY install_uv.sh requirements.txt settings/   1.5kB
<missing>      2 minutes ago   RUN curl -LsSf https://astral.sh/ruff/...       18MB
<missing>      2 minutes ago   RUN curl -LsSf https://astral.sh/uv/install.sh  35MB
<missing>      2 minutes ago   RUN apt-get update && apt-get install -y ...    25MB
<missing>      3 weeks ago     /bin/sh -c #(nop)  CMD ["/bin/bash"]            0B
<missing>      3 weeks ago     /bin/sh -c #(nop) ADD file:... in /             77.9MB
```

This is the fastest way to spot oversized layers when you need to slim
the image. Add `--no-trunc` to see the full command for each layer.

### 4.4 List containers (running and stopped)

`docker ps` lists **containers**, not images:

```bash
docker ps           # only running containers
docker ps -a        # also include stopped containers
```

Typical output:

```
CONTAINER ID   IMAGE                         COMMAND       CREATED         STATUS         PORTS    NAMES
8f3a2b1c4d5e   rkrispin/chapter_2:v0.1.0     "bash"        10 seconds ago  Up 9 seconds            keen_curie
```

Useful variations:

| Command                                                                | What it does                                                |
| ---------------------------------------------------------------------- | ----------------------------------------------------------- |
| `docker ps -a`                                                         | Include stopped containers too.                             |
| `docker ps -q`                                                         | Only container IDs (handy for piping).                      |
| `docker ps --filter "ancestor=rkrispin/chapter_2:v0.1.0"`              | Only containers created from this image.                    |
| `docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'`       | A custom, easier-to-read column layout.                     |

### 4.5 Inspect a running container

The same `docker inspect` command works on container names/IDs and is the
go-to tool for debugging:

```bash
docker inspect chapter2-dev
docker inspect --format '{{.State.Status}}' chapter2-dev          # running / exited
docker inspect --format '{{.NetworkSettings.IPAddress}}' chapter2-dev
docker inspect --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}' chapter2-dev
```

Other quick container introspection commands:

| Command                                | What it shows                                                            |
| -------------------------------------- | ------------------------------------------------------------------------ |
| `docker logs chapter2-dev`             | Stdout/stderr from the container's main process.                         |
| `docker logs -f chapter2-dev`          | Same, but follow new log lines as they arrive.                           |
| `docker top chapter2-dev`              | Running processes inside the container.                                  |
| `docker stats chapter2-dev`            | Live CPU / memory / network / I/O usage.                                 |
| `docker diff chapter2-dev`             | Files changed in the container's writable layer vs. the image.           |
| `docker port chapter2-dev`             | Host-to-container port mappings published with `-p`.                     |

## 5. Running the image

After the build finishes, start a container from the image:

```bash
docker run --rm -it rkrispin/chapter_2:v0.1.0 bash
```

Argument-by-argument:

| Part                          | Meaning                                                                                                  |
| ----------------------------- | -------------------------------------------------------------------------------------------------------- |
| `docker run`                  | Create a new container from an image and start it.                                                       |
| `--rm`                        | Automatically delete the container's filesystem when it exits, so stopped containers don't pile up.      |
| `-i`                          | Interactive — keep STDIN open so the shell can read what you type.                                       |
| `-t`                          | Allocate a pseudo-TTY so the shell looks and behaves like a real terminal (prompt, colors, line editing). |
| `-it`                         | Just `-i` and `-t` combined — the conventional way to ask for an interactive terminal.                   |
| `rkrispin/chapter_2:v0.1.0`   | The image to run (built in section 3).                                                                   |
| `bash`                        | The command to run inside the container. Overrides the image's default `CMD`.                            |

Inside the container you can verify the tools are installed:

```bash
uv --version
ruff --version
```

## 6. Connecting to the container and testing the Python environment

> **Note on terminology:** people often say "SSH into a container", but
> containers do not run an SSH daemon by default and you do not need one.
> Docker provides two equivalent ways to get an interactive shell:
>
> - **`docker run -it ... bash`** — start a *new* container and attach to it.
> - **`docker exec -it <container> bash`** — attach to an *already-running*
>   container.
>
> Both give you the same kind of interactive shell SSH would, without
> opening any network ports.

### Option A — start a fresh container interactively

This is the most common workflow when you just want to poke around:

```bash
docker run --rm -it rkrispin/chapter_2:v0.1.0 bash
```

Argument-by-argument:

| Part                          | Meaning                                                                                       |
| ----------------------------- | --------------------------------------------------------------------------------------------- |
| `docker run`                  | Create and start a new container from an image.                                               |
| `--rm`                        | Delete the container automatically once you exit the shell, so it doesn't leave a stopped container behind. |
| `-i`                          | Interactive mode — keep STDIN open so you can type into the shell.                            |
| `-t`                          | Allocate a pseudo-TTY so prompts, colors, and line editing work correctly.                    |
| `rkrispin/chapter_2:v0.1.0`   | The image (and tag) to run.                                                                   |
| `bash`                        | Override the image's default command and run `bash` instead, giving you an interactive shell. |

Useful additions you may want later:

- `-v $(pwd):/work -w /work` — bind-mount the current host directory into
  `/work` inside the container so edits on the host are visible inside.
- `-p 8888:8888` — publish a container port to the host (handy for Jupyter).
- `--name chapter2-dev` — give the container a stable name instead of a
  random one (cannot be combined with `--rm` if you also want to restart it).

### Option B — exec into a long-running container

If the container is already running (for example as a dev container):

```bash
# 1. Start it in the background and give it a name
docker run -d --name chapter2-dev rkrispin/chapter_2:v0.1.0 sleep infinity

# 2. Open a shell inside it
docker exec -it chapter2-dev bash

# 3. When you are done
docker stop chapter2-dev && docker rm chapter2-dev
```

Argument-by-argument:

**Step 1 — `docker run -d --name chapter2-dev rkrispin/chapter_2:v0.1.0 sleep infinity`**

| Part                          | Meaning                                                                                          |
| ----------------------------- | ------------------------------------------------------------------------------------------------ |
| `-d`                          | Detached mode — start the container in the background and return immediately.                    |
| `--name chapter2-dev`         | Assign a stable, human-friendly name so you can refer to it later without looking up its ID.     |
| `rkrispin/chapter_2:v0.1.0`   | The image to run.                                                                                |
| `sleep infinity`              | A no-op foreground command that keeps the container alive. Containers exit when their main process exits, so without something to run, the container would stop immediately. |

**Step 2 — `docker exec -it chapter2-dev bash`**

| Part              | Meaning                                                                          |
| ----------------- | -------------------------------------------------------------------------------- |
| `docker exec`     | Run a command inside an *already-running* container (does not start a new one).  |
| `-i`              | Keep STDIN open so the shell is interactive.                                     |
| `-t`              | Allocate a pseudo-TTY for the shell.                                             |
| `chapter2-dev`    | The target container's name (or ID).                                             |
| `bash`            | The command to run inside the container — here, an interactive Bash shell.       |

You can `docker exec` into the same container as many times as you want
(e.g. from multiple terminal tabs).

**Step 3 — `docker stop chapter2-dev && docker rm chapter2-dev`**

| Part                          | Meaning                                                                                       |
| ----------------------------- | --------------------------------------------------------------------------------------------- |
| `docker stop chapter2-dev`    | Send SIGTERM (then SIGKILL after a grace period) to the container's main process to stop it.  |
| `&&`                          | Shell operator — only run the next command if the previous one succeeded.                     |
| `docker rm chapter2-dev`      | Delete the stopped container's filesystem (without `--rm`, stopped containers stick around).  |

### Verifying the toolchain

Once you have a shell inside the container, run:

```bash
# uv was installed by the Astral installer into /root/.local/bin
uv --version
ruff --version
which uv
which ruff
```

If `uv` or `ruff` is reported as "command not found", `~/.local/bin` is not
on your `PATH`. Either source the env file the installer dropped:

```bash
source $HOME/.local/bin/env
```

…or, better, bake the path into the image by adding this line to the
Dockerfile after the installers run:

```dockerfile
ENV PATH="/root/.local/bin:${PATH}"
```

### Verifying the Python virtual environment

The helper script `install_uv.sh` is intended to create a virtual
environment at `/opt/python-dev` and install `requirements.txt` into it.
Once those lines in the script are active, you can verify the venv from
inside the container like this:

```bash
# 1. The venv directory should exist
ls /opt/python-dev

# 2. Activate it
source /opt/python-dev/bin/activate

# 3. Confirm Python is the expected version and is coming from the venv
python --version           # -> Python 3.12.11
which python               # -> /opt/python-dev/bin/python

# 4. Confirm the packages from requirements.txt are installed
uv pip list                # should include pandas==2.2.2
python -c "import pandas; print(pandas.__version__)"   # -> 2.2.2

# 5. Quick end-to-end smoke test
python - <<'PY'
import sys, pandas as pd
print("python:", sys.version.split()[0])
print("pandas:", pd.__version__)
print(pd.DataFrame({"x": [1, 2, 3]}).describe())
PY
```

Expected output of the smoke test:

```
python: 3.12.11
pandas: 2.2.2
              x
count  3.000000
mean   2.000000
std    1.000000
min    1.000000
25%    1.500000
50%    2.000000
75%    2.500000
max    3.000000
```

If any of the steps above fail, the most common causes are:

| Symptom                                            | Likely cause                                                                 |
| -------------------------------------------------- | ---------------------------------------------------------------------------- |
| `ls /opt/python-dev` → no such file or directory   | The `uv venv ...` line in `install_uv.sh` is still commented out.            |
| `pandas` not found                                 | The `uv pip install -r ./settings/requirements.txt` line is commented out.   |
| `uv: command not found` after `docker run`         | `~/.local/bin` is not on `PATH` — see the `ENV PATH=...` tip above.          |
| `uv venv` fails with a Python download error       | The container has no network, or `curl`/CA certs were not installed.        |
