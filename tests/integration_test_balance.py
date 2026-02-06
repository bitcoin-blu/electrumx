import socket
import json
import time
import logging
import sys
from datetime import datetime
from hashlib import sha256

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Configuration
HOST = "electrumx.bitcoin-blu.org"
PORT = 50001
TIMEOUT = 30  # seconds - increased from 5 for production debugging
RECV_BUFFER_SIZE = 4096

ADDRESSES = [
    "bb1q4gvrjugztv8fflpznjjmfjy02sz0amjtn0grk0",  # bech32
    "BDDh5sYMZRprgXrJ4Ki1npt2n6Qh3pUVCX",  # base58 P2PKH
    "BBQhaT9zSDjSutWYqpLY8VhFZzPzfRFtoz",  # base58 P2PKH
]

def bech32_polymod(values):
    """Internal function for bech32 checksum calculation."""
    generator = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk

def bech32_verify_checksum(hrp, data):
    """Verify a bech32 checksum."""
    return bech32_polymod(bech32_hrp_expand(hrp) + data) == 1

def bech32_hrp_expand(hrp):
    """Expand the HRP into values for checksum computation."""
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]

def bech32_decode(bech):
    """Validate a Bech32 string, and determine HRP and data."""
    if ((any(ord(x) < 33 or ord(x) > 126 for x in bech)) or
            (bech.lower() != bech and bech.upper() != bech)):
        return (None, None)
    bech = bech.lower()
    pos = bech.rfind('1')
    if pos < 1 or pos + 7 > len(bech) or len(bech) > 90:
        return (None, None)
    if not all(x in 'qpzry9x8gf2tvdw0s3jn54khce6mua7l' for x in bech[pos+1:]):
        return (None, None)
    hrp = bech[:pos]
    data = [BECH32_CHARSET.find(x) for x in bech[pos+1:]]
    if not bech32_verify_checksum(hrp, data):
        return (None, None)
    return (hrp, data[:-6])

BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

def convertbits(data, frombits, tobits, pad=True):
    """General power-of-2 base conversion."""
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            return None
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret

def base58_decode_check(s):
    """Decode a base58check-encoded string."""
    BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    
    # Convert from base58
    num = 0
    for char in s:
        num = num * 58 + BASE58_ALPHABET.index(char)
    
    # Convert to bytes
    byte_array = []
    while num > 0:
        byte_array.insert(0, num % 256)
        num //= 256
    
    # Add leading zeros
    leading_zeros = 0
    for char in s:
        if char == '1':
            leading_zeros += 1
        else:
            break
    byte_array = [0] * leading_zeros + byte_array
    
    # Verify checksum
    if len(byte_array) < 4:
        raise ValueError("Address too short")
    
    payload = bytes(byte_array[:-4])
    checksum = bytes(byte_array[-4:])
    hash_result = sha256(sha256(payload).digest()).digest()
    
    if hash_result[:4] != checksum:
        raise ValueError("Invalid checksum")
    
    return payload

