# Chapter 2 — Lesson 7: Dockerfile best practices

So far in this chapter we have built, run, and managed our first containers. To close the chapter, we will look at how to write Dockerfiles that are smaller, faster to build, and easier to maintain.

[CLICK]

The first best practice is to **pin versions**.

A Dockerfile that starts with `FROM python` may build today but break tomorrow when `python:latest` moves to a new version. We always pin a specific tag, such as `python:3.11-slim` for full reproducibility.

The same applies to packages installed inside the image. Pin them in a requirements file or with explicit versions.

[CLICK]

The second best practice is to **order instructions for cache efficiency**.

Docker caches each layer. As soon as one instruction changes, every instruction after it is rebuilt.

Put the things that change rarely at the top of the Dockerfile, and the things that change often at the bottom. 

For example, the dockerfile on the right side copy the application code at the end as it changes most often.

The dependency install layer stays cached as long as `requirements.txt` is unchanged.

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

[CLICK]

The third best practice is to **use `ARG` and `ENV` deliberately**.

`ARG` values are available only during the build, and are perfect for tool versions or feature flags. Combine `ARG` with the `build-arg` to override them from the command line.

`ENV` values persist into the running container, which is what we want for runtime configuration such as paths or feature toggles.

In our RAG project, the development Dockerfile assigns the args as environment variable to make them available after the build time. 

```dockerfile
ARG PYTHON_VER="3.11"
ENV PYTHON_VER=$PYTHON_VER
```

[CLICK]

The fourth best practice is to **combine related commands into a single `RUN`**.

Every `RUN` creates a new layer. Splitting an install into many RUN instructions could potentially increases the image size.

 Combine them with double ampersand (`&&`) and clean up in the same layer:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
```

This installs `curl`, then cleans up the apt cache, all in one layer. If we cleaned up in a separate `RUN`, the cache would still live inside the previous layer and inflate the image.

[CLICK]

The fifth best practice is to **move complex setup into shell scripts**.

When a `RUN` instruction grows beyond a few lines, it becomes hard to read. Move it into a script, copy the script into the image, and call it from a single `RUN`:

```dockerfile
COPY install_dependencies.sh settings/
RUN bash ./settings/install_dependencies.sh
```

This is exactly what we do in our RAG project for installing system dependencies and `uv`. The Dockerfile stays clean and the script is easy to test in isolation.

[CLICK]

The sixth best practice is to **use a `.dockerignore` file**.

Files like `.git`, virtual environments, and caches do not belong in the image. Excluding them from the build context shrinks the image and speeds up the build.

[CLICK]

The seventh best practice is to **run as a non-root user when possible**.

Production containers should not run as root. Create a dedicated user and switch it:

```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

[CLICK]

The eighth best practice is to **keep secrets and data out of the image**.

Never bake API keys, passwords, or credentials into a Dockerfile or copy a `.env` file into the image. 


Image layers are cached, shared, and pushed to registries, and anyone who has the image can read them back with `docker history`. The same applies to application data: an image is a static, shareable artifact, not a place to store data.

Instead, pass secrets at **runtime** and keep data in **mounted volumes**:

```bash
docker run -e OPENAI_API_KEY --env-file .env -v "$PWD/data:/app/data" my-image
```

And let `.dockerignore` exclude files like `.env`, so a secret can't slip into the build context in the first place.

[CLICK]

A few more habits worth adopting:

* Prefer `COPY` over `ADD` unless we need URL fetching or tar extraction.
* Use the exec form of `CMD` and `ENTRYPOINT` so signals are forwarded correctly.
* Add a `HEALTHCHECK` so Docker knows when the container is actually ready.
* Add `LABEL` metadata to make images easier to inspect.

[CLICK]

The Dockerfiles we built in this chapter are intentionally simple. As our application grows, these practices keep our images small, our builds fast, and our containers safe to run in production.

This concludes Chapter 2. In the next chapter, we will return to our RAG project and start applying everything we learned here to build the development environment.
