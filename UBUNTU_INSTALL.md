# Ubuntu Installation Guide for ElectrumX

This guide explains how to install and run ElectrumX on a fresh Ubuntu system.

## Quick Start

Run the automated installation script:

```bash
git clone https://github.com/spesmilo/electrumx.git
cd electrumx
./install-ubuntu.sh
```

## Manual Installation

If you prefer to install manually, follow these steps:

### 1. Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
    git \
    python3 \
    python3-pip \
    python3-setuptools \
    python3-venv \
    libsnappy-dev \
    zlib1g-dev \
    libbz2-dev \
    libgflags-dev \
    liblz4-dev \
    librocksdb-dev \
    libleveldb-dev \
    libboost-all-dev \
    libsodium-dev \
    build-essential
```

### 2. Clone the Repository

```bash
git clone https://github.com/spesmilo/electrumx.git
cd electrumx
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install ElectrumX

```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install Cython (required for rocksdb)
pip install 'Cython<3.0'

# Install ElectrumX with RocksDB support (recommended)
pip install ".[rocksdb]"

# Or install without RocksDB (LevelDB only)
# pip install .
```

### 5. Create Database Directory

```bash
sudo mkdir -p /var/lib/electrumx
sudo chown $USER:$USER /var/lib/electrumx
```

## Configuration

### 1. Create Configuration File

```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

### 2. Configure for BitcoinBLU

Edit `.env` with these settings:

```bash
COIN=BitcoinBlu
NET=main-blu
DB_DIRECTORY=/var/lib/electrumx
DAEMON_URL=http://rpcuser:rpcpassword@localhost:8342/
SERVICES=tcp://:50001,rpc://
DB_ENGINE=leveldb
CACHE_MB=1200
LOG_LEVEL=info
```

### 3. Ensure BitcoinBLU Daemon is Running

Make sure your `bitcoinblu-cli` daemon is running with:

```ini
# In bitcoinblu.conf
server=1
rpcuser=your_rpc_user
rpcpassword=your_rpc_password
rpcport=8342
txindex=1
```

## Running ElectrumX

### Activate Virtual Environment

```bash
source venv/bin/activate
```

### Start the Server

```bash
electrumx_server
```

### Run in Background

```bash
nohup electrumx_server > electrumx.log 2>&1 &
```

### Check Logs

```bash
tail -f electrumx.log
```

## Systemd Service (Optional)

Create a systemd service for automatic startup:

```bash
sudo nano /etc/systemd/system/electrumx.service
```

Add the following content (adjust paths as needed):

```ini
[Unit]
Description=ElectrumX Server
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/electrumx
Environment="PATH=/path/to/electrumx/venv/bin"
ExecStart=/path/to/electrumx/venv/bin/electrumx_server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable electrumx
sudo systemctl start electrumx
sudo systemctl status electrumx
```

## Troubleshooting

### Python Version

ElectrumX requires Python 3.10 or higher:

```bash
python3 --version
```

If you have an older version, install Python 3.10+:

```bash
sudo apt-get install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-venv python3.10-dev
```

### Database Engine Issues

If you encounter issues with RocksDB, you can use LevelDB instead:

```bash
# In .env file
DB_ENGINE=leveldb
```

### Permission Issues

If you get permission errors for the database directory:

```bash
sudo chown -R $USER:$USER /var/lib/electrumx
```

### Daemon Connection Issues

Verify your daemon is accessible:

```bash
# For BitcoinBLU
bitcoinblu-cli getblockchaininfo

# Test RPC connection
curl --user rpcuser:rpcpassword --data-binary '{"jsonrpc": "1.0", "id":"test", "method": "getblockchaininfo", "params": []}' -H 'content-type: text/plain;' http://localhost:8342/
```

### Out of Memory

If you encounter memory issues during sync, reduce the cache size:

```bash
# In .env file
CACHE_MB=600
```

## Requirements

- **Python**: 3.10 or higher
- **Disk Space**: At least 70-80GB free (for Bitcoin mainnet)
- **RAM**: 2GB minimum, 4GB+ recommended
- **Database**: LevelDB or RocksDB
- **Bitcoin Daemon**: Must have `txindex=1` enabled

## Additional Resources

- [ElectrumX HOWTO](docs/HOWTO.rst) - Detailed documentation
- [BitcoinBLU Setup Guide](BITCOINBLU_SETUP.md) - BitcoinBLU-specific configuration
- [Server Setup Guide](SERVER_SETUP.md) - General server configuration

