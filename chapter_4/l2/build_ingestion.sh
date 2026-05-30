#!/bin/bash

# Builds the HEAVY ingestion-service image (carries the full Docling stack).
# Run from the project root, as the Dockerfile COPYs repo-root paths:
#   bash chapter_4/l2/build_ingestion.sh

# Image settings
image_name="rag-ingestion"
tag=0.1.0
dockerfile="chapter_4/l2/Dockerfile_Ingestion"

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
