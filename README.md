# Docker for Local AI App Development: Build Lightweight, Containerized AI Applications
This is the repository for the LinkedIn Learning course `Docker for Local AI App Development: Build Lightweight, Containerized AI Applications`. The full course is available from [LinkedIn Learning][lil-course-url].

![lil-thumbnail-url]

## Course Description

In this course for developers, learn how to build lightweight, containerized AI applications using a simple, repeatable workflow. Instructor Rami Krispin shows you how to run small open‑source LLMs locally, integrate powerful AI APIs, and orchestrate multiservice stacks—such as app containers, embedding services, and vector databases—using Docker and Docker Compose. Through hands-on, interactive building exercises, learn how to containerize AI features, debug them in an isolated environment, and package them as portable microservices. By the end of this course, you’ll be equipped with a fully reproducible development workflow you can use on any machine to prototype and ship AI‑powered application features with confidence.

_See the readme file in the main branch for updated instructions and information._

## Instructions
This repository has branches for each of the videos in the course. You can use the branch pop up menu in github to switch to a specific branch and take a look at the course at that stage, or you can add `/tree/BRANCH_NAME` to the URL to go to the branch you want to access.

## Branches
The branches are structured to correspond to the videos in the course. The naming convention is `CHAPTER#_MOVIE#`. As an example, the branch named `02_03` corresponds to the second chapter and the third video in that chapter. 
Some branches will have a beginning and an end state. These are marked with the letters `b` for "beginning" and `e` for "end". The `b` branch contains the code as it is at the beginning of the movie. The `e` branch contains the code as it is at the end of the movie. The `main` branch holds the final state of the code when in the course.

When switching from one exercise files branch to the next after making changes to the files, you may get a message like this:

    error: Your local changes to the following files would be overwritten by checkout:        [files]
    Please commit your changes or stash them before you switch branches.
    Aborting

To resolve this issue:
	
    Add changes to git using this command: git add .
	Commit changes using this command: git commit -m "some message"


## Instructor

Rami Krispin is a senior manager of data science and engineering.

Rami Krispin is a data science and engineering manager who mainly focuses on time series analysis, forecasting, and MLOps applications. He is passionate about open source, Docker and MLOps, working with data and APIs, machine learning, Bayesian statistics, data visualization, and GIS data.

Rami is also an open-source contributor and the author of Hands-On Time Series Analysis with R and several R packages for time series analysis and machine learning applications.

Check out my other courses on [LinkedIn Learning](https://www.linkedin.com/learning/instructors/).

[0]: # (Replace these placeholder URLs with actual course URLs)

[lil-course-url]: https://www.linkedin.com/learning/docker-for-local-ai-app-development-build-lightweight-containerized-ai-applications
[lil-thumbnail-url]: https://media.licdn.com/dms/image/v2/D560DAQGoTCsSja_SFA/learning-public-crop_675_1200/B56Z6RYQG5KYAY-/0/1780555514606?e=2147483647&v=beta&t=PkBX1XXo7ehcBusW7D7b6-WZ6zKelpDvWM717DvFabA

