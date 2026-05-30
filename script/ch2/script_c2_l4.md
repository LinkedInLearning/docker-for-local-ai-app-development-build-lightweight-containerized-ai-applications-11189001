# Chapter 2 — Lesson 4: Working with Registries

In the previous lesson, we built an image and it landed in our **local** image store. That is fine for our own machine — but a teammate, a server, or a CI pipeline cannot see it there.

This lesson is about sharing images through a **registry**.

[CLICK]

A registry is a service that stores and distributes images. We already been using one without thinking about it.

The image we built in the previous lesson uses  the `python:3.11-slim` image. During the build time, if the image is not available locally, Docker **pulls** that base image from a registry. By default, that registry is **Docker Hub** — the public registry Docker uses unless you tell it otherwise.

[CLICK]

We can specifically pull an image with the docker pull command. For example, this is how we pull the python slim image from docker hub using the docker pull command followed with the image name - python:3.11-slim

```bash
docker pull python:3.11-slim
```

This downloads the image and its layers into our local store, ready to use.

[CLICK]

To understand pushing, we first need to understand how images are **named**.

A full image reference looks like this:

```text
docker.io/library/python:3.11-slim
└─ registry ┘└ namespace ┘└ repo ┘└ tag ┘
```

When you type `python:3.11-slim`, Docker fills in the defaults: the `docker.io` registry and the `library` namespace that holds official images. To push your *own* image, the namespace must be **your Docker Hub username**.

[CLICK]

So sharing an image is three steps: **log in**, **tag**, **push**.

First, log in to Docker Hub using:

```bash
docker login
```

This prompts for your Docker Hub username and a password or access token, and stores the credentials locally.

[CLICK]

Next, **tag** the local image with your namespace. Tagging does not copy the image — it adds a reference point to the same image. For example, this docker tag command add to the demo:0.1 image the user name as a point of reference.

```bash
docker tag demo:0.1 myuser/demo:0.1
```
The second name - myuser/demo:0.1 is the one a registry will accept.

[CLICK]

Lastrly, we will use the docker **push** command to push the image to the image registry.

```bash
docker push myuser/demo:0.1
```

Docker uploads each layer that the registry does not already have. Layers it already has are skipped — the same caching idea we saw with builds, now over the network.

[CLICK]

The image now lives on Docker Hub. On any other machine — a colleague's laptop, a server, a CI runner — it can be pulled using the docker pull command followed by the image reference:

```bash
docker pull myuser/demo:0.1
```

That round trip, push here and pull there, is how an image travels from your machine to where it actually runs.

[CLICK]

Two things worth knowing before we move on.

A repository can be public or private. Public images can be pulled by anyone, while private images require authentication.

Tags are also important. If you push an image without specifying a version, for example,  myuser/demo, Docker set a default tag as latest. This tag is convenient, but not reliable for real use cases because it can change without notice. We’ll revisit tagging strategies later when we prepare images for production.


[PAUSE, SKIP TO LAST SLIDE]

That is the typical workflow: pull base images, build on top of it and tag it with your own namespace, push to share, pull to deploy.

In the next lesson, we will learn how to run images with the `docker run` command.



[CLICK]

---

> **🎬 LIVE DEMO — pivot to the VS Code terminal.**
> Switch to VS Code and open the integrated terminal. We'll pull a base image,
> then push the `demo:0.1` image we built in Lesson 3 up to Docker Hub. Use your
> own Docker Hub username in place of `myuser`, and have a browser tab ready on
> hub.docker.com.

Let's do this live. First, let's pull a base image on its own, to see a registry pull by itself:

```bash
docker pull python:3.11-slim
```

Docker contacts Docker Hub and downloads the image and its layers into our local store. If we already have it, it simply reports the image is up to date.

Now let's share our *own* image — the `demo:0.1` image we built last lesson. Three steps: log in, tag, push.

First, log in:

```bash
docker login
```

I'll enter my Docker Hub username and an access token — use a token rather than your password; it's revocable.

Next, tag the local image with my namespace — my Docker Hub username in place of `myuser`:

```bash
docker tag demo:0.1 myuser/demo:0.1
```

And push it:

```bash
docker push myuser/demo:0.1
```

Docker uploads each layer the registry doesn't already have, skips the ones it does, and prints the digest when it finishes.

Now let's confirm it landed.

> **[SWITCH TO BROWSER]** Open `https://hub.docker.com/r/myuser/demo` (your username in place of `myuser`).

There it is — the `demo` repository, the `0.1` tag we just pushed, the image size, and when it was last updated. Anyone with access can now run `docker pull myuser/demo:0.1` and get exactly this image.

Back to the slides.

---

[CLICK]

That is the whole everyday workflow: pull base images, tag your own with your namespace, push to share, pull to deploy.

In the next lesson, we go back to running images — the `docker run` command and the flags you will use every day.
