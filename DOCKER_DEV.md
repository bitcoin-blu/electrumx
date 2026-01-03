# Docker Development Environment

This guide explains how to set up and use the Docker-based development environment for ElectrumX. This setup uses Ubuntu/Debian (matching the CI environment) and avoids the macOS-specific issues with native dependencies.

## Prerequisites

- Docker installed and running
- Docker Compose (usually included with Docker Desktop)

Verify installation:
```bash
docker --version
docker-compose --version
```

## Quick Start

1. **Build the development image:**
   ```bash
   ./docker-dev.sh build
   ```

2. **Start the container:**
   ```bash
   ./docker-dev.sh start
   ```

3. **Set up the Python environment:**
   ```bash
   ./docker-dev.sh setup
   ```

4. **Enter the container:**
   ```bash
   ./docker-dev.sh shell
   ```

5. **Run tests:**
   ```bash
   ./docker-dev.sh test
   ```

## Detailed Workflow

### Initial Setup

```bash
# 1. Build the Docker image (one-time setup)
./docker-dev.sh build

# 2. Start the container
./docker-dev.sh start

# 3. Set up Python virtual environment and install dependencies
./docker-dev.sh setup
```

The `setup` command will:
- Create a Python virtual environment
- Install all development dependencies (pytest, pytest-asyncio, pytest-cov, etc.)
- Install RocksDB Python bindings
- Install ElectrumX in editable mode

### Daily Development

```bash
# Enter the container
./docker-dev.sh shell

# Inside the container, activate the virtual environment
source venv/bin/activate

# Now you can work normally:
python -c "import electrumx; print(electrumx.__version__)"
pytest
electrumx_server --help
```

### Running Tests

```bash
# Run all tests
./docker-dev.sh test

# Or from inside the container:
docker-compose exec electrumx-dev bash -c "cd /workspace && source venv/bin/activate && pytest"
```

### Installing Additional Packages

```bash
# Install a package
./docker-dev.sh install package-name

# Or from inside the container:
docker-compose exec electrumx-dev bash -c "cd /workspace && source venv/bin/activate && pip install package-name"
```

## Manual Docker Commands

If you prefer using Docker commands directly:

```bash
# Build the image
docker-compose build

# Start the container
docker-compose up -d

# Enter the container
docker-compose exec electrumx-dev /bin/bash

# Stop the container
docker-compose down

# View logs
docker-compose logs -f electrumx-dev
```

## Container Details

### Base Image
- **OS**: Debian Trixie (matching CI environment)
- **Python**: Python 3 (system package)

### Installed System Packages
- `libleveldb-dev` - LevelDB development libraries
- `librocksdb-dev` - RocksDB development libraries
- `libsnappy-dev`, `zlib1g-dev`, `libbz2-dev` - Compression libraries
- `libgflags-dev`, `liblz4-dev` - Additional dependencies
- `libboost-all-dev` - Boost C++ libraries
- `libsodium-dev` - Cryptography library
- Build tools (gcc, make, etc.)

### Volume Mounts
- **Source code**: `./` → `/workspace` (your changes are immediately available)
- **Pip cache**: Persisted across container restarts
- **Database storage**: Optional volume for ElectrumX database

### Network
- Uses `host` network mode, so the container can access services on your host machine (e.g., bitcoind on localhost:8332)

## Development Tips

### Code Changes
Since the source code is mounted as a volume, any changes you make on your host machine are immediately available in the container. No need to rebuild or restart.

### Virtual Environment
The virtual environment is created inside the container at `/workspace/venv`. It persists as long as the volume mount exists.

### Running ElectrumX Server
To run the server for testing:

```bash
# Inside the container
source venv/bin/activate
export COIN=Bitcoin
export DB_DIRECTORY=/tmp/electrumx-db
export DAEMON_URL=http://user:pass@host.docker.internal:8332/
electrumx_server
```

Note: For accessing host services, use `host.docker.internal` (macOS/Windows) or the host's IP address.

### Debugging
- View container logs: `./docker-dev.sh logs`
- Check container status: `docker-compose ps`
- Inspect container: `docker-compose exec electrumx-dev /bin/bash`

## Troubleshooting

### Container won't start
```bash
# Check Docker is running
docker ps

# Check for port conflicts
docker-compose ps
```

### Permission issues
The container runs as a non-root user (`developer`). If you encounter permission issues, check file ownership on mounted volumes.

### Dependencies not installing
```bash
# Rebuild the image
./docker-dev.sh build

# Re-run setup
./docker-dev.sh setup
```

### Network issues accessing host services
- On macOS/Windows: Use `host.docker.internal`
- On Linux: Use the host's IP address or `172.17.0.1` (default Docker bridge IP)

### Clean slate
```bash
# Remove everything and start fresh
./docker-dev.sh clean
./docker-dev.sh build
./docker-dev.sh start
./docker-dev.sh setup
```

## Advantages Over Native macOS Setup

1. **No dependency issues**: All system libraries are properly installed and compatible
2. **Matches CI environment**: Same OS and packages as the CI pipeline
3. **Isolated environment**: Doesn't affect your system Python or packages
4. **Reproducible**: Same environment for all developers
5. **Easy cleanup**: Just remove the container/image

## Integration with IDE

You can configure your IDE to use the Python interpreter from the container:

1. Find the Python path in the container:
   ```bash
   docker-compose exec electrumx-dev which python3
   ```

2. Configure your IDE to use Docker as a remote interpreter (VS Code, PyCharm support this)

## Next Steps

- Read the main [HOWTO](docs/HOWTO.rst) for ElectrumX configuration
- Check [environment variables](docs/environment.rst) documentation
- Review the [architecture](docs/architecture.rst) documentation

