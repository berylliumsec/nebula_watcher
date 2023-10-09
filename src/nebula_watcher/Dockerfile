FROM ubuntu:latest
ENV IN_DOCKER=yes
LABEL org.opencontainers.image.authors="david@berylliumsec.com"
# Set the working directory in the Docker container

RUN apt update && \
    apt upgrade -y && \
    apt-get install -y --no-install-recommends \
        graphviz \
        python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the current directory's content into the container
COPY nebula_watcher.py  /app/

COPY diagram_resources /app/diagram_resources
# Install the necessary packages
RUN pip install pip --upgrade && pip install --no-cache-dir diagrams psutil

# Run the script when the container launches
CMD ["python3", "nebula_watcher.py", "--diagram_name", "/app/output/ethical_hacking_activity"]