def address_to_scripthash(address):
    """Convert a BitcoinBLU address (bech32 or base58) to Electrum script hash format.
    
    The Electrum protocol uses script hashes which are:
    - SHA256 of the script
    - Reversed bytes
    - Hex encoded
    """
    # BitcoinBLU address prefixes
    P2PKH_VERBYTE = 0x19  # "B" prefix
    P2SH_VERBYTE = 0x56   # "b" prefix
    
    # Try bech32 first (starts with "bb1")
    if address.startswith("bb1"):
        hrp, data = bech32_decode(address)
        if hrp is not None and data is not None:
            # Convert from 5-bit to 8-bit
            decoded = convertbits(data[1:], 5, 8, False)
            if decoded is None or len(decoded) < 2 or len(decoded) > 40:
                raise ValueError(f"Invalid bech32 data length")
            
            # Get witness version (first 5-bit value)
            witness_version = data[0]
            if witness_version > 16:
                raise ValueError(f"Invalid witness version: {witness_version}")
            
            # For P2WPKH (witness version 0, 20 bytes) or P2WSH (witness version 0, 32 bytes)
            if witness_version == 0:
                if len(decoded) == 20:  # P2WPKH
                    script = bytes([0x00, 0x14]) + bytes(decoded)
                elif len(decoded) == 32:  # P2WSH
                    script = bytes([0x00, 0x20]) + bytes(decoded)
                else:
                    raise ValueError(f"Invalid witness program length: {len(decoded)}")
            else:
                # For witness version > 0, use OP_1 to OP_16
                script = bytes([0x50 + witness_version]) + bytes([len(decoded)]) + bytes(decoded)
        else:
            raise ValueError(f"Invalid bech32 address: {address}")
    else:
        # Try base58 (P2PKH or P2SH)
        try:
            decoded = base58_decode_check(address)
            
            if len(decoded) != 21:  # 1 byte version + 20 bytes hash160
                raise ValueError(f"Invalid address length: {len(decoded)}")
            
            verbyte = decoded[0]
            hash160 = decoded[1:]
            
            # Create script based on version byte
            if verbyte == P2PKH_VERBYTE:
                # P2PKH script: OP_DUP OP_HASH160 <hash160> OP_EQUALVERIFY OP_CHECKSIG
                script = bytes([0x76, 0xa9, 0x14]) + hash160 + bytes([0x88, 0xac])
            elif verbyte == P2SH_VERBYTE:
                # P2SH script: OP_HASH160 <hash160> OP_EQUAL
                script = bytes([0xa9, 0x14]) + hash160 + bytes([0x87])
            else:
                raise ValueError(f"Unknown address version byte: {verbyte:02x}")
        except Exception as e:
            raise ValueError(f"Invalid base58 address {address}: {e}")
    
    # Hash with SHA256
    script_hash = sha256(script).digest()
    # Reverse the bytes (Electrum protocol requirement)
    script_hash_reversed = script_hash[::-1]
    # Convert to hex string
    return script_hash_reversed.hex()


def dns_resolve(host):
    """Resolve hostname and log all IPs."""
    logger.info(f"DNS: Resolving {host}...")
    start = time.perf_counter()
    try:
        ips = socket.getaddrinfo(host, PORT, socket.AF_INET, socket.SOCK_STREAM)
        elapsed = (time.perf_counter() - start) * 1000
        unique_ips = list(set(ip[4][0] for ip in ips))
        logger.info(f"DNS: Resolved to {unique_ips} in {elapsed:.2f}ms")
        return unique_ips
    except socket.gaierror as e:
        elapsed = (time.perf_counter() - start) * 1000
        logger.error(f"DNS: Resolution failed after {elapsed:.2f}ms - {e}")
        raise


def create_connection_with_logging(host, port, timeout):
    """Create a socket connection with detailed logging."""
    logger.info(f"CONNECTION: Attempting to connect to {host}:{port} (timeout={timeout}s)")
    
    # DNS resolution
    ips = dns_resolve(host)
    
    # Try to connect
    start = time.perf_counter()
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        elapsed = (time.perf_counter() - start) * 1000
        
        # Get socket info
        local_addr = sock.getsockname()
        remote_addr = sock.getpeername()
        
        logger.info(f"CONNECTION: Established in {elapsed:.2f}ms")
        logger.info(f"CONNECTION: Local  = {local_addr[0]}:{local_addr[1]}")
        logger.info(f"CONNECTION: Remote = {remote_addr[0]}:{remote_addr[1]}")
        
        # Log socket options
        tcp_nodelay = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY)
        so_keepalive = sock.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE)
        logger.debug(f"CONNECTION: TCP_NODELAY={tcp_nodelay}, SO_KEEPALIVE={so_keepalive}")
        
        return sock
    except socket.timeout as e:
        elapsed = (time.perf_counter() - start) * 1000
        logger.error(f"CONNECTION: Timeout after {elapsed:.2f}ms - {e}")
        raise
    except socket.error as e:
        elapsed = (time.perf_counter() - start) * 1000
        logger.error(f"CONNECTION: Failed after {elapsed:.2f}ms - {e}")
        raise


