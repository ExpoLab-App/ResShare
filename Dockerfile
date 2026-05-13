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

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p /opt/conda \
    && rm /tmp/miniconda.sh

# Add conda to PATH
ENV PATH="/opt/conda/bin:${PATH}"

# Accept conda Terms of Service
RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main \
    && conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

# Create conda environment with Python 3.8
RUN conda create --name reschat_venv python=3.8 -y

# Make RUN commands use the conda environment
SHELL ["conda", "run", "-n", "reschat_venv", "/bin/bash", "-c"]

# Install Bazelisk
RUN wget https://github.com/bazelbuild/bazelisk/releases/download/v1.19.0/bazelisk-linux-amd64 -O /usr/local/bin/bazel \
    && chmod +x /usr/local/bin/bazel

# Set Bazel version
ENV USE_BAZEL_VERSION=7.5.0

# Install IPFS
RUN wget https://dist.ipfs.tech/kubo/v0.29.0/kubo_v0.29.0_linux-amd64.tar.gz \
    && tar -xvzf kubo_v0.29.0_linux-amd64.tar.gz \
    && cd kubo \
    && bash install.sh \
    && cd .. \
    && rm -rf kubo kubo_v0.29.0_linux-amd64.tar.gz

# Install IPFS Cluster Service
RUN wget https://dist.ipfs.tech/ipfs-cluster-service/v1.1.4/ipfs-cluster-service_v1.1.4_linux-amd64.tar.gz \
    && tar -xvzf ipfs-cluster-service_v1.1.4_linux-amd64.tar.gz \
    && mv ipfs-cluster-service/ipfs-cluster-service /usr/local/bin/ \
    && rm -rf ipfs-cluster-service ipfs-cluster-service_v1.1.4_linux-amd64.tar.gz

# Initialize IPFS (will be done in entrypoint for proper data persistence)
# We'll initialize it in the entrypoint script to handle volumes properly

# Copy requirements first for better caching
COPY requirements.txt /app/

# Upgrade pip and install Python dependencies in conda environment
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the entire application
COPY . /app/

# Build with Bazel (commented out since using API instead of pybind)
# WORKDIR /app/backend/bazel
# RUN bazel build //kv_service:pybind_kv.so

# Copy the built .so file to backend directory (commented out)
# RUN cp -f bazel-bin/kv_service/pybind_kv.so /app/backend/

# Back to app directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/backend/vector_db \
    && mkdir -p /root/.ipfs \
    && mkdir -p /root/.ipfs-cluster

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
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

