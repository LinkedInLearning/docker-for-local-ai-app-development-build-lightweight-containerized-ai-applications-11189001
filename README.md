# Docker for Local AI App Development: Build Lightweight, Containerized AI Applications
This is the repository for the LinkedIn Learning course `Docker for Local AI App Development: Build Lightweight, Containerized AI Applications`. The full course is available from [LinkedIn Learning][lil-course-url].

![lil-thumbnail-url]

## Course Description

In this course for AI developers, learn how to make Docker containers part of the entire application lifecycle - from defining requirements and building a reproducible development environment to testing services and preparing images for production. Instructor Rami Krispin uses a retrieval-augmented generation (RAG) system as a running architectural case study, showing you how to identify application services, define their requirements, and choose container boundaries that fit both development and production needs. Build a foundation in Dockerfiles, images, registries, and the build-and-run workflow; then use Docker Compose and VS Code Dev Containers to create a containerized workspace for prototyping and validating the application. See how to transform that prototype into dedicated ingestion, query, and vector database services, test the stack in an environment that closely resembles production, and prepare its images for release through multi-stage builds, security hardening, multi-platform builds, versioned publishing, runtime safeguards, and CI validation. By the end of the course, you’ll have a practical, reusable framework for developing, testing, and preparing multi-service AI applications for production at the image and container levels.

## Instructions

To use the course materials, make sure you have:

- **Docker:** Docker Desktop for macOS or Windows, or Docker Engine for Linux.
- **Visual Studio Code:** Install VS Code and the Dev Containers extension.
- **Internet access:** Required on the initial launch to download the container images and models.
- **Model provider credentials:** The course uses OpenAI by default for embeddings and chat. You can also configure Google Gemini for either role or Anthropic for chat. Change the active providers and model selections in [`config/settings.yaml`](config/settings.yaml).
- **Python:** No local installation is required because the project runs inside a VS Code Dev Container.

For more detailed guidance, see:

- **Setup and configuration:** [Project Settings](docs/01_settings.md) covers environment variables, storage, launching the Dev Container, and verifying the environment.
- **Application architecture:** [The RAG System](docs/02_rag.md) explains the ingestion and query pipelines, ChromaDB, and the main project modules.
- **Command-line workflows:** [Command-Line Usage](docs/03_rag_cli.md) shows how to run the ingestion and query pipelines inside the development container.

## Instructor

Rami Krispin is a senior manager of data science and engineering.

Rami Krispin is a data science and engineering manager who mainly focuses on time series analysis, forecasting, and MLOps applications. He is passionate about open source, Docker and MLOps, working with data and APIs, machine learning, Bayesian statistics, data visualization, and GIS data.

Rami is also an open-source contributor and the author of Hands-On Time Series Analysis with R and several R packages for time series analysis and machine learning applications.

Check out my other courses on [LinkedIn Learning](https://www.linkedin.com/learning/instructors/).

[0]: # (Replace these placeholder URLs with actual course URLs)

[lil-course-url]: https://www.linkedin.com/learning/docker-for-local-ai-app-development-build-lightweight-containerized-ai-applications
[lil-thumbnail-url]: https://media.licdn.com/dms/image/v2/D560DAQGoTCsSja_SFA/learning-public-crop_675_1200/B56Z6RYQG5KYAY-/0/1780555514606?e=2147483647&v=beta&t=PkBX1XXo7ehcBusW7D7b6-WZ6zKelpDvWM717DvFabA
