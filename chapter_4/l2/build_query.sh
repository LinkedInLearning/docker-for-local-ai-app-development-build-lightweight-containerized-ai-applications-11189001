#!/bin/bash

# Builds the LEAN query-service image (no PDF-parsing stack).
# Run from the project root, as the Dockerfile COPYs repo-root paths:
#   bash chapter_4/l2/build_query.sh

# Image settings
image_name="rag-query"
tag=0.1.0
dockerfile="chapter_4/l2/Dockerfile_Query"

echo "Build the docker"

docker build . -f $dockerfile \
                --progress=plain \
                -t $image_name:$tag

if [[ $? = 0 ]] ; then
echo "Done. Image $image_name:$tag built"
docker images | grep rag-
else
echo "Docker build failed"
fi
