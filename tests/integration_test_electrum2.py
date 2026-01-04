import socket, json

HOST = "electrumx.bitcoin-blu.org"
PORT = 50001

def send_request(s, method, params=None, request_id=1):
    """Send a request and return the response with matching id"""
    req = {"id": request_id, "method": method, "params": params or []}
    s.sendall((json.dumps(req) + "\n").encode())
    
    # Read response(s) - may receive notifications first
    buffer = ""
    while True:
        data = s.recv(4096).decode()
        if not data:
            break
        buffer += data
        # Try to find our response (has matching id)
        lines = buffer.split('\n')
        for line in lines[:-1]:  # Process complete lines
            if line.strip():
                try:
                    resp = json.loads(line)
                    if 'id' in resp and resp['id'] == request_id:
                        return json.dumps(resp, indent=2)
                except json.JSONDecodeError:
                    pass
        # Keep incomplete line in buffer
        buffer = lines[-1]
    return buffer

# Use persistent connection for all calls
with socket.create_connection((HOST, PORT), timeout=5) as s:
    print("1. server.version →")
    print(send_request(s, "server.version", ["integration_test", "1.4"], request_id=1))
    
    print("\n2. server.features →")
    print(send_request(s, "server.features", request_id=2))
    
    print("\n3. blockchain.headers.subscribe →")
    print(send_request(s, "blockchain.headers.subscribe", request_id=3))
