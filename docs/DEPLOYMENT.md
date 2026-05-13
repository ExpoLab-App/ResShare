# ResShare Docker Deployment Guide

This guide covers deploying the ResShare backend using Docker, both locally and on AWS EC2.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Testing](#local-testing)
3. [AWS EC2 Deployment](#aws-ec2-deployment)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Local Testing Requirements
- Docker Engine 20.10 or higher
- Docker Compose 1.29 or higher (optional but recommended)
- At least 4GB RAM available for Docker
- At least 10GB free disk space

### AWS EC2 Requirements
- AWS Account with EC2 access
- SSH key pair for EC2 instance access
- Security group configured for ports 22 (SSH) and 5000 (Flask app)

---

## Local Testing

### Step 1: Prepare Environment

1. **Clone or navigate to your project directory:**
   ```bash
   cd /home/devang/Projects/ResShareDeployable
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` and add your Google API key:**
   ```bash
   nano .env
   ```
   
   Set your actual API key:
   ```
   GOOGLE_API_KEY=your-actual-gemini-api-key-here
   ```

### Step 2: Build Docker Image

**Build the Docker image:**
```bash
docker build -t resshare-backend:latest . --no-cache
```

This will take 10-15 minutes on first build. It will:
- Install all system dependencies
- Install Bazel and build C++ components
- Install IPFS and IPFS Cluster
- Install Python dependencies
- Set up the application

**Verify the build:**
```bash
docker images | grep resshare-backend
```

### Step 3: Run with Docker Compose (Recommended)

**Start the application:**
```bash
docker-compose up -d
```

**Check logs:**
```bash
docker-compose logs -f
```

**Stop the application:**
```bash
docker-compose down
```

**Stop and remove volumes (clean slate):**
```bash
docker-compose down -v
```

### Step 4: Run with Docker CLI (Alternative)

**Start container:**
```bash
docker run -d \
  --name resshare-backend \
  -p 5000:5000 \
  -e GOOGLE_API_KEY="your-api-key-here" \
  -v resshare_ipfs:/root/.ipfs \
  -v resshare_ipfs_cluster:/root/.ipfs-cluster \
  -v resshare_vector_db:/app/backend/vector_db \
  resshare-backend:latest
```

**View logs:**
```bash
docker logs -f resshare-backend
```

**Stop container:**
```bash
docker stop resshare-backend
docker rm resshare-backend
```

### Step 5: Test the Application

1. **Wait for services to start** (about 30-60 seconds)

2. **Test the health endpoint:**
   ```bash
   curl http://localhost:5000/
   ```

3. **Test signup:**
   ```bash
   curl -X POST http://localhost:5000/signup \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"testpass123"}'
   ```

4. **Test login:**
   ```bash
   curl -X POST http://localhost:5000/login \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"testpass123"}' \
     -c cookies.txt
   ```

5. **Access from browser:**
   - Update your frontend config to point to `http://localhost:5000`
   - Or use Postman/Insomnia for API testing

---

## AWS EC2 Deployment

### Step 1: Launch EC2 Instance

1. **Login to AWS Console** and navigate to EC2

2. **Launch Instance:**
   - **Name:** `resshare-backend`
   - **AMI:** Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
   - **Instance Type:** t3.medium (minimum) or t3.large (recommended)
     - Minimum: 2 vCPU, 4 GB RAM
     - Recommended: 2 vCPU, 8 GB RAM
   - **Storage:** 20 GB gp3 (minimum)
   - **Key pair:** Select or create a new key pair

3. **Configure Security Group:**
   
   Create a new security group or edit existing:
   
   | Type       | Protocol | Port Range | Source      | Description           |
   |------------|----------|------------|-------------|-----------------------|
   | SSH        | TCP      | 22         | Your IP     | SSH access            |
   | Custom TCP | TCP      | 5000       | 0.0.0.0/0   | Flask application     |
   | Custom TCP | TCP      | 80         | 0.0.0.0/0   | HTTP (optional)       |
   | Custom TCP | TCP      | 443        | 0.0.0.0/0   | HTTPS (optional)      |

4. **Launch the instance**

### Step 2: Connect to EC2 Instance

```bash
# Replace with your key file and instance IP
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### Step 3: Install Docker on EC2

```bash
# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add ubuntu user to docker group (optional, avoids using sudo)
sudo usermod -aG docker ubuntu

# Log out and back in for group changes to take effect
exit
```

**Reconnect to EC2:**
```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

**Verify Docker installation:**
```bash
docker --version
docker compose version
```

### Step 4: Transfer Application to EC2

**Option A: Using Git (Recommended)**

```bash
# On EC2 instance
cd ~
git clone https://github.com/your-username/ResShareDeployable.git
cd ResShareDeployable
```

**Option B: Using SCP from local machine**

```bash
# On your local machine
cd /home/devang/Projects/ResShareDeployable

# Create tarball (exclude unnecessary files)
tar -czf resshare.tar.gz \
    --exclude='frontend/node_modules' \
    --exclude='backend/__pycache__' \
    --exclude='backend/bazel/bazel-*' \
    --exclude='backend/vector_db' \
    --exclude='.git' \
    .

# Transfer to EC2
scp -i your-key.pem resshare.tar.gz ubuntu@your-ec2-public-ip:~/

# On EC2, extract
ssh -i your-key.pem ubuntu@your-ec2-public-ip
cd ~
tar -xzf resshare.tar.gz -C ResShareDeployable/
cd ResShareDeployable
```

### Step 5: Configure Environment on EC2

```bash
# Create .env file
cp .env.example .env
nano .env
```

Add your actual Google API key:
```
GOOGLE_API_KEY=your-actual-gemini-api-key-here
FLASK_ENV=production
```

### Step 6: Build and Run on EC2

**Build the image:**
```bash
docker build -t resshare-backend:latest .
```

This may take 10-20 minutes on first build.

**Run with Docker Compose:**
```bash
docker compose up -d
```

**Check status:**
```bash
docker compose ps
docker compose logs -f
```

### Step 7: Verify Deployment

1. **Check if container is running:**
   ```bash
   docker ps
   ```

2. **Test from EC2 instance:**
   ```bash
   curl http://localhost:5000/
   ```

3. **Test from your local machine:**
   ```bash
   curl http://your-ec2-public-ip:5000/
   ```

4. **Test signup:**
   ```bash
   curl -X POST http://your-ec2-public-ip:5000/signup \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"testpass123"}'
   ```

### Step 8: Configure Frontend to Use EC2 Backend

Update your frontend configuration (on Vercel or local) to point to:
```
http://your-ec2-public-ip:5000
```

Or if using HTTPS/domain:
```
https://your-domain.com
```

---

## Configuration

### CORS Configuration

By default, the application allows CORS from `http://localhost:5997`. To change this for production:

1. **Edit `app.py`:**
   ```python
   CORS(app, supports_credentials=True, origins=[
       'http://localhost:5997', 
       'http://127.0.0.1:5997',
       'https://your-vercel-domain.vercel.app'  # Add your Vercel domain
   ])
   ```

2. **Rebuild and restart:**
   ```bash
   docker compose down
   docker build -t resshare-backend:latest .
   docker compose up -d
   ```

### Environment Variables

| Variable       | Description                          | Required | Default     |
|----------------|--------------------------------------|----------|-------------|
| GOOGLE_API_KEY | Google Gemini API key for RAG chat   | Yes      | None        |
| FLASK_ENV      | Flask environment (production/debug) | No       | production  |

### Persistent Data

Docker volumes are used to persist data:
- `ipfs_data`: IPFS blockchain data
- `ipfs_cluster_data`: IPFS cluster configuration
- `vector_db`: RAG vector database

**Backup volumes:**
```bash
docker run --rm -v resshare_vector_db:/data -v $(pwd):/backup ubuntu tar czf /backup/vector_db_backup.tar.gz -C /data .
```

**Restore volumes:**
```bash
docker run --rm -v resshare_vector_db:/data -v $(pwd):/backup ubuntu tar xzf /backup/vector_db_backup.tar.gz -C /data
```

---

## Troubleshooting

### Container won't start

**Check logs:**
```bash
docker compose logs
```

**Common issues:**
- IPFS not starting: May need more time, wait 60s
- Port 5000 already in use: Change port mapping in `docker-compose.yml`
- Out of memory: Increase EC2 instance size

### IPFS connection errors

**Enter container and check IPFS:**
```bash
docker exec -it resshare-backend bash
ipfs id
ipfs-cluster-service --version
```

### Build fails

**Check Bazel build:**
```bash
docker build --no-cache -t resshare-backend:latest .
```

**If Bazel fails:**
- Increase Docker memory limit (Docker Desktop: Settings → Resources)
- Try building on a more powerful machine or EC2 instance

### Application not accessible from outside

**Check security group:**
- Ensure port 5000 is open in EC2 security group
- Source should be `0.0.0.0/0` for public access

**Check if Flask is listening on all interfaces:**
```bash
# Inside container
docker exec -it resshare-backend bash
netstat -tuln | grep 5000
```

If it shows `127.0.0.1:5000`, modify `app.py`:
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### Clean slate restart

```bash
# Stop and remove everything
docker compose down -v

# Remove image
docker rmi resshare-backend:latest

# Rebuild and restart
docker build -t resshare-backend:latest .
docker compose up -d
```

---

## Production Best Practices

### 1. Use Reverse Proxy (Nginx)

Install Nginx on EC2:
```bash
sudo apt install nginx
```

Configure Nginx as reverse proxy:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 2. Enable HTTPS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. Set up monitoring

**Container monitoring:**
```bash
docker stats resshare-backend
```

**Set up logging:**
```bash
docker compose logs -f > /var/log/resshare.log 2>&1
```

### 4. Auto-restart on failure

Docker Compose already includes `restart: unless-stopped`. For systemd:

Create `/etc/systemd/system/resshare.service`:
```ini
[Unit]
Description=ResShare Backend
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/ResShareDeployable
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable resshare.service
sudo systemctl start resshare.service
```

---

## Maintenance

### Update application

```bash
cd ~/ResShareDeployable
git pull origin main
docker compose down
docker build -t resshare-backend:latest .
docker compose up -d
```

### View logs

```bash
docker compose logs -f
```

### Backup data

```bash
# Backup all volumes
docker run --rm \
  -v resshare_ipfs:/ipfs \
  -v resshare_ipfs_cluster:/cluster \
  -v resshare_vector_db:/vector_db \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/resshare_backup_$(date +%Y%m%d).tar.gz -C / ipfs cluster vector_db
```

---

## Support

For issues and questions:
- Check logs: `docker compose logs`
- GitHub Issues: [Your repo URL]
- Documentation: [Your docs URL]

