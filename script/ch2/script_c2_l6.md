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

Adding the `-a` shows all containers, including stopped ones. This is important, because by default `docker run` does not delete the container when it exits. Stopped containers sit around until we remove them.

`docker images` shows all images stored locally, along with their tag and size.

These two commands give us a snapshot of what is on our machine right now.

[CLICK]

Next, **looking inside a container**.

`docker logs <name>` prints everything the container wrote to Standard Output and Standard Error. We use this to find out why a container crashed or what an app is doing.

The `-f` follows the log output in real time, similar to `tail -f` on a regular log file.

`docker exec` enables us to open an interactive shell *inside* a running container. This is one of the most useful debugging commands in Docker. We can move around the filesystem, check installed packages, and see what the app sees.

`docker inspect` prints a large JSON document with every detail about the container: its mounts, its environment variables, its network, and the command it is running. We can pipe it through `jq` to extract specific fields.

[CLICK]

Then, there is the **lifecycle commands**.

`docker stop` sends a polite shutdown signal. Docker waits up to 10 seconds for the container to stop gracefully. If it is still running after that, Docker forces it to stop.

`docker start <name>` starts a stopped container again with the same configuration.

`docker restart <name>` is stop + start in one step.

`docker rm <name>` removes a stopped container. Add `-f` to remove a running container. And,

`docker rmi <image>` removes an image. 

[CLICK]

Finally, let’s look at cleanup.

As we build images and run containers, Docker resources start to accumulate. Old containers, unused images, and build cache can consume a significant amount of disk space over time.

A good place to start is with docker ps -a and docker images, which show all containers and images currently on the system.

To get a quick storage summary, use docker system df. It reports how much disk space is being used by images, containers, volumes, and the build cache.

When it’s time to clean up, docker container prune removes all stopped containers, while docker image prune removes dangling images.

Adding the -a flag to docker image prune removes all images that are not being used by at least one container.

For a more thorough cleanup, docker system prune removes unused containers, networks, and dangling images in a single command. Adding -a --volumes also removes unused images and volumes. This can free up a substantial amount of disk space, but use it carefully since the changes cannot be undone.

[CLICK]

A short list of commands worth memorizing:

* `docker ps -a` — returns what containers exist.
* `docker images` — what images exist.
* `docker logs -f <name>` — what is the container doing.
* `docker exec -it <name> bash` — enables us to ssh the container for debugging and testing
* `docker stop` and `docker rm` — shut down and clean up. Last but not least, 
* `docker system prune` — reclaim disk space.

The README for this lesson has the full reference, sample output, and a cheat sheet you can keep open while working.

In the next lesson — the last in this chapter — we will look at Dockerfile **best practices**.