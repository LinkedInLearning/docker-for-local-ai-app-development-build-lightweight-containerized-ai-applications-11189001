# Chapter 2 — Lesson 3: `docker build`

In the previous lesson, we learned about the Dockerfile and the core instructions used to define an image.

Now we will take that Dockerfile and turn it into a real image using the `docker build` command.

[CLICK]

The basic syntax is simple - docker build followed by some arguments. Here is a simple example:

```bash
docker build -t my-image:0.1 .
```

Three things are happening here. Let's break them down.

[CLICK]

First, the dot at the end. That is the **build context**.

The build context is the local folder reference to the build engine. Every file Docker copies into the image must live inside the context. If we type a dot, Docker uses the current directory.

Anything outside the context cannot be referenced with the `COPY` or `ADD` commands. This is also a good reason to keep the context small. A large context slows down the build and inflates image size.

To exclude files from the context, we use a `.dockerignore` file. It works exactly like `.gitignore` file and is one of the easiest ways to speed up a build.

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

Layers are not just an implementation detail. They are the foundation of Docker’s build cache.

When we run docker build again, Docker compares each instruction to the previous build. If nothing changed up to a certain step, Docker reuses the cached layer instead of rebuilding it.

This is why the order of instructions is important. For example, if we copy the application code before installing dependencies, even a small code change will invalidate the dependency layer. As a result, Docker will reinstall all Python packages during the next build, which can significantly slow down the process.

[CLICK]

We can also pass build arguments from the command line using the `build-arg` argument. For example, our project's build script uses this to override the Python version:

```bash
docker build --build-arg PYTHON_VER=3.11 -t my-image:0.1 .
```

This works for any `ARG` declared in the Dockerfile.

[CLICK]

Other flags worth knowing:

* `--no-cache` forces Docker to rebuild every layer from scratch — useful when debugging cache problems.
* `--progress=plain` shows the full build output instead of the compact view, and
* `--platform` builds for a specific architecture, such as `linux/amd64` or `linux/arm64`. This argument is critical when working with multiple environment and we will dive into it later on in the course. 

[CLICK]

---

> **🎬 LIVE DEMO — pivot to VS Code.**
> Leave the slides on this "Live demo" cue. Switch to VS Code with this
> lesson's `chapter_2/l3/Dockerfile` open on the **left** (copied from Lesson 2,
> together with `main.py` and `requirements.txt`) and an integrated terminal
> open on the **right**, with its working directory set to `chapter_2/l3`.

Now let’s see this in practice — I'll switch over to VS Code.

On the left side, we have the Dockerfile we wrote in lesson 2. The file is under the chapter_2/l3 folders in the course repository. and on the right side we have the terminal opened in the same folder 

On the left is the Dockerfile we wrote in Lesson 2 — the same seven instructions, copied into this lesson's folder. On the right is a terminal, opened in that same folder.

I'll run the build command we just walked through:

```bash
docker build -t chapter_2:lesson_3 .
```

Watch the output. Docker prints **one step per instruction** — `[1/6] FROM…`, `[2/6] WORKDIR…`, `[3/6] COPY…`, and so on. Each of those lines maps directly to a line in the Dockerfile on the left, and each one becomes a **layer** in the image. The `RUN pip install` step is the slow one — that's where Docker actually downloads and installs our dependencies. When it's done, Docker prints `exporting to image` and the final image ID.

*(Optional — reinforces the cache slide.)* Let me run the **exact same command** again:

```bash
docker build -t demo:0.1 .
```

This time almost every step says `CACHED`. Nothing changed, so Docker reuses the layers from the first build and finishes in a fraction of a second — that's the layer cache in action.

Finally, let's confirm the image is really there:

```bash
docker images
```

That lists **`demo`** with tag **`0.1`**, its image ID, and its size — the artifact we just built, now sitting in our local image store, ready to run. (`docker ps`, by contrast, lists *running containers* — we have none yet, and that's exactly what the next lesson, `docker run`, is about.)

Now I'll switch back to the slides.

---

[CLICK]

Once the build finishes, the image lives in our local Docker registry. We can list it with `docker images` and inspect its layers with `docker history`.

The image is now ready to run.

In the next lesson, we will look at how to share that image beyond our own machine — pulling and pushing images to a registry like Docker Hub.
