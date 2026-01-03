# Running ElectrumX Server

This guide explains how to run the ElectrumX server using the Docker development environment.

## Quick Start

1. **Copy the example configuration:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your settings:**
   ```bash
   # Edit .env file with your actual values
   # Most importantly: DAEMON_URL with your Bitcoin daemon credentials
   ```

3. **Start the server:**
   ```bash
   ./docker-dev.sh server
   ```

## Configuration File

The `.env` file contains all server configuration. It's gitignored to protect sensitive information like RPC credentials.

### Required Settings

- **COIN**: The cryptocurrency (e.g., `Bitcoin`, `BitcoinTestnet`)
- **DB_DIRECTORY**: Where to store the database (inside container)
- **DAEMON_URL**: Your Bitcoin daemon RPC connection
  - Format: `http://username:password@hostname:port/`
  - For macOS: use `host.docker.internal` instead of `localhost`
  - For Linux: use host IP or `172.17.0.1`

### Example `.env` for Local Development

```bash
COIN=Bitcoin
NET=mainnet
DB_DIRECTORY=/var/lib/electrumx
DAEMON_URL=http://rpcuser:rpcpassword@host.docker.internal:8332/
SERVICES=tcp://:50001,rpc://
DB_ENGINE=leveldb
CACHE_MB=1200
ALLOW_ROOT=true
```

## Running the Server

### Foreground (see logs directly)

```bash
./docker-dev.sh server
```

### Background (detached)

```bash
./docker-dev.sh server-bg
```

View logs:
```bash
./docker-dev.sh logs
```

## Prerequisites

### Bitcoin Daemon

You need a running Bitcoin Core daemon with:
- `txindex=1` in `bitcoin.conf`
- RPC enabled
- Fully synced (or ElectrumX will sync from genesis)

Example `bitcoin.conf`:
```
server=1
rpcuser=youruser
rpcpassword=yourpassword
rpcport=8332
txindex=1
```

### Accessing Host Services from Docker

- **macOS/Windows**: Use `host.docker.internal` in DAEMON_URL
- **Linux**: Use your host's IP address or `172.17.0.1` (default Docker bridge)

## Server Commands

```bash
# Start server (foreground)
./docker-dev.sh server

# Start server (background)
./docker-dev.sh server-bg

# View server logs
./docker-dev.sh logs

# Stop server (stop container)
./docker-dev.sh stop

# Restart server
./docker-dev.sh restart
```

## Manual Server Execution

You can also run the server manually inside the container:

```bash
# Enter container
./docker-dev.sh shell

# Inside container
source venv/bin/activate

# Load environment variables from .env
set -a
source /workspace/.env
set +a

# Run server
electrumx_server
```

## Initial Sync

On first run, ElectrumX will:
1. Create the database
2. Start indexing from genesis block
3. This can take **hours or days** depending on:
   - Hardware (CPU, disk speed)
   - Chain size
   - Network speed

The server will **not accept client connections** until fully synced, but RPC will work for monitoring.

## Monitoring

### Check Sync Status

```bash
# Inside container
./docker-dev.sh shell
source venv/bin/activate
electrumx_rpc getinfo
```

### View Logs

```bash
./docker-dev.sh logs
```

### Check Database Size

```bash
docker-compose exec electrumx-dev du -sh /var/lib/electrumx
```

## Troubleshooting

### Server Won't Start

1. **Check .env file exists:**
   ```bash
   ls -la .env
   ```

2. **Verify Bitcoin daemon is accessible:**
   ```bash
   # Test from container
   docker-compose exec electrumx-dev curl http://host.docker.internal:8332/
   ```

3. **Check required environment variables:**
   ```bash
   docker-compose exec electrumx-dev env | grep -E "(COIN|DB_DIRECTORY|DAEMON_URL)"
   ```

### Connection Issues

- **Can't connect to bitcoind**: Check DAEMON_URL uses correct hostname
- **Permission denied**: Ensure bitcoind RPC credentials are correct
- **Connection refused**: Verify bitcoind is running and RPC is enabled

### Database Issues

- **Disk space**: Ensure at least 70-80GB free for Bitcoin mainnet
- **Permissions**: Database directory must be writable
- **Corruption**: Delete database directory and resync if needed

## Production Considerations

For production use, consider:

1. **SSL Certificates**: Set up proper SSL certificates
2. **Firewall**: Configure firewall rules for exposed ports
3. **Monitoring**: Set up monitoring and alerting
4. **Backups**: Regular database backups
5. **Resource Limits**: Adjust CACHE_MB and other limits
6. **Logging**: Configure proper log rotation
7. **Security**: Use strong RPC passwords, restrict network access

## Additional Resources

- [Environment Variables Documentation](docs/environment.rst)
- [HOWTO Guide](docs/HOWTO.rst)
- [ElectrumX Documentation](https://electrumx-spesmilo.readthedocs.io)

