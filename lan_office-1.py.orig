"""
LAN Office - Local Network Communication & File Transfer Tool
Run this on each PC in your office network.
Requirements: Python 3.8+  (all libraries are built-in except nothing extra needed)
"""

import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import json
import os
import time
import struct

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
BROADCAST_PORT  = 55000   # UDP – user discovery / presence
CHAT_PORT       = 55001   # TCP – chat messages
FILE_PORT       = 55002   # TCP – file transfers
BROADCAST_INTERVAL = 5    # seconds between presence broadcasts
BUFFER_SIZE     = 4096

# ─────────────────────────────────────────────
#  NETWORK HELPERS
# ─────────────────────────────────────────────
def get_local_ip():
    """Return the machine's LAN IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

def get_broadcast_address(local_ip):
    """Return the subnet broadcast address (assumes /24)."""
    parts = local_ip.rsplit(".", 1)
    return parts[0] + ".255"

# ─────────────────────────────────────────────
#  CORE APPLICATION
# ─────────────────────────────────────────────
class LANOfficeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LAN Office")
        self.root.geometry("900x620")
        self.root.minsize(750, 500)
        self.root.configure(bg="#1e1e2e")

        self.username = ""
        self.local_ip = get_local_ip()
        self.broadcast_addr = get_broadcast_address(self.local_ip)

        # {ip: {"name": str, "last_seen": float}}
        self.peers = {}
        self.peers_lock = threading.Lock()

        self.running = False
        self.selected_peer_ip = None   # for direct messages

        self._build_login_screen()

    # ══════════════════════════════════════════
    #  LOGIN SCREEN
    # ══════════════════════════════════════════
    def _build_login_screen(self):
        self.login_frame = tk.Frame(self.root, bg="#1e1e2e")
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(self.login_frame, text="LAN Office", font=("Segoe UI", 28, "bold"),
                 bg="#1e1e2e", fg="#cdd6f4").pack(pady=(0, 6))
        tk.Label(self.login_frame, text="Local Network Communication", font=("Segoe UI", 11),
                 bg="#1e1e2e", fg="#6c7086").pack(pady=(0, 30))

        tk.Label(self.login_frame, text="Your display name:", font=("Segoe UI", 11),
                 bg="#1e1e2e", fg="#cdd6f4").pack(anchor="w")

        self.name_entry = tk.Entry(self.login_frame, font=("Segoe UI", 13),
                                   bg="#313244", fg="#cdd6f4", insertbackground="#cdd6f4",
                                   relief="flat", width=26, bd=8)
        self.name_entry.pack(pady=(4, 14))
        self.name_entry.bind("<Return>", lambda e: self._start_app())

        join_btn = tk.Button(self.login_frame, text="Join Network →",
                             font=("Segoe UI", 12, "bold"),
                             bg="#89b4fa", fg="#1e1e2e", relief="flat",
                             activebackground="#74c7ec", activeforeground="#1e1e2e",
                             padx=20, pady=8, cursor="hand2",
                             command=self._start_app)
        join_btn.pack()

        ip_lbl = tk.Label(self.login_frame,
                          text=f"Your IP: {self.local_ip}",
                          font=("Segoe UI", 9), bg="#1e1e2e", fg="#45475a")
        ip_lbl.pack(pady=(16, 0))

    # ══════════════════════════════════════════
    #  MAIN UI
    # ══════════════════════════════════════════
    def _start_app(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Name required", "Please enter a display name.")
            return
        self.username = name
        self.login_frame.destroy()
        self._build_main_ui()
        self._start_networking()

    def _build_main_ui(self):
        # ── Sidebar (peers) ──────────────────
        sidebar = tk.Frame(self.root, bg="#181825", width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="ONLINE USERS", font=("Segoe UI", 8, "bold"),
                 bg="#181825", fg="#6c7086", padx=12, pady=10).pack(anchor="w")

        self.peers_listbox = tk.Listbox(sidebar, bg="#181825", fg="#cdd6f4",
                                        selectbackground="#313244", selectforeground="#89b4fa",
                                        relief="flat", bd=0, font=("Segoe UI", 11),
                                        activestyle="none", highlightthickness=0)
        self.peers_listbox.pack(fill="both", expand=True, padx=4)
        self.peers_listbox.bind("<<ListboxSelect>>", self._on_peer_select)

        self.peer_status_label = tk.Label(sidebar, text="", font=("Segoe UI", 8),
                                          bg="#181825", fg="#6c7086", pady=4)
        self.peer_status_label.pack()

        # ── Main area ────────────────────────
        main = tk.Frame(self.root, bg="#1e1e2e")
        main.pack(side="right", fill="both", expand=True)

        # Header
        header = tk.Frame(main, bg="#181825", height=48)
        header.pack(fill="x")
        header.pack_propagate(False)

        self.chat_title = tk.Label(header, text="💬  Group Chat",
                                   font=("Segoe UI", 12, "bold"),
                                   bg="#181825", fg="#cdd6f4", padx=16)
        self.chat_title.pack(side="left", pady=10)

        self.dm_clear_btn = tk.Button(header, text="← Back to Group",
                                      font=("Segoe UI", 9), bg="#313244", fg="#89b4fa",
                                      relief="flat", padx=10, cursor="hand2",
                                      command=self._clear_dm_selection)
        # only shown when DM is active

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            main, state="disabled", bg="#1e1e2e", fg="#cdd6f4",
            font=("Segoe UI", 11), relief="flat", bd=0, padx=12, pady=8,
            wrap="word", insertbackground="#cdd6f4"
        )
        self.chat_display.pack(fill="both", expand=True, padx=0, pady=0)

        # Tag styles
        self.chat_display.tag_config("timestamp", foreground="#45475a", font=("Segoe UI", 9))
        self.chat_display.tag_config("name_self",  foreground="#a6e3a1", font=("Segoe UI", 11, "bold"))
        self.chat_display.tag_config("name_other", foreground="#89b4fa", font=("Segoe UI", 11, "bold"))
        self.chat_display.tag_config("name_system",foreground="#f38ba8", font=("Segoe UI", 10, "italic"))
        self.chat_display.tag_config("msg_self",   foreground="#cdd6f4")
        self.chat_display.tag_config("msg_other",  foreground="#cdd6f4")
        self.chat_display.tag_config("msg_system", foreground="#f38ba8", font=("Segoe UI", 10, "italic"))
        self.chat_display.tag_config("file_recv",  foreground="#fab387", font=("Segoe UI", 10))

        # Input bar
        input_bar = tk.Frame(main, bg="#313244", pady=8, padx=8)
        input_bar.pack(fill="x", side="bottom")

        self.msg_entry = tk.Entry(input_bar, font=("Segoe UI", 12),
                                  bg="#45475a", fg="#cdd6f4", insertbackground="#cdd6f4",
                                  relief="flat", bd=6)
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.msg_entry.bind("<Return>", lambda e: self._send_message())

        send_btn = tk.Button(input_bar, text="Send", font=("Segoe UI", 10, "bold"),
                             bg="#89b4fa", fg="#1e1e2e", relief="flat",
                             activebackground="#74c7ec", padx=14, cursor="hand2",
                             command=self._send_message)
        send_btn.pack(side="left")

        file_btn = tk.Button(input_bar, text="📎 File", font=("Segoe UI", 10),
                             bg="#313244", fg="#cdd6f4", relief="flat",
                             activebackground="#45475a", padx=10, cursor="hand2",
                             command=self._send_file_dialog)
        file_btn.pack(side="left", padx=(6, 0))

        self._log_system("Welcome to LAN Office! Discovering peers on your network…")

    # ══════════════════════════════════════════
    #  CHAT HELPERS
    # ══════════════════════════════════════════
    def _log_message(self, sender_name, text, is_self=False):
        ts = time.strftime("%H:%M")
        self.chat_display.config(state="normal")
        self.chat_display.insert("end", f"[{ts}] ", "timestamp")
        tag = "name_self" if is_self else "name_other"
        msg_tag = "msg_self" if is_self else "msg_other"
        self.chat_display.insert("end", f"{sender_name}: ", tag)
        self.chat_display.insert("end", text + "\n", msg_tag)
        self.chat_display.config(state="disabled")
        self.chat_display.see("end")

    def _log_system(self, text):
        self.chat_display.config(state="normal")
        ts = time.strftime("%H:%M")
        self.chat_display.insert("end", f"[{ts}] ● {text}\n", "msg_system")
        self.chat_display.config(state="disabled")
        self.chat_display.see("end")

    def _log_file(self, text):
        self.chat_display.config(state="normal")
        self.chat_display.insert("end", f"  📁 {text}\n", "file_recv")
        self.chat_display.config(state="disabled")
        self.chat_display.see("end")

    # ══════════════════════════════════════════
    #  PEER SELECTION (DM vs GROUP)
    # ══════════════════════════════════════════
    def _on_peer_select(self, event):
        sel = self.peers_listbox.curselection()
        if not sel:
            return
        label = self.peers_listbox.get(sel[0])
        # find IP for this label
        with self.peers_lock:
            for ip, info in self.peers.items():
                display = f"🟢 {info['name']}"
                if display == label:
                    self.selected_peer_ip = ip
                    self.chat_title.config(text=f"💬  DM → {info['name']}")
                    self.dm_clear_btn.pack(side="right", pady=6, padx=10)
                    return

    def _clear_dm_selection(self):
        self.selected_peer_ip = None
        self.peers_listbox.selection_clear(0, "end")
        self.chat_title.config(text="💬  Group Chat")
        self.dm_clear_btn.pack_forget()

    # ══════════════════════════════════════════
    #  SENDING
    # ══════════════════════════════════════════
    def _send_message(self):
        text = self.msg_entry.get().strip()
        if not text:
            return
        self.msg_entry.delete(0, "end")
        self._log_message(self.username, text, is_self=True)

        payload = json.dumps({
            "type": "chat",
            "name": self.username,
            "text": text,
            "dm": False
        }).encode()

        if self.selected_peer_ip:
            # DM – send only to selected peer
            threading.Thread(target=self._tcp_send,
                             args=(self.selected_peer_ip, CHAT_PORT, payload),
                             daemon=True).start()
        else:
            # Broadcast to all peers
            with self.peers_lock:
                targets = list(self.peers.keys())
            for ip in targets:
                threading.Thread(target=self._tcp_send,
                                 args=(ip, CHAT_PORT, payload),
                                 daemon=True).start()

    def _tcp_send(self, ip, port, data):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((ip, port))
            # Prefix length so receiver knows where message ends
            s.sendall(struct.pack("!I", len(data)) + data)
            s.close()
        except Exception:
            pass

    def _send_file_dialog(self):
        target_ip = self.selected_peer_ip
        if not target_ip:
            # Ask user to select a peer first
            with self.peers_lock:
                peer_count = len(self.peers)
            if peer_count == 0:
                messagebox.showinfo("No peers", "No peers online yet.")
                return
            messagebox.showinfo("Select a recipient",
                                "Click a user in the sidebar first, then press 📎 File.")
            return

        path = filedialog.askopenfilename(title="Select a file to send")
        if not path:
            return

        threading.Thread(target=self._send_file,
                         args=(target_ip, path),
                         daemon=True).start()

    def _send_file(self, ip, path):
        try:
            filename = os.path.basename(path)
            filesize = os.path.getsize(path)

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(30)
            s.connect((ip, FILE_PORT))

            # Header: JSON metadata
            meta = json.dumps({
                "filename": filename,
                "filesize": filesize,
                "sender": self.username
            }).encode()
            s.sendall(struct.pack("!I", len(meta)) + meta)

            # File data
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    s.sendall(chunk)
            s.close()

            self.root.after(0, self._log_file,
                            f"Sent '{filename}' ({self._fmt_size(filesize)}) to "
                            f"{self.peers.get(ip, {}).get('name', ip)}")
        except Exception as e:
            self.root.after(0, self._log_system, f"File send failed: {e}")

    @staticmethod
    def _fmt_size(n):
        for unit in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} TB"

    # ══════════════════════════════════════════
    #  NETWORKING – START
    # ══════════════════════════════════════════
    def _start_networking(self):
        self.running = True
        threading.Thread(target=self._broadcast_presence, daemon=True).start()
        threading.Thread(target=self._listen_presence,    daemon=True).start()
        threading.Thread(target=self._listen_chat,        daemon=True).start()
        threading.Thread(target=self._listen_file,        daemon=True).start()
        threading.Thread(target=self._prune_peers,        daemon=True).start()

    # ── Presence (UDP broadcast) ─────────────
    def _broadcast_presence(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        payload = json.dumps({"type": "presence", "name": self.username,
                              "ip": self.local_ip}).encode()
        while self.running:
            try:
                sock.sendto(payload, (self.broadcast_addr, BROADCAST_PORT))
            except Exception:
                pass
            time.sleep(BROADCAST_INTERVAL)
        sock.close()

    def _listen_presence(self):
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
            except socket.timeout:
                pass
            except Exception:
                pass
        sock.close()

    def _on_peer_join(self, ip, name):
        self._log_system(f"{name} joined the network.")
        self._refresh_peers_list()

    def _prune_peers(self):
        """Remove peers not seen for 15 seconds."""
        while self.running:
            time.sleep(5)
            now = time.time()
            stale = []
            with self.peers_lock:
                for ip, info in list(self.peers.items()):
                    if now - info["last_seen"] > 15:
                        stale.append((ip, info["name"]))
                        del self.peers[ip]
            for ip, name in stale:
                self.root.after(0, self._on_peer_leave, name)

    def _on_peer_leave(self, name):
        self._log_system(f"{name} left the network.")
        self._refresh_peers_list()

    def _refresh_peers_list(self):
        self.peers_listbox.delete(0, "end")
        with self.peers_lock:
            for ip, info in self.peers.items():
                self.peers_listbox.insert("end", f"🟢 {info['name']}")
        count = self.peers_listbox.size()
        self.peer_status_label.config(
            text=f"{count} user{'s' if count != 1 else ''} online")

    # ── Chat (TCP listener) ──────────────────
    def _listen_chat(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("", CHAT_PORT))
        srv.listen(10)
        srv.settimeout(1)
        while self.running:
            try:
                conn, addr = srv.accept()
                threading.Thread(target=self._handle_chat,
                                 args=(conn, addr), daemon=True).start()
            except socket.timeout:
                pass
        srv.close()

    def _handle_chat(self, conn, addr):
        try:
            raw_len = conn.recv(4)
            if len(raw_len) < 4:
                return
            msg_len = struct.unpack("!I", raw_len)[0]
            data = b""
            while len(data) < msg_len:
                chunk = conn.recv(min(BUFFER_SIZE, msg_len - len(data)))
                if not chunk:
                    break
                data += chunk
            msg = json.loads(data.decode())
            if msg.get("type") == "chat":
                self.root.after(0, self._log_message,
                                msg["name"], msg["text"], False)
        except Exception:
            pass
        finally:
            conn.close()

    # ── File transfer (TCP listener) ─────────
    def _listen_file(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("", FILE_PORT))
        srv.listen(5)
        srv.settimeout(1)
        while self.running:
            try:
                conn, addr = srv.accept()
                threading.Thread(target=self._handle_file,
                                 args=(conn, addr), daemon=True).start()
            except socket.timeout:
                pass
        srv.close()

    def _handle_file(self, conn, addr):
        try:
            raw_len = conn.recv(4)
            if len(raw_len) < 4:
                return
            meta_len = struct.unpack("!I", raw_len)[0]
            meta_data = b""
            while len(meta_data) < meta_len:
                chunk = conn.recv(min(BUFFER_SIZE, meta_len - len(meta_data)))
                if not chunk:
                    break
                meta_data += chunk

            meta = json.loads(meta_data.decode())
            filename = meta["filename"]
            filesize = meta["filesize"]
            sender   = meta.get("sender", addr[0])

            # Ask user where to save (on main thread)
            save_path_holder = [None]
            done_event = threading.Event()

            def ask_save():
                answer = messagebox.askyesno(
                    "Incoming File",
                    f"{sender} wants to send you:\n{filename} "
                    f"({self._fmt_size(filesize)})\n\nAccept?")
                if answer:
                    p = filedialog.asksaveasfilename(
                        initialfile=filename,
                        title="Save file as")
                    save_path_holder[0] = p
                done_event.set()

            self.root.after(0, ask_save)
            done_event.wait(timeout=60)

            save_path = save_path_holder[0]
            if not save_path:
                conn.close()
                return

            received = 0
            with open(save_path, "wb") as f:
                while received < filesize:
                    chunk = conn.recv(min(BUFFER_SIZE, filesize - received))
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)

            self.root.after(0, self._log_file,
                            f"Received '{filename}' from {sender} → saved to {save_path}")
        except Exception as e:
            self.root.after(0, self._log_system, f"File receive error: {e}")
        finally:
            conn.close()

    # ══════════════════════════════════════════
    #  CLEANUP
    # ══════════════════════════════════════════
    def on_close(self):
        self.running = False
        self.root.destroy()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = LANOfficeApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
