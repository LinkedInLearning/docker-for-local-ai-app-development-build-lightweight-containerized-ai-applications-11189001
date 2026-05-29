# Chapter 2 — Lesson 2: Core Dockerfile Commands

In the previous lesson, we walked through the Docker workflow at a high level. Now it is time to zoom into the first artifact we write — the Dockerfile.

[CLICK]

A Dockerfile is a plain text file that tells Docker how to build an image.

It has no extension and is usually called `Dockerfile`, but we can give it a custom name such as `Dockerfile_API` or `Dockerfile_Dev`. This is useful when a project needs more than one image, which is exactly what we do in our RAG project.

[CLICK]

Docker reads the file top to bottom and runs each instruction in order. Most instructions produce a new layer in the resulting image.

A typical Dockerfile follows a predictable shape:

* Start from a base image
* Define build-time arguments and environment variables
* Set a working directory
* Install system packages
* Copy application files
* Install the application dependencies
* Declare the runtime command

[CLICK]

Let's look at the core instructions you will use most often.

[CLICK]

`FROM` is the first non-comment line of almost every Dockerfile. It selects the base image. For example, `python:3.11-slim` gives us a small Linux image with Python 3.11 already installed.

[CLICK]

`RUN` executes a command during the build. We use it to install packages, run scripts, or perform any setup that needs to be baked into the image.

[CLICK]

`COPY` copies files from our project folder into the image. This is how the application code and configuration get into the container.

[CLICK]

`WORKDIR` sets the current directory for the instructions that follow. Think of it as a persistent `cd` command.

[CLICK]

`ENV` defines an environment variable that will be available both during the build and inside the running container.

`ARG`, on the other hand, defines a variable that is only available during the build. We use it for things like tool versions or feature flags that we want to override from the command line.

[CLICK]

`EXPOSE` documents the port the application listens on. It does not publish the port — that happens at run time — but it tells consumers of the image what to expect.

[CLICK]

Finally, `CMD` declares the default command that runs when the container starts. If no command is provided to `docker run`, this is what executes.

[CLICK]

Let's see how these instructions look together. Here is a minimal Dockerfile for a Python application:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python", "main.py"]
```

Seven lines, and we have a fully reproducible recipe for our application.

[CLICK]

Notice the order. We copy and install the requirements *before* we copy the rest of the code. This is intentional. Docker caches each layer, so as long as the requirements file does not change, this expensive install step is skipped on the next build. We will explore this in more depth in the best-practices lesson.

[CLICK]

The README that accompanies this lesson contains a full reference for every Dockerfile instruction, when to use each one, and a few common points of confusion such as `CMD` versus `ENTRYPOINT` and `ARG` versus `ENV`.

For now, the takeaway is simple: a Dockerfile is a short, ordered list of instructions that describes how to build the environment our application needs.

In the next lesson, we will take a Dockerfile and run `docker build` to turn it into an actual image.
