# Chapter 2 — Lesson 3: `docker build`

In the previous lesson, we learned about the Dockerfile and the core instructions used to define an image.

Now we will take that Dockerfile and turn it into a real image using the `docker build` command.

[CLICK]

The basic syntax is simple:

```bash
docker build -t my-image:0.1 .
```

Three things are happening here. Let's break them down.

[CLICK]

First, the dot at the end. That is the **build context**.

The build context is the folder Docker sends to the build engine. Every file Docker copies into the image must live inside the context. If we type a dot, Docker uses the current directory.

Anything outside the context cannot be referenced with `COPY` or `ADD`. This is also a good reason to keep the context small. A large context slows down the build and inflates image size.

To exclude files from the context, we use a `.dockerignore` file. It works like `.gitignore` and is one of the easiest ways to speed up a build.

[CLICK]

Second, the `-t` flag. This **tags** the image with a name and an optional version, like `my-image:0.1`. Without a tag, the image is hard to reference later. If we omit the version, Docker assumes `latest`, which is rarely what we want.

[CLICK]

Third, the Dockerfile itself. By default, `docker build` looks for a file named `Dockerfile` in the build context. If we use a different name, such as `Dockerfile_API`, we tell Docker about it with the `-f` flag:

```bash
docker build -f docker/Dockerfile_API -t rag-api:0.1 .
```

[CLICK]

When we run `docker build`, Docker reads the Dockerfile top to bottom and creates a new layer for most instructions.

A layer is a read-only filesystem change. Each `RUN`, `COPY`, and `ADD` typically adds one layer. The final image is the stack of those layers.

[CLICK]

Layers are not just an implementation detail. They drive **build caching**.

If we run `docker build` a second time, Docker compares each instruction to the previous build. If nothing changed up to a given line, Docker reuses the cached layer instead of rebuilding it.

This is why the order of instructions matters. If we copy our application code *before* installing dependencies, every code change invalidates the dependency installation layer, and we wait for `pip` to reinstall everything.

[CLICK]

We can also pass build arguments from the command line using `--build-arg`. For example, our project's build script uses this to override the Python version:

```bash
docker build --build-arg PYTHON_VER=3.11 -t my-image:0.1 .
```

This works for any `ARG` declared in the Dockerfile.

[CLICK]

Other flags worth knowing:

* `--no-cache` forces Docker to rebuild every layer from scratch — useful when debugging cache problems.
* `--progress=plain` shows the full build output instead of the compact view.
* `--platform` builds for a specific architecture, such as `linux/amd64` or `linux/arm64`.

[CLICK]

Once the build finishes, the image lives in our local Docker registry. We can list it with `docker images` and inspect its layers with `docker history`.

The image is now ready to run.

In the next lesson, we will look at how to share that image beyond our own machine — pulling and pushing images to a registry like Docker Hub.
