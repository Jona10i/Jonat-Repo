import os

path = r"c:\Users\HomePC\Downloads\Documents\lan_office-1.py"

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Refactor _listen_presence
old_listen_presence = """    def _listen_presence(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", BROADCAST_PORT))
        sock.settimeout(1)
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                msg = json.loads(data.decode())
                if msg.get("type") == "presence" and addr[0] != self.local_ip:
                    ip = addr[0]
                    name = msg.get("name", ip)
                    with self.peers_lock:
                        is_new = ip not in self.peers
                        self.peers[ip] = {"name": name, "last_seen": time.time()}
                    if is_new:
                        self.root.after(0, self._on_peer_join, ip, name)
                    else:
                        self.root.after(0, self._refresh_peers_list)
                elif msg.get("type") == "leave":
                    ip = addr[0]
                    name = msg.get("name", ip)
                    with self.peers_lock:
                        if ip in self.peers:
                            del self.peers[ip]
                    self.root.after(0, self._on_peer_leave, ip, name)
            except socket.timeout:
                pass
            except Exception as e:
                self.logger.error(f"Presence listen error: {e}")
        sock.close()"""

new_listen_presence = """    def _listen_presence(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", BROADCAST_PORT))
        sock.settimeout(1)
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                self._handle_presence_data(data, addr)
            except socket.timeout:
                pass
            except Exception as e:
                self.logger.error(f"Presence listen error: {e}")
        sock.close()

    def _handle_presence_data(self, data, addr):
        try:
            msg = json.loads(data.decode())
            mtype = msg.get("type")
            if mtype == "presence" and addr[0] != self.local_ip:
                self._update_peer_presence(addr[0], msg.get("name", addr[0]))
            elif mtype == "leave":
                self._remove_peer(addr[0], msg.get("name", addr[0]))
        except Exception:
            pass

    def _update_peer_presence(self, ip, name):
        with self.peers_lock:
            is_new = ip not in self.peers
            self.peers[ip] = {"name": name, "last_seen": time.time()}
        if is_new:
            self.root.after(0, self._on_peer_join, ip, name)
        else:
            self.root.after(0, self._refresh_peers_list)

    def _remove_peer(self, ip, name):
        with self.peers_lock:
            if ip in self.peers:
                del self.peers[ip]
        self.root.after(0, self._on_peer_leave, ip, name)"""

if old_listen_presence in content:
    content = content.replace(old_listen_presence, new_listen_presence)
    print("Refactored _listen_presence")
else:
    # Try with CRLF
    old_listen_presence_crlf = old_listen_presence.replace('\\n', '\\r\\n')
    if old_listen_presence_crlf in content:
        content = content.replace(old_listen_presence_crlf, new_listen_presence.replace('\\n', '\\r\\n'))
        print("Refactored _listen_presence (CRLF)")
    else:
        print("Failed to find _listen_presence")

# Refactor _handle_file
# (Similar logic...)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
