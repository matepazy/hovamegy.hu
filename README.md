# Holavonat - Hungarian Train Tracker

A web application that displays real-time positions of Hungarian trains using the MÁV EMMA API.

## Running with Docker

### Prerequisites
- Docker installed on your system
- Docker Compose (usually included with Docker Desktop)

### Quick Start

1. **Clone or navigate to the project directory:**
   ```bash
   cd holavonat
   ```

2. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   Open your browser and go to: http://localhost:8000

### Alternative Docker Commands

**Build the Docker image:**
```bash
docker build -t holavonat .
```

**Run the container:**
```bash
docker run -p 8000:8000 holavonat
```

**Run with data persistence:**
```bash
docker run -p 8000:8000 -v $(pwd)/data:/app/data holavonat
```

### Docker Compose Commands

**Start in background:**
```bash
docker-compose up -d
```

**Stop the application:**
```bash
docker-compose down
```

**View logs:**
```bash
docker-compose logs -f
```

**Rebuild and restart:**
```bash
docker-compose up --build
```

### Configuration

- **Port:** The application runs on port 8000 by default
- **Data:** Train data is cached in JSON format and updated every 60 seconds
- **Health Check:** Docker includes a health check that verifies the application is responding

### Cloudflare Tunnel Setup (Optional)

The application includes support for Cloudflare Tunnel to expose your local instance to the internet securely.

1. **Create a Cloudflare Tunnel:**
   - Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
   - Navigate to Access > Tunnels
   - Create a new tunnel and get your tunnel token

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your tunnel token
   ```

3. **Run with Cloudflare Tunnel:**
   ```bash
   docker-compose up --build
   ```

The cloudflared container will automatically create a secure tunnel to your application.

### Troubleshooting

1. **Port already in use:**
   - Change the port mapping in `docker-compose.yml` from `8000:8000` to `8001:8000` (or any other available port)

2. **Build fails:**
   - Make sure Docker is running
   - Check that all required files are present (holavonat.py, static/index.html, requirements.txt)

3. **Application not loading:**
   - Wait a few seconds for the initial data fetch
   - Check logs with `docker-compose logs`

### Features

- Real-time train positions on an interactive map
- Train details including delays, stops, and schedules
- Responsive web interface
- Automatic data updates every minute
- Works with all Hungarian trains (MÁV network)

## Running without Docker

If you prefer to run without Docker:

1. Install Python 3.8+
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python holavonat.py`
4. Open: http://localhost:8000