import socket, json

HOST = "electrumx.bitcoin-blu.org"
PORT = 50001   # use 50002 with SSL wrapper if needed

req = {
    "id": 1,
    "method": "server.version",
    "params": ["probe", "1.4"]
}

with socket.create_connection((HOST, PORT), timeout=5) as s:
    s.sendall((json.dumps(req) + "\n").encode())
    resp = s.recv(4096).decode()
    print("Response:", resp)