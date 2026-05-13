# ResShare Deployment Guide

This guide provides step-by-step instructions for deploying the ResShare application.

## Prerequisites

- Ubuntu 22.04 or compatible Linux distribution
- Administrative access (sudo privileges)
- Internet connection for downloading dependencies

## Backend Setup

### 1. Install Conda
Install Anaconda or Miniconda on your system.

### 2. Create Python Environment
```bash
conda create --name reschat_venv python=3.8
conda activate reschat_venv
```

### 3. Install C++ Compilers
```bash
sudo apt install gcc-11
sudo apt install g++-11
```

### 4. Install C++ Dependencies
```bash
sudo apt install openssl libssl-dev
```

### 5. Install Bazel
Install Bazel globally if not already installed:

a) Download the amd64.deb release from: http://github.com/bazelbuild/bazelisk/releases
```bash
sudo apt install ./bazelisk-amd64.deb
```

b) Set the Bazel version (strictly required):
```bash
export USE_BAZEL_VERSION=7.5.0
```

c) Verify installation:
```bash
bazel --version
```

### 6. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 7. Build with Bazel
```bash
bazel build //...
```

### 8. Install IPFS

#### a) Install IPFS Daemon
```bash
# Download IPFS
wget https://dist.ipfs.tech/kubo/v0.29.0/kubo_v0.29.0_linux-amd64.tar.gz
tar -xvzf kubo_v0.29.0_linux-amd64.tar.gz
cd kubo
sudo bash install.sh

# Verify installation
ipfs --version

# Initialize IPFS
ipfs init

# Start IPFS daemon
ipfs daemon
```

#### b) Install IPFS Cluster Service
```bash
# Download IPFS Cluster Service
wget https://dist.ipfs.tech/ipfs-cluster-service/v1.1.4/ipfs-cluster-service_v1.1.4_linux-amd64.tar.gz
tar -xvzf ipfs-cluster-service_v1.1.4_linux-amd64.tar.gz
sudo mv ipfs-cluster-service/ipfs-cluster-service /usr/local/bin/

# Verify installation
ipfs-cluster-service --version

# Initialize and start cluster service
ipfs-cluster-service init
ipfs-cluster-service daemon
```

### 9. Configure Environment Variables
```bash
export GOOGLE_API_KEY="your-gemini-api-key-here"
```

### 10. Update IPFS Configuration
Update `backend/config/ipfs.config` with:
```
http://127.0.0.1:9094/
http://127.0.0.1:8080/
```

### 11. Run the Application
```bash
python app.py
```

## Frontend Setup

### Prerequisites
- Node.js version 22.19.0

### Installation Steps
```bash
cd frontend
npm install
npm run start
```

## Verification

After completing the setup:

1. Backend should be running on the configured port
2. Frontend should be accessible via the development server
3. IPFS daemon should be running and accessible
4. IPFS cluster service should be running

## Troubleshooting

- Ensure all services are running before starting the application
- Check that all required ports are available
- Verify that the Google API key is correctly set
- Ensure IPFS configuration matches the running services