def send_request(s, method, params=None, request_id=1):
    """Send a request and return the response with matching id, with detailed logging."""
    req = {"id": request_id, "method": method, "params": params or []}
    req_json = json.dumps(req) + "\n"
    req_bytes = req_json.encode()
    
    # Log the request
    logger.info(f"REQUEST [{request_id}]: {method}")
    logger.debug(f"REQUEST [{request_id}]: Params = {params}")
    logger.debug(f"REQUEST [{request_id}]: Payload size = {len(req_bytes)} bytes")
    
    # Send with timing
    send_start = time.perf_counter()
    try:
        bytes_sent = s.sendall(req_bytes)
        send_elapsed = (time.perf_counter() - send_start) * 1000
        logger.info(f"REQUEST [{request_id}]: Sent {len(req_bytes)} bytes in {send_elapsed:.2f}ms")
    except socket.error as e:
        send_elapsed = (time.perf_counter() - send_start) * 1000
        logger.error(f"REQUEST [{request_id}]: Send failed after {send_elapsed:.2f}ms - {e}")
        raise
    
    # Receive with timing
    recv_start = time.perf_counter()
    buffer = ""
    total_bytes_received = 0
    recv_count = 0
    
    while True:
        recv_chunk_start = time.perf_counter()
        try:
            logger.debug(f"RESPONSE [{request_id}]: Waiting for data (recv #{recv_count + 1})...")
            data = s.recv(RECV_BUFFER_SIZE)
            recv_chunk_elapsed = (time.perf_counter() - recv_chunk_start) * 1000
            recv_count += 1
            
            if not data:
                logger.warning(f"RESPONSE [{request_id}]: Connection closed by server (recv #{recv_count}, {recv_chunk_elapsed:.2f}ms)")
                break
            
            decoded_data = data.decode()
            total_bytes_received += len(data)
            logger.debug(f"RESPONSE [{request_id}]: Received {len(data)} bytes in {recv_chunk_elapsed:.2f}ms (recv #{recv_count}, total: {total_bytes_received} bytes)")
            
            buffer += decoded_data
            
            # Try to find our response (has matching id)
            lines = buffer.split('\n')
            for line in lines[:-1]:  # Process complete lines
                if line.strip():
                    try:
                        resp = json.loads(line)
                        if 'id' in resp and resp['id'] == request_id:
                            total_elapsed = (time.perf_counter() - recv_start) * 1000
                            logger.info(f"RESPONSE [{request_id}]: Complete! {total_bytes_received} bytes in {total_elapsed:.2f}ms ({recv_count} recv calls)")
                            
                            if 'error' in resp:
                                logger.warning(f"RESPONSE [{request_id}]: Server returned error: {resp['error']}")
                            else:
                                result_preview = str(resp.get('result', ''))[:100]
                                logger.debug(f"RESPONSE [{request_id}]: Result preview: {result_preview}...")
                            
                            return json.dumps(resp, indent=2)
                        else:
                            # Log unexpected messages (notifications, etc.)
                            if 'method' in resp:
                                logger.debug(f"RESPONSE [{request_id}]: Received notification: {resp.get('method')}")
                            else:
                                logger.debug(f"RESPONSE [{request_id}]: Received message with different id: {resp.get('id')}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"RESPONSE [{request_id}]: JSON decode error on line: {line[:50]}... - {e}")
            
            # Keep incomplete line in buffer
            buffer = lines[-1]
            
        except socket.timeout as e:
            recv_chunk_elapsed = (time.perf_counter() - recv_chunk_start) * 1000
            total_elapsed = (time.perf_counter() - recv_start) * 1000
            logger.error(f"RESPONSE [{request_id}]: TIMEOUT after {total_elapsed:.2f}ms total ({recv_count} recv calls, {total_bytes_received} bytes received)")
            logger.error(f"RESPONSE [{request_id}]: Buffer content: {buffer[:200]}...")
            raise
        except socket.error as e:
            recv_chunk_elapsed = (time.perf_counter() - recv_chunk_start) * 1000
            total_elapsed = (time.perf_counter() - recv_start) * 1000
            logger.error(f"RESPONSE [{request_id}]: Socket error after {total_elapsed:.2f}ms - {e}")
            raise
    
    total_elapsed = (time.perf_counter() - recv_start) * 1000
    logger.warning(f"RESPONSE [{request_id}]: Loop ended without finding response. Buffer: {buffer[:200]}...")
    return buffer


def main():
    """Main test function with comprehensive logging."""
    logger.info("=" * 80)
    logger.info("ElectrumX Integration Test - Balance Query")
    logger.info("=" * 80)
    logger.info(f"Target: {HOST}:{PORT}")
    logger.info(f"Timeout: {TIMEOUT}s")
    logger.info(f"Addresses to query: {len(ADDRESSES)}")
    logger.info("=" * 80)
    
    # Convert addresses to script hashes
    logger.info("PHASE 1: Converting addresses to script hashes")
    address_scripthashes = {}
    for address in ADDRESSES:
        try:
            start = time.perf_counter()
            scripthash = address_to_scripthash(address)
            elapsed = (time.perf_counter() - start) * 1000
            address_scripthashes[address] = scripthash
            logger.info(f"  {address[:20]}... -> {scripthash[:16]}... ({elapsed:.2f}ms)")
        except Exception as e:
            logger.error(f"  {address}: FAILED - {e}")
    
    logger.info("")
    logger.info("PHASE 2: Connecting to ElectrumX server")
    
    try:
        sock = create_connection_with_logging(HOST, PORT, TIMEOUT)
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return 1
    
    try:
        logger.info("")
        logger.info("PHASE 3: Protocol handshake (server.version)")
        print("\n1. server.version →")
        result = send_request(sock, "server.version", ["integration_test_balance", "1.4"], request_id=1)
        print(result)
        
        # Query balance for each address
        logger.info("")
        logger.info("PHASE 4: Querying balances")
        request_id = 2
        for address, scripthash in address_scripthashes.items():
            print(f"\n{'='*70}")
            print(f"Address: {address}")
            print(f"{'='*70}")
            
            logger.info(f"Querying balance for {address[:30]}...")
            print(f"\nblockchain.scripthash.get_balance →")
            
            query_start = time.perf_counter()
            result = send_request(sock, "blockchain.scripthash.get_balance", [scripthash], request_id=request_id)
            query_elapsed = (time.perf_counter() - query_start) * 1000
            
            print(result)
            logger.info(f"Balance query completed in {query_elapsed:.2f}ms")
            
            # Parse and display balance nicely
            try:
                resp = json.loads(result)
                if 'result' in resp:
                    balance = resp['result']
                    confirmed = balance.get('confirmed', 0)
                    unconfirmed = balance.get('unconfirmed', 0)
                    total = confirmed + unconfirmed
                    
                    # Convert satoshis to BBLU (1 BBLU = 100,000,000 satoshis)
                    confirmed_bblu = confirmed / 100_000_000
                    unconfirmed_bblu = unconfirmed / 100_000_000
                    total_bblu = total / 100_000_000
                    
                    print(f"\nBalance Summary:")
                    print(f"  Confirmed:   {confirmed:,} satoshis ({confirmed_bblu:.8f} BBLU)")
                    print(f"  Unconfirmed: {unconfirmed:,} satoshis ({unconfirmed_bblu:.8f} BBLU)")
                    print(f"  Total:       {total:,} satoshis ({total_bblu:.8f} BBLU)")
                    
                    logger.info(f"  Balance: {total_bblu:.8f} BBLU (confirmed: {confirmed_bblu:.8f}, unconfirmed: {unconfirmed_bblu:.8f})")
                elif 'error' in resp:
                    print(f"\nError: {resp['error']}")
                    logger.error(f"  Server error: {resp['error']}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"\nCould not parse balance: {e}")
                logger.error(f"  Parse error: {e}")
            
            request_id += 1
        
        logger.info("")
        logger.info("PHASE 5: Test completed successfully")
        return 0
        
    except socket.timeout as e:
        logger.error(f"TIMEOUT: {e}")
        return 1
    except socket.error as e:
        logger.error(f"SOCKET ERROR: {e}")
        return 1
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    finally:
        logger.info("Closing connection...")
        try:
            sock.close()
            logger.info("Connection closed")
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
