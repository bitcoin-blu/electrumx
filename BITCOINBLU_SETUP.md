# BitcoinBLU Setup Guide

This guide explains how to configure ElectrumX to work with BitcoinBLU blockchain.

## Overview

BitcoinBLU is a Bitcoin fork with the following differences:
- **Daemon**: `bitcoinblu-cli` (instead of `bitcoin-cli`)
- **RPC Port**: `8342` (instead of `8332`)
- **Network Name**: `main-blu` (instead of `mainnet`)
- **Address Prefixes**: Different from Bitcoin
- **WIF Prefixes**: Different for compressed/uncompressed keys

## Configuration

### 1. Update `.env` File

Edit your `.env` file with BitcoinBLU settings:

```bash
# Coin and Network
COIN=BitcoinBlu
NET=main-blu

# Database directory
DB_DIRECTORY=/var/lib/electrumx

# BitcoinBLU daemon RPC URL (note port 8342)
DAEMON_URL=http://rpcuser:rpcpassword@host.docker.internal:8342/

# Services
SERVICES=tcp://:50001,rpc://

# Database engine
DB_ENGINE=leveldb

# Cache size
CACHE_MB=1200

# Allow root (needed for Docker)
ALLOW_ROOT=true
```

### 2. BitcoinBLU Daemon Configuration

Ensure your `bitcoinblu.conf` has:

```ini
server=1
rpcuser=your_rpc_user
rpcpassword=your_rpc_password
rpcport=8342
txindex=1
```

### 3. Run the Server

```bash
./docker-dev.sh server
```

## BitcoinBLU Coin Specifications

The BitcoinBLU coin class has been added to ElectrumX with the following parameters:

- **NAME**: `BitcoinBlu`
- **SHORTNAME**: `BBLU`
- **NET**: `main-blu`
- **RPC_PORT**: `8342`
- **P2PKH Prefix**: `0x19` (base58: "B") - from `PUBKEY_ADDRESS`
- **P2SH Prefix**: `0x56` (base58: "b") - from `SCRIPT_ADDRESS`
- **WIF SECRET_KEY**: `0xbc` (188 decimal) - from `SECRET_KEY`
  - Uncompressed: `0xbc` + privkey → base58 starts with "7"
  - Compressed: `0xbc` + privkey + `0x01` → base58 starts with "U"
- **XPUB**: `0x0488b31f`
- **XPRV**: `0x0488afe5`
- **GENESIS_HASH**: `0000000043770b6cd3992ee9602eaa941d8a5de392c1f1baf1f55eb9cd898be6`

## Verification

To verify the coin class is working:

```bash
./docker-dev.sh shell
# Inside container:
source venv/bin/activate
python3 -c "from electrumx.lib.coins import Coin; coin = Coin.lookup_coin_class('BitcoinBlu', 'main-blu'); print(f'Coin: {coin.NAME}, Network: {coin.NET}, RPC Port: {coin.RPC_PORT}')"
```

## Notes

- The coin class uses the standard Bitcoin deserializer (assuming same block format)
- Transaction statistics (TX_COUNT, TX_COUNT_HEIGHT, TX_PER_BLOCK) are set to Bitcoin defaults and may need adjustment based on actual BitcoinBLU chain state
- If BitcoinBLU has different block format or magic bytes, additional deserializer modifications may be needed
- Native segwit (bech32) addresses with "bb" prefix are handled automatically by ElectrumX's segwit support

## Troubleshooting

### Coin Not Found Error

If you get `CoinError: unknown coin BitcoinBlu and network main-blu combination`:
- Ensure the coin class was added to `src/electrumx/lib/coins.py`
- Restart the container: `./docker-dev.sh restart`
- Reinstall in editable mode: `./docker-dev.sh setup`

### Connection Issues

- Verify `bitcoinblu-cli` is running: `bitcoinblu-cli getblockchaininfo`
- Check RPC port is 8342: `bitcoinblu-cli -rpcport=8342 getblockchaininfo`
- For Docker, use `host.docker.internal:8342` in DAEMON_URL (macOS/Windows)
- For Linux Docker, use host IP or `172.17.0.1:8342`

### Address Format Issues

If addresses aren't being recognized:
- Verify P2PKH_VERBYTE and P2SH_VERBYTES are correct
- Check that addresses start with "B" (P2PKH) or "b" (P2SH)

## Additional Resources

- [ElectrumX Environment Variables](docs/environment.rst)
- [Server Setup Guide](SERVER_SETUP.md)
- [Docker Development Guide](DOCKER_DEV.md)

