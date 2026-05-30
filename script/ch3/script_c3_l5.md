# Chapter 3 — Lesson 5: Development Environment Best Practices

We have a working prototype: a multi-container environment, an editor wired into it, and a development loop that runs against the real database. This final lesson of the chapter steps back to cover the practices that keep that environment **maintainable** as the project grows.

Four habits, all of which our RAG project already follows.

[CLICK]

**First: version your images with meaningful tags.**

An image without a version is a moving target. `latest` today is not `latest` next week, and "it worked yesterday" becomes impossible to reproduce.

Give every image a real tag — `python-dev-rag-docker:0.0.3` — and bump it deliberately when the environment changes. 

A new dependency or a base-image change earns a new tag. 

The tag becomes a pin: a teammate, a CI job, or your future self can pull that exact environment and get exactly what you had.

[CLICK]

**Second: script your builds.**

The build commands grow long — platforms, build args, tags, a push at the end. Typing that by hand is error-prone and undocumented. So we put it in a shell script.

```bash
# docker/build_dev_docker.sh
docker buildx build . -f Dockerfile_Dev \
  --platform linux/amd64,linux/arm64 \
  --build-arg PYTHON_VER=3.11 \
  --build-arg VENV_NAME=python-3.11-dev \
  -t rkrispin/python-dev-rag-docker:0.0.3
```

The script is the documentation of how the image is built. The image settings — name, tag, versions — live at the top as variables, so bumping a version is a one-line edit. Anyone can rebuild the exact image without knowing the full set of commands.

[CLICK]

**Third — and this is the big one: split the build into a base image and a dev image.**

Remember the stability tiers from Lesson 1. Some things almost never change — the OS, system tools, the Python toolchain. Other things change with the project — its dependencies and code. Put those in two separate images.

[CLICK]

The **base image** carries the stable, project-agnostic foundation.

In our repo that's base Dockerfile which include the Ubuntu, system dependencies, and the shell setup. It's built once, tagged, and pushed to a registry. It rarely changes.

```dockerfile
# docker/Dockerfile_Base
FROM ubuntu:22.04
RUN bash ./settings/install_dependencies.sh
RUN bash ./settings/install_quarto.sh $QUARTO_VER
```

[CLICK]

The **dev image** builds `FROM` that base and adds only the project-specific pieces — the Python environment and specific project's models and tooling.

```dockerfile
# docker/Dockerfile_Dev
FROM docker.io/rkrispin/python-base:0.0.4
COPY install_uv.sh requirements.txt settings/
RUN bash ./settings/install_uv.sh $VENV_NAME $PYTHON_VER $RUFF_VER
```

The win: when a dependency changes, we rebuild only the thin dev image on top of the already-built base. We never reinstall the OS and system tools just to add a Python package. The expensive, stable work is done once.

[CLICK]

**Fourth: start new projects from a template.**

Once you've built a good containerized setup — the Dockerfiles, the build scripts, the Compose file, the `devcontainer.json` — you don't want to recreate it from scratch every time.

Set a template using tools such as **GitHub template repository**. A new project starts as a copy of the template, already wired for containerized development. You change the project name and dependencies, and run the build, instead of rebuild the whole setup.

[CLICK]

Put together, these four habits make the environment durable: tagged images you can reproduce, scripted builds you can rerun, a base/dev split that keeps rebuilds cheap, and a template that makes the next project start where this one finished.

That closes Chapter 3. We've taken our RAG application from idea to a working prototype, developed entirely inside containers.

In Chapter 4, we move from prototyping to **testing** — splitting the prototype into dedicated, containers and running them in an environment close to production.
