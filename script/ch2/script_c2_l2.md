# Chapter 2 — Lesson 2: Core Dockerfile Commands

In the previous lesson, we walked through the Docker workflow at a high level. Now it is time to zoom into the first artifact we write — the Dockerfile.

[CLICK]

A Dockerfile is a plain text file that tells Docker how to build an image.

A Dockerfile usually has no file extension and is typically named Dockerfile. However, we can also use custom names such as Dockerfile_API or Dockerfile_Dev. This is useful when a project requires multiple images, which is exactly what we do in our RAG application.

[CLICK]

Docker reads the file from top to bottom and executes each instruction in order. Most instructions create a new layer in the final image.

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

`FROM` is the first dockerfile command of almost every Dockerfile. It selects the base image. For example, `python:3.11-slim` gives us a small Linux image with Python version 3.11 already installed.

[CLICK]

`RUN` executes a command during the build. We use it to install packages, run scripts, or perform any setup that needs to be baked into the image.

[CLICK]
Next is 
`COPY`, which as the name implies, it enables us to copy files from our project folder into the image. This is how the application script and configuration files get into the container.

[CLICK]

`WORKDIR` sets the current directory for the instructions that follow. Think of it as a persistent `cd` command.

[CLICK]

`ENV` defines an environment variable that will be available both during the build and inside the running container.

`ARG`, on the other hand, defines a variable that is only available during the build. We use it for things like tool versions or feature flags that we want to override from the command line.

[CLICK]

`EXPOSE` documents the port the application listens on. It does not publish the port — that happens at run time — but it tells the end users of the image what to expect.

[CLICK]

Finally, `CMD` declares the default command that runs when the container starts. If no command is provided to `docker run`, this is what executes.

[CLICK]

Let’s see how these instructions work together. Here is a minimal Dockerfile for containerizing a FastAPI Python application.

The Dockerfile starts by using a slim Python image as the base with the `FROM` command and sets the app folder as the working directory. It then copies the `requirements.txt` file into the image and uses the pip command to install the required Python libraries with the `RUN` command.

Next, it uses the `COPY` command again to add the Python application files to the image file system.

Finally, it exposes port 8080 and defines the command used to launch the FastAPI application.


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

If you would like to learn more about Dockerfile instructions, I recommend checking the README file included with this lesson. It contains a full reference of the most common Docker commands and when to use them.

For now, the takeaway is simple: a Dockerfile is a short, ordered list of instructions that describes how to build the environment our application needs.

In the next lesson, we will take a Dockerfile and run `docker build` to turn it into an actual image.
