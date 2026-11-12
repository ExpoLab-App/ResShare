# ResShare Backend Dockerfile
FROM ubuntu:22.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    tar \
    gcc-11 \
    g++-11 \
    openssl \
    libssl-dev \
    git \
    ca-certificates \
    bzip2 \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Set gcc-11 and g++-11 as default
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 100 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 100

# Install Miniconda for the image architecture.
# On Apple Silicon, Docker builds linux/arm64 by default. The x86_64 installer
# is an amd64 ELF, and Rosetta exits 133 because the arm64 image has no
# /lib64/ld-linux-x86-64.so.2.
ARG TARGETARCH
RUN set -eu; \
    case "${TARGETARCH}" in \
      amd64) MINICONDA_ARCH=x86_64 ;; \
      arm64) MINICONDA_ARCH=aarch64 ;; \
      *) echo "Unsupported architecture: ${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    wget "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-${MINICONDA_ARCH}.sh" -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p /opt/conda \
    && rm /tmp/miniconda.sh

# Add conda to PATH
ENV PATH="/opt/conda/bin:${PATH}"

# Accept conda Terms of Service
RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main \
    && conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

# Create conda environment with a Python version supported by qdrant-client
RUN conda create --name reschat_venv python=3.10 -y

# Make RUN commands use the conda environment
SHELL ["conda", "run", "-n", "reschat_venv", "/bin/bash", "-c"]

# Install IPFS from the GitHub release. dist.ipfs.tech refuses connections.
ARG TARGETARCH
RUN curl -fL --retry 5 --retry-delay 2 \
      -o "kubo_v0.29.0_linux-${TARGETARCH}.tar.gz" \
      "https://github.com/ipfs/kubo/releases/download/v0.29.0/kubo_v0.29.0_linux-${TARGETARCH}.tar.gz" \
    && tar -xvzf "kubo_v0.29.0_linux-${TARGETARCH}.tar.gz" \
    && cd kubo \
    && bash install.sh \
    && cd .. \
    && rm -rf kubo "kubo_v0.29.0_linux-${TARGETARCH}.tar.gz"

# Install IPFS Cluster Service. v1.1.4 published binaries only on dist.ipfs.tech
# and that GitHub release has no assets. v1.1.6 has no config or API changes.
ARG TARGETARCH
RUN curl -fL --retry 5 --retry-delay 2 \
      -o "ipfs-cluster-service_v1.1.6_linux-${TARGETARCH}.tar.gz" \
      "https://github.com/ipfs-cluster/ipfs-cluster/releases/download/v1.1.6/ipfs-cluster-service_v1.1.6_linux-${TARGETARCH}.tar.gz" \
    && tar -xvzf "ipfs-cluster-service_v1.1.6_linux-${TARGETARCH}.tar.gz" \
    && mv ipfs-cluster-service/ipfs-cluster-service /usr/local/bin/ \
    && rm -rf ipfs-cluster-service "ipfs-cluster-service_v1.1.6_linux-${TARGETARCH}.tar.gz"

# Initialize IPFS (will be done in entrypoint for proper data persistence)
# We'll initialize it in the entrypoint script to handle volumes properly

# Copy requirements first for better caching
COPY requirements.txt /app/

# Upgrade pip and install Python dependencies in conda environment
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the entire application
COPY . /app/

# Back to app directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /root/.ipfs \
    && mkdir -p /root/.ipfs-cluster

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Expose Flask port and IPFS ports
EXPOSE 5000 8080 9094

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
