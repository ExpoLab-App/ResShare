# ResShare Backend - Quick Start Guide

## Local Testing

```bash
# 1. Setup environment
cp env.example .env
nano .env  # Add your GOOGLE_API_KEY

# 2. Build and run
docker build -t resshare-backend:latest .
docker compose up -d

# 3. Check logs
docker compose logs -f

# 4. Test
curl http://localhost:5000/
```

## AWS EC2 Deployment (30 Minutes)

### Quick Steps

```bash
# 1. Launch EC2 Instance
# - Ubuntu 22.04, t3.medium, 20GB storage
# - Open ports: 22 (SSH), 5000 (App)

# 2. Connect
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
# Logout and login again

# 4. Transfer Code
git clone https://github.com/your-repo/ResShareDeployable.git
cd ResShareDeployable


# 5. Configure
cp env.example .env
nano .env  # Add GOOGLE_API_KEY and CORS_ORIGINS

# 6. Deploy
docker build -t resshare-backend:latest .
docker compose up -d

# 7. Verify
curl http://localhost:5000/
curl http://your-ec2-ip:5000/  # From local machine
```

## Essential Commands

### Local Development

```bash
# Build
docker build -t resshare-backend:latest .

# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f

# Restart
docker compose restart

# Clean restart (remove all data)
docker compose down -v
docker compose up -d

# Shell into container
docker exec -it resshare-backend bash
```

### Testing API

```bash
# Health check
curl http://localhost:5000/

# Signup
curl -X POST http://localhost:5000/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}' \
  -c cookies.txt

# Create folder (requires login cookie)
curl -X POST http://localhost:5000/create-folder \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"folder_path":"Documents"}'
```

## Configuration

### Environment Variables (.env)

```bash
# Required
GOOGLE_API_KEY=your-gemini-api-key-here

# Optional
FLASK_ENV=production  # or 'development' for debug mode
CORS_ORIGINS=https://your-app.vercel.app,https://www.yourdomain.com
```

### Update CORS for Production

Add your Vercel frontend URL to `.env`:
```
CORS_ORIGINS=https://your-app.vercel.app
```

Or set it when running:
```bash
CORS_ORIGINS=https://your-app.vercel.app docker compose up -d
```

## Troubleshooting

### Container won't start
```bash
docker compose logs
# Common: Wait 60s for IPFS to initialize
```

### Build fails
```bash
# Increase Docker memory (Desktop: Settings → Resources → Memory: 4GB+)
# Or use larger EC2 instance (t3.medium minimum)
```

### Can't access from outside (EC2)
```bash
# 1. Check security group has port 5000 open
# 2. Test from EC2 first: curl http://localhost:5000/
# 3. Then test externally: curl http://your-ec2-ip:5000/
```

### CORS errors
```bash
# Add your frontend URL to .env
echo 'CORS_ORIGINS=https://your-app.vercel.app' >> .env
docker compose restart
```

## Monitoring

```bash
# Container stats
docker stats resshare-backend

# Logs (follow)
docker compose logs -f

# Logs (last 100 lines)
docker compose logs --tail=100

# Check container health
docker ps
docker inspect resshare-backend | grep -A 10 Health
```

## Data Backup

```bash
# Backup all volumes
docker run --rm \
  -v resshare_ipfs:/ipfs \
  -v resshare_ipfs_cluster:/cluster \
  -v resshare_vector_db:/vector_db \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/backup_$(date +%Y%m%d).tar.gz -C / ipfs cluster vector_db

# Restore
docker run --rm \
  -v resshare_ipfs:/ipfs \
  -v resshare_ipfs_cluster:/cluster \
  -v resshare_vector_db:/vector_db \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/backup_YYYYMMDD.tar.gz -C /
```

## Production Setup (Nginx + HTTPS)

### Install Nginx on EC2
```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx -y
```

### Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/resshare
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/resshare /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Enable HTTPS
```bash
sudo certbot --nginx -d your-domain.com
```

## 📝 Notes

- **First startup** takes 60-90 seconds for IPFS to initialize
- **Memory**: Minimum 4GB RAM recommended
- **Storage**: Plan for 10GB+ (IPFS data grows)
- **Ports**: 5000 (Flask), 4001 (IPFS P2P), 5001 (IPFS API), 8080 (IPFS Gateway)
- **Persistence**: Data stored in Docker volumes (survives container restarts)

## Full Documentation

For detailed instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)

