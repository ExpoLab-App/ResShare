# ResShare Development Environment Deployment Guide

This guide provides step-by-step instructions for deploying ResShare in a **development environment** on **AWS EC2** (backend) and **Vercel** (frontend).

## Table of Contents

2. [Prerequisites](#prerequisites)
3. [Backend Deployment on EC2](#backend-deployment-on-ec2)
4. [Frontend Deployment on Vercel](#frontend-deployment-on-vercel)
5. [Configuration](#configuration)
6. [Post-Deployment Setup](#post-deployment-setup)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)


### Required Credentials

- **Google Gemini API Key**: For RAG chat functionality
  - Get it from: https://aistudio.google.com/prompts/new_chat
- **Flask Secret Key**: For session management (generate a secure random string)
- **ResilientDB KV Service URL**

### EC2 Instance Requirements

- **Minimum**: t3.medium (2 vCPU, 4 GB RAM)
- **Recommended**: t3.large (2 vCPU, 8 GB RAM) or better
- **Storage**: 20 GB minimum (gp3 SSD)
- **OS**: Ubuntu 22.04 LTS

---

## Backend Deployment on EC2

### Step 1: Launch EC2 Instance

1. **Login to AWS Console** → Navigate to EC2

2. **Click "Launch Instance"** and configure:

   - **Name**: `resshare-backend`
   - **AMI**: Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
   - **Instance Type**: t3.medium or t3.large
   - **Key Pair**: Select or create a new key pair (save the `.pem` file securely)
   - **Network Settings**: 
     - Create security group with the following rules:

   | Type       | Protocol | Port Range | Source      | Description           |
   |------------|----------|------------|-------------|-----------------------|
   | SSH        | TCP      | 22         | Your IP     | SSH access            |
   | Custom TCP | TCP      | 5000       | 0.0.0.0/0   | Flask application     |
   | Custom TCP | TCP      | 8080       | 0.0.0.0/0   | IPFS Gateway          |
   | Custom TCP | TCP      | 9094       | 0.0.0.0/0   | IPFS Cluster API      |
   | Custom TCP | TCP      | 80         | 0.0.0.0/0   | HTTP (for Nginx)      |
   | Custom TCP | TCP      | 443        | 0.0.0.0/0   | HTTPS (for Nginx)     |

   - **Storage**: 20 GB gp3 (minimum)

3. **Launch the instance**

4. **Note the Public IP address** of your instance

### Step 2: Connect to EC2 Instance

```bash
# On your local machine
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

1. **Update the system:**

    ```bash
    sudo apt-get update && sudo apt-get upgrade -y
    ```

2. **Install Docker:**

    ```bash
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    ```

3. **Start Docker and enable on boot:**

    ```bash
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker ubuntu
    ```

4. **Logout and reconnect for group changes to take effect:**

    ```bash
    exit
    ssh -i your-key.pem ubuntu@your-ec2-public-ip
    ```

5. **Verify Docker installation:**

    ```bash
    docker --version
    docker compose version
    ```

### Step 4: Transfer Application to EC2

```bash
# On EC2 instance
cd ~
git clone https://github.com/devangb3/ResShareDeployable.git
cd ResShareDeployable
```
```

### Step 5: Configure Environment Variables

```bash
# Create .env file
cd ~/ResShareDeployable
cp env.example .env
nano .env
```

**Edit `.env` with your actual values:**

```bash
# Google API Key for Gemini (required for RAG chat functionality)
GOOGLE_API_KEY=your-actual-gemini-api-key-here

# Flask Configuration
FLASK_ENV=production

# CORS Origins (comma-separated, for production frontends)
# Add your Vercel domain here
CORS_ORIGINS=https://res-share-deployable.vercel.app/

# Flask Secret Key (generate a secure random string)
FLASK_SECRET_KEY=your-secure-random-secret-key-here

# Storage Type: 'memory' or 'resilientdb'
STORAGE_TYPE=memory

# KV Service URL (if using resilientdb)
KV_SERVICE_URL=https://crow.resilientdb.com
```

**Generate a secure Flask secret key:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 6: Build and Run Docker Container

```bash
# Build the Docker image (this will take 10-20 minutes on first build)
cd ~/ResShareDeployable
docker build -t resshare-backend:latest .

# Run with Docker Compose
docker compose up -d

# Check logs
docker compose logs -f
```

**Wait for services to start** (about 60-90 seconds). You should see:
- IPFS daemon started
- IPFS Cluster service started
- Flask application started

### Step 7: Verify Backend Deployment

```bash
# Check if container is running
docker ps

# Test health endpoint from EC2
curl http://localhost:5000/

# Test from your local machine
curl http://YOUR_EC2_PUBLIC_IP:5000/
```

**Expected response:**
```json
{"message": "OK"}
```

### Step 8: Set Up Ngrok Tunnel

Ngrok provides a secure tunnel to your local/EC2 backend, useful for development, testing, or when you don't want to expose EC2 directly to the internet.

**Install ngrok on EC2:**
```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com bookworm main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list \
  && sudo apt update \
  && sudo apt install ngrok
```

**Get ngrok authtoken (if not already configured):**
1. Sign up at [ngrok.com](https://ngrok.com) (free account available)
2. Get your authtoken from the dashboard
3. Configure it:
   ```bash
   ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN
   ```

**Start ngrok tunnel:**
```bash
# Tunnel to Flask backend (port 5000)
ngrok http 5000
```

# View ngrok URL
curl http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url'
```

**Note the ngrok URL** (e.g., `https://abc123.ngrok-free.app`)

**Update backend CORS to include ngrok URL:**
```bash
cd ~/ResShareDeployable
nano .env
```

Add ngrok URL to CORS_ORIGINS:
```bash
CORS_ORIGINS=https://res-share-deployable.vercel.app/,https://abc123.ngrok-free.app
```

**Restart backend:**
```bash
docker compose restart
```

**Use ngrok URL for frontend:**
- Update `REACT_APP_API_BASE_URL` in Vercel to use the ngrok URL

## Frontend Deployment on Vercel

### Step 1: Prepare Frontend for Deployment

1. **Update API Configuration**

   Edit `frontend/src/utils/api.js` or create a `.env` file in the `frontend` directory:

   ```bash
   cd frontend
   nano .env.production
   ```

   Add:
   ```
   REACT_APP_API_BASE_URL=https://your-ec2-public-ip:5000
   ```

   Or if using a domain with HTTPS:
   ```
   REACT_APP_API_BASE_URL=https://your-domain.com
   ```

   Or if using ngrok tunnel:
   ```
   REACT_APP_API_BASE_URL=https://your-ngrok-url.ngrok-free.app
   ```

2. **Update CORS in Backend**

   Make sure your EC2 backend's `.env` includes your Vercel domain:
   ```bash
   CORS_ORIGINS=https://your-app.vercel.app
   ```

   Then restart the backend:
   ```bash
   docker compose restart
   ```

### Step 2: Deploy to Vercel


** Using Vercel Dashboard**

 **Add Environment Variables:**
   - Click "Environment Variables"
   - Add:
     ```
     REACT_APP_API_BASE_URL = https://your-domain.com
     ```

6. **Click "Deploy"**

### Step 3: Update Backend CORS

After Vercel deployment, you'll get a URL like `https://res-share-deployable.vercel.app/`.

1. **Update EC2 backend `.env`:**
   ```bash
   ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
   cd ~/ResShareDeployable
   nano .env
   ```

   Update:
   ```bash
   CORS_ORIGINS=https://res-share-deployable.vercel.app/
   ```

2. **Restart backend:**
   ```bash
   docker compose down
   docker compose up -d
   ```

### Step 4: Verify Frontend Deployment

1. **Visit your Vercel URL**: `https://res-share-deployable.vercel.app/`
2. **Test login/signup functionality**
3. **Check browser console for any CORS errors**

---

## Configuration

### Environment Variables Summary

#### Backend (EC2) - `.env`

| Variable         | Description                          | Required | Example                          |
|------------------|--------------------------------------|----------|----------------------------------|
| GOOGLE_API_KEY   | Google Gemini API key for RAG chat   | Yes      | `AIzaSy...`                      |
| FLASK_ENV        | Flask environment                    | No       | `production`                     |
| FLASK_SECRET_KEY | Secret key for session management    | Yes      | `abc123...` (32+ chars)          |
| CORS_ORIGINS     | Allowed frontend origins (comma-sep) | Yes      | `https://app.vercel.app`         |
| STORAGE_TYPE     | Storage backend type                 | No       | `memory` or `resilientdb`        |
| KV_SERVICE_URL   | ResilientDB KV service URL           | No       | `https://crow.resilientdb.com`   |

#### Frontend (Vercel) - Environment Variables

| Variable              | Description                    | Required | Example                    |
|-----------------------|--------------------------------|----------|----------------------------|
| REACT_APP_API_BASE_URL| Backend API URL                | Yes      | `https://your-ec2-ip:5000` |

### IPFS Configuration

The backend uses IPFS Cluster for file storage. Configuration files are in:
- `backend/config/ipfs.config` - IPFS Cluster and Gateway URLs
- `backend/config/kv_service.config` - KV Service configuration

These are automatically configured in the Docker container.

---

## Troubleshooting

### Backend Issues

#### Container Won't Start

```bash
# Check logs
docker compose logs

# Common issues:
# - IPFS not starting: Wait 60-90 seconds
# - Port 5000 in use: Change port in docker-compose.yml
# - Out of memory: Increase EC2 instance size
```

#### IPFS Connection Errors

```bash
# Enter container
docker exec -it resshare-backend bash

# Check IPFS status
ipfs id
ipfs-cluster-service --version

# Check IPFS logs
cat /app/ipfs.log
cat /app/ipfs-cluster.log
```

#### Application Not Accessible from Outside

1. **Check security group**: Ensure port 5000 is open
2. **Check if Flask is listening on all interfaces:**
   ```bash
   docker exec -it resshare-backend bash
   netstat -tuln | grep 5000
   ```
   Should show `0.0.0.0:5000`, not `127.0.0.1:5000`

3. **Test from EC2 first:**
   ```bash
   curl http://localhost:5000/
   ```

4. **Then test externally:**
   ```bash
   curl http://YOUR_EC2_PUBLIC_IP:5000/
   ```

#### CORS Errors

1. **Check backend `.env`** has correct Vercel URL:
   ```bash
   CORS_ORIGINS=https://your-app.vercel.app
   ```

2. **Restart backend:**
   ```bash
   docker compose restart
   ```

3. **Check browser console** for specific CORS error messages

#### Ngrok Issues

**Ngrok tunnel not working:**
```bash
# Check if ngrok is running
ps aux | grep ngrok

# Check ngrok status
curl http://localhost:4040/api/tunnels

# View ngrok logs
tail -f /tmp/ngrok.log

# Restart ngrok
pkill ngrok
ngrok http 5000
```

**Ngrok URL changed:**
- Free ngrok URLs change on each restart
- Update `CORS_ORIGINS` in backend `.env` with new URL
- Update `REACT_APP_API_BASE_URL` in Vercel
- Restart backend: `docker compose restart`

**Ngrok connection refused:**
- Ensure Flask backend is running: `docker compose ps`
- Verify port 5000 is accessible: `curl http://localhost:5000/`
- Check ngrok is pointing to correct port: `ngrok http 5000`

**Get current ngrok URL programmatically:**
```bash
# Get ngrok URL
curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url'

# Or without jq
curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*"' | head -1
```

### Frontend Issues

#### API Connection Errors

1. **Check `REACT_APP_API_BASE_URL`** in Vercel environment variables
2. **Verify backend is accessible** from browser
3. **Check CORS configuration** in backend

#### Build Failures on Vercel

1. **Check build logs** in Vercel dashboard
2. **Verify `package.json`** has correct build scripts
3. **Ensure all dependencies** are in `package.json` (not just devDependencies)

### Common Solutions

#### Clean Slate Restart

```bash
# Stop and remove everything
docker compose down -v

# Remove image
docker rmi resshare-backend:latest

# Rebuild and restart
docker build -t resshare-backend:latest .
docker compose up -d
```

#### Reset IPFS Data

```bash
# Stop container
docker compose down

# Remove IPFS volumes
docker volume rm resshare_ipfs resshare_ipfs_cluster

# Restart
docker compose up -d
```

---

## Maintenance

### Update Application

**Backend (EC2):**
```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
cd ~/ResShareDeployable
git pull origin main
docker compose down
docker build -t resshare-backend:latest .
docker compose up -d
```

**Frontend (Vercel):**
- Push changes to GitHub
- Vercel will automatically redeploy
- Or manually trigger redeploy in Vercel dashboard

### Backup Data

**Backup Docker volumes:**
```bash
# Backup all volumes
docker run --rm \
  -v resshare_ipfs:/ipfs \
  -v resshare_ipfs_cluster:/cluster \
  -v resshare_vector_db:/vector_db \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/resshare_backup_$(date +%Y%m%d).tar.gz -C / ipfs cluster vector_db

# Download backup
scp -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP:~/ResShareDeployable/resshare_backup_*.tar.gz ./
```

**Restore from backup:**
```bash
# Upload backup to EC2
scp -i your-key.pem resshare_backup_YYYYMMDD.tar.gz ubuntu@YOUR_EC2_PUBLIC_IP:~/

# On EC2, restore
docker compose down
docker run --rm \
  -v resshare_ipfs:/ipfs \
  -v resshare_ipfs_cluster:/cluster \
  -v resshare_vector_db:/vector_db \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/resshare_backup_YYYYMMDD.tar.gz -C /
docker compose up -d
```

### View Logs

**Backend logs:**
```bash
# All logs
docker compose logs

# Follow logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100

# Specific service logs
docker compose logs resshare-backend
```

**Frontend logs:**
- Check Vercel dashboard → Your Project → Deployments → View Function Logs

### Monitor Resources

**EC2 Resource Usage:**
```bash
# CPU and memory
htop

# Disk usage
df -h

# Docker disk usage
docker system df
```

**Vercel Usage:**
- Check Vercel dashboard → Your Project → Analytics

---

## Security Best Practices

1. **Use HTTPS**: Set up SSL/TLS with Let's Encrypt
2. **Rotate Secrets**: Regularly update `FLASK_SECRET_KEY`
3. **Limit Security Group**: Restrict SSH access to your IP only
4. **Keep Updated**: Regularly update Docker images and dependencies
5. **Monitor Logs**: Set up log monitoring and alerts
6. **Backup Regularly**: Automate backups of Docker volumes

---

## Cost Estimation

### EC2 Costs (Approximate)

- **t3.medium**: ~$30/month (on-demand)
- **t3.large**: ~$60/month (on-demand)
- **Storage (20 GB)**: ~$2/month
- **Data Transfer**: Varies by usage

**Tips to reduce costs:**
- Use Reserved Instances (1-3 year commitment)
- Use Spot Instances for development
- Set up auto-scaling if needed

### Vercel Costs

- **Free Tier**: 
  - 100 GB bandwidth/month
  - Unlimited deployments
  - Perfect for small to medium applications

- **Pro Tier** ($20/month):
  - 1 TB bandwidth/month
  - Advanced features

---

## Support

For issues and questions:
- Check logs: `docker compose logs`
- GitHub Issues: [Your repository URL]
- Documentation: See `docs/` directory

---

## Quick Reference Commands

### EC2 Backend

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart

# View logs
docker compose logs -f

# Rebuild
docker build -t resshare-backend:latest .
docker compose up -d

# Check status
docker ps
curl http://localhost:5000/
```

### Ngrok

```bash
# Install ngrok
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com bookworm main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list \
  && sudo apt update \
  && sudo apt install ngrok

# Configure authtoken
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN

# Start tunnel
ngrok http 5000

# Start in background
nohup ngrok http 5000 > /tmp/ngrok.log 2>&1 &

# Get current URL
curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url'

# Check status
curl http://localhost:4040/api/tunnels

# Stop ngrok
pkill ngrok
```

### Vercel Frontend

```bash
# Deploy
vercel --prod

# View logs
vercel logs

# List deployments
vercel ls
```