# Chapter 2 — Lesson 1: The Docker Workflow

In the previous chapter, we discussed why containers matter and reviewed the container strategy for our RAG application.

Before we start writing our first Dockerfile, we need to understand the overall Docker workflow.

This lesson is meant to give you the big picture, so that when we zoom into the details in the following lessons, you already know how the pieces connect.

[CLICK]

The Docker workflow has four main steps:

* Requirements
* Dockerfile
* `docker build`, and
* `docker run`

Let's walk through each one.

[CLICK]

Step one — requirements.

Before we write any Docker code, we need to know what our application needs to run.

For example, if we want to containerize the query pipeline of our RAG application, we may need:

* A specific Python version, such as Python 3.11
* A set of Python libraries listed in a requirements file
* System dependencies such as `curl` or `git`
* Environment variables for API keys, and
* A port to expose the API service

This step is often skipped, but it is the most important one. The clearer the requirements, the cleaner the Dockerfile.

[CLICK]

Step two is the Dockerfile.

A Dockerfile is a plain text file that translates those requirements into instructions Docker can follow.

It tells Docker:

* Which base image to start from
* Which files to copy into the image
* Which commands to run during the build, and
* Which command to execute when the container starts

We can think of a Dockerfile as a recipe, and the image as the cake.

[CLICK]

The next step is building the image.

Once we have a Dockerfile, we run the `docker build` command.

Docker reads the file from top to bottom and executes each instruction, creating a dedicate layer for most of them.

The final stack of layers is the image. The image is a read-only snapshot that contains everything the application needs to run.

Images are immutable. If we need to change something, we update the Dockerfile and build a new image.

[CLICK]

Last but not least is the `docker run` command.

The image is just a template. To actually execute our application, we use the `docker run` command.

This creates a container from the image. A container is a running instance of the image, with its own filesystem, network interface, and isolated process space.

We can run multiple containers from the same image, just like we can launch many instances of a program from the same executable file.

[CLICK]

This four-step workflow is repeated every time we change the application.

When we update the code or change a dependency, we update the relevant requirements, the Dockerfile if needed, rebuild the image, and run a new container.

Over time, this loop becomes very fast, because Docker uses a sophisticated caching system which we will discuss later on in the course.

[CLICK]

The important takeaway from this lesson is that every container starts from clear requirements and follows the same path:

Dockerfile → `docker build` → `docker run`.

In the next lessons, we will zoom into each of these steps. We will start with the Dockerfile, then look at `docker build` in detail, then `docker run`, and finally cover best practices for setting and running containers.
