# Chapter 2 — Lesson 6: Managing containers and images

In the previous lessons, we learned how to build images and run containers.

As we work with Docker, our machine gradually accumulates images, containers, volumes, and networks. Some containers are running, others have stopped, and some resources are no longer needed but still consume disk space.

In this lesson, we'll cover a set of useful Docker CLI commands for listing, inspecting, debugging, and cleaning up these resources.

[CLICK]

Docker manages four main types of objects:

* **Images** — read-only templates that we build or pull from a registry.
* **Containers** — running or stopped instances of an image.
* **Volumes** — persistent storage attached to containers.
* **Networks** — virtual networks that allow containers to communicate with each other.


Each one has its own family of commands that follow the same pattern: `list`, `inspect`, `remove`, `prune`.

In this lesson we focus on the two we touch most often: images and containers.

[CLICK]

Let's start with **listing things**.

`docker ps` shows running containers.

`docker ps -a` shows all containers, including stopped ones. This is important, because by default `docker run` does not delete the container when it exits. Stopped containers sit around until we remove them.

`docker images` shows all images stored locally, along with their tag and size.

These two commands give us a snapshot of what is on our machine right now.

[CLICK]

Next, **looking inside a container**.

`docker logs <name>` prints everything the container wrote to Standard Output and Standard Error. We use this to find out why a container crashed or what an app is doing.

`docker logs -f <name>` follows the log output in real time, similar to `tail -f` on a regular log file.

`docker exec -it <name> bash` opens an interactive shell *inside* a running container. This is one of the most useful debugging commands in Docker. We can move around the filesystem, check installed packages, and see what the app sees.

`docker inspect <name>` prints a large JSON document with every detail about the container: its mounts, its environment variables, its network, the command it is running. We pipe it through `jq` to extract specific fields.

[CLICK]

Then, **lifecycle commands**.

`docker stop <name>` sends a polite shutdown signal. After 10 seconds, if the container has not exited, Docker forces it to.

`docker start <name>` starts a stopped container again with the same configuration.

`docker restart <name>` is stop + start in one step.

`docker rm <name>` removes a stopped container. Add `-f` to remove a running container.

`docker rmi <image>` removes an image. Docker refuses if any container, even a stopped one, is still using it.

[CLICK]

Finally, **cleaning up**.

Disk usage adds up quickly. Every build leaves behind dangling layers, and every run leaves a stopped container.

`docker ps -a` and `docker images` are the first step. They show what is there.

`docker system df` summarizes how much disk space images, containers, volumes, and the build cache are using.

`docker container prune` removes all stopped containers.

`docker image prune` removes dangling images. Adding `-a` removes every image not used by at least one container.

`docker system prune` removes containers, networks, and dangling images in one shot. Adding `-a --volumes` also removes unused images and volumes — powerful, but irreversible.

[CLICK]

A short list of commands worth memorizing:

* `docker ps -a` — what containers exist.
* `docker images` — what images exist.
* `docker logs -f <name>` — what is the container doing.
* `docker exec -it <name> bash` — get inside.
* `docker stop` / `docker rm` — shut down and clean up.
* `docker system prune` — reclaim disk space.

The README for this lesson has the full reference, sample output, and a cheat sheet you can keep open while working.

In the next lesson — the last in this chapter — we will look at Dockerfile **best practices**: how to write Dockerfiles that produce smaller, faster, and safer images.
