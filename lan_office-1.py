"""
LAN Office - Local Network Communication & File Transfer Tool
Run this on each PC in your office network.
Requirements: Python 3.8+  (all libraries are built-in except nothing extra needed)
"""

import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, simpledialog
import json
import os
import time
import struct
import logging
import traceback

# ---------------------------------------------
#  CONFIGURATION
# ---------------------------------------------
DEFAULT_FONT_FAMILY = "Segoe UI"
BROADCAST_PORT  = 55000   # UDP – user discovery / presence
CHAT_PORT       = 55001   # TCP – chat messages
FILE_PORT       = 55002   # TCP – file transfers
BROADCAST_INTERVAL = 5    # seconds between presence broadcasts
CHAT_HISTORY_FILE = "chat_history.jsonl"
MAX_HISTORY_LOAD = 100
BUFFER_SIZE     = 4096
CONFIG_FILE     = "lan_config.json"

# ---------------------------------------------
#  NETWORK HELPERS
# ---------------------------------------------
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
    """Return the subnet broadcast address (tries to be smart)."""
    try:
        import ipaddress
        # Assumes /24 by default, but attempts to be robust
        net = ipaddress.IPv4Network(f"{local_ip}/255.255.255.0", strict=False)
        return str(net.broadcast_address)
    except Exception:
        parts = local_ip.rsplit(".", 1)
        return parts[0] + ".255"

# ---------------------------------------------
#  CORE APPLICATION
# ---------------------------------------------
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

        # Set up logging
        self.logger = logging.getLogger(f"LANOffice-{self.local_ip}")
        self.logger.setLevel(logging.DEBUG)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(ch_formatter)

        # File handler
        fh = logging.FileHandler('lan_office.log', encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(fh_formatter)

        self.logger.addHandler(ch)
        self.logger.addHandler(fh)

        self.logger.info(f"LAN Office started. IP: {self.local_ip}, Broadcast: {self.broadcast_addr}")

        # Set Icon
        try:
            icon_path = "app_icon.png"
            if os.path.exists(icon_path):
                self.icon_img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, self.icon_img)
        except Exception:
            self.logger.debug("Failed to load app icon", exc_info=True)

        # {ip: {"name": str, "last_seen": float}}
        self.peers = {}
        self.peers_lock = threading.Lock()

        self.running = False
        self.selected_peer_ip = None   # for direct messages
        self.cancel_transfer = False

        self.chat_history = []
        self.chat_history_lock = threading.Lock()

        self._load_config()
        self._build_login_screen()

    # ==========================================
    #  CONFIG & PERSISTENCE
    # ==========================================
    def _load_config(self):
        self.config = {"username": "", "download_dir": ""}
        self.username = ""
        self.download_dir = ""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.config = json.load(f)
                    self.username = self.config.get("username", "")
                    self.download_dir = self.config.get("download_dir", "")
            except Exception:
                self.logger.debug("Failed to load config file", exc_info=True)

    def _save_config(self):
        self.config["username"] = self.username
        self.config["download_dir"] = self.download_dir
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f)
        except Exception:
            self.logger.error("Failed to save config", exc_info=True)

    def _load_chat_history(self):
        """Load recent chat history from file."""
        if not os.path.exists(CHAT_HISTORY_FILE):
            return
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines[-MAX_HISTORY_LOAD:]:
                try:
                    msg = json.loads(line.strip())
                    self.chat_history.append(msg)
                except Exception:
                    continue
        except Exception as e:
            self.logger.debug(f"Failed to load chat history: {e}")

    def _save_message(self, sender_name, text, is_self=False, is_system=False, filename=None):
        """Save a message to history file."""
        msg = {
            "timestamp": time.time(),
            "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
            "sender": sender_name,
            "text": text,
            "is_self": is_self,
            "is_system": is_system,
            "filename": filename
        }
        with self.chat_history_lock:
            self.chat_history.append(msg)
        try:
            with open(CHAT_HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(msg) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to save message: {e}")

    # ==========================================
    #  LOGIN SCREEN
    # ==========================================
    def _build_login_screen(self):
        self.login_frame = tk.Frame(self.root, bg="#1e1e2e")
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(self.login_frame, text="LAN Office", font=(DEFAULT_FONT_FAMILY, 28, "bold"),
                 bg="#1e1e2e", fg="#cdd6f4").pack(pady=(0, 6))
        tk.Label(self.login_frame, text="Local Network Communication", font=(DEFAULT_FONT_FAMILY, 11),
                 bg="#1e1e2e", fg="#6c7086").pack(pady=(0, 30))

        tk.Label(self.login_frame, text="Your display name:", font=(DEFAULT_FONT_FAMILY, 11),
                 bg="#1e1e2e", fg="#cdd6f4").pack(anchor="w")

        self.name_entry = tk.Entry(self.login_frame, font=(DEFAULT_FONT_FAMILY, 13),
                                   bg="#313244", fg="#cdd6f4", insertbackground="#cdd6f4",
                                   relief="flat", width=26, bd=8)
        self.name_entry.pack(pady=(4, 14))
        if self.username:
            self.name_entry.insert(0, self.username)
            self.name_entry.selection_range(0, "end")
        self.name_entry.bind("<Return>", lambda e: self._start_app())

        join_btn = tk.Button(self.login_frame, text="Join Network →",
                             font=(DEFAULT_FONT_FAMILY, 12, "bold"),
                             bg="#89b4fa", fg="#1e1e2e", relief="flat",
                             activebackground="#74c7ec", activeforeground="#1e1e2e",
                             padx=20, pady=8, cursor="hand2",
                             command=self._start_app)
        join_btn.pack()

        ip_lbl = tk.Label(self.login_frame,
                          text=f"Your IP: {self.local_ip}",
                          font=(DEFAULT_FONT_FAMILY, 9), bg="#1e1e2e", fg="#45475a")
        ip_lbl.pack(pady=(16, 0))

    # ==========================================
    #  MAIN UI
    # ==========================================
    def _start_app(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Name required", "Please enter a display name.")
            return
        self.username = name
        self._save_config()
        self.login_frame.destroy()
        self._build_main_ui()
        self._load_chat_history()
        # Replay history
        for msg in self.chat_history:
            if msg.get("is_system"):
                self._log_system(msg["text"])
            elif msg.get("filename"):
                self._log_file(f"Received '{msg['filename']}' from {msg['sender']} → saved to [previous location]", filename=msg["filename"])
            else:
                self._log_message(msg["sender"], msg["text"], is_self=msg.get("is_self", False))
        self._start_networking()

    def _build_main_ui(self):
        # -- Sidebar (peers) ------------------
        sidebar = tk.Frame(self.root, bg="#181825", width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="ONLINE USERS", font=(DEFAULT_FONT_FAMILY, 8, "bold"),
                 bg="#181825", fg="#6c7086", padx=12, pady=10).pack(anchor="w")

        self.peers_listbox = tk.Listbox(sidebar, bg="#181825", fg="#cdd6f4",
                                        selectbackground="#313244", selectforeground="#89b4fa",
                                        relief="flat", bd=0, font=(DEFAULT_FONT_FAMILY, 11),
                                        activestyle="none", highlightthickness=0)
        self.peers_listbox.pack(fill="both", expand=True, padx=4)
        self.peers_listbox.bind("<<ListboxSelect>>", self._on_peer_select)

        self.peer_status_label = tk.Label(sidebar, text="", font=(DEFAULT_FONT_FAMILY, 8),
                                          bg="#181825", fg="#6c7086", pady=4)
        self.peer_status_label.pack()

        # -- Main area ------------------------
        main = tk.Frame(self.root, bg="#1e1e2e")
        main.pack(side="right", fill="both", expand=True)

        # Header
        header = tk.Frame(main, bg="#181825", height=48)
        header.pack(fill="x")
        header.pack_propagate(False)

        self.chat_title = tk.Label(header, text="💬  Group Chat",
                                   font=(DEFAULT_FONT_FAMILY, 12, "bold"),
                                   bg="#181825", fg="#cdd6f4", padx=16)
        self.chat_title.pack(side="left", pady=10)

        settings_btn = tk.Button(header, text="👤 Profile", font=(DEFAULT_FONT_FAMILY, 9),
                                 bg="#313244", fg="#cdd6f4", relief="flat",
                                 activebackground="#45475a", padx=10, cursor="hand2",
                                 command=self._open_settings)
        settings_btn.pack(side="right", pady=10, padx=10)

        clear_btn = tk.Button(header, text="🗑️ Clear", font=(DEFAULT_FONT_FAMILY, 9),
                              bg="#313244", fg="#cdd6f4", relief="flat",
                              activebackground="#45475a", padx=10, cursor="hand2",
                              command=self._clear_chat_history)
        clear_btn.pack(side="right", pady=10, padx=(0, 6))

        dl_btn = tk.Button(header, text="📂 Folder", font=(DEFAULT_FONT_FAMILY, 9),
                           bg="#313244", fg="#cdd6f4", relief="flat",
                           activebackground="#45475a", padx=10, cursor="hand2",
                           command=self._open_download_settings)
        dl_btn.pack(side="right", pady=10)

        self.dm_clear_btn = tk.Button(header, text="← Back to Group",
                                      font=(DEFAULT_FONT_FAMILY, 9), bg="#313244", fg="#89b4fa",
                                      relief="flat", padx=10, cursor="hand2",
                                      command=self._clear_dm_selection)
        # only shown when DM is active

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            main, state="disabled", bg="#1e1e2e", fg="#cdd6f4",
            font=(DEFAULT_FONT_FAMILY, 11), relief="flat", bd=0, padx=12, pady=8,
            wrap="word", insertbackground="#cdd6f4"
        )
        self.chat_display.pack(fill="both", expand=True, padx=0, pady=0)

        # Tag styles
        self.chat_display.tag_config("timestamp", foreground="#45475a", font=(DEFAULT_FONT_FAMILY, 9))
        self.chat_display.tag_config("name_self",  foreground="#a6e3a1", font=(DEFAULT_FONT_FAMILY, 11, "bold"))
        self.chat_display.tag_config("name_other", foreground="#89b4fa", font=(DEFAULT_FONT_FAMILY, 11, "bold"))
        self.chat_display.tag_config("name_system",foreground="#f38ba8", font=(DEFAULT_FONT_FAMILY, 10, "italic"))
        self.chat_display.tag_config("msg_self",   foreground="#cdd6f4")
        self.chat_display.tag_config("msg_other",  foreground="#cdd6f4")
        self.chat_display.tag_config("msg_system", foreground="#f38ba8", font=(DEFAULT_FONT_FAMILY, 10, "italic"))
        self.chat_display.tag_config("file_recv",  foreground="#fab387", font=(DEFAULT_FONT_FAMILY, 10))

        # Input bar
        input_bar = tk.Frame(main, bg="#313244", pady=8, padx=8)
        input_bar.pack(fill="x", side="bottom")

        self.msg_entry = tk.Entry(input_bar, font=(DEFAULT_FONT_FAMILY, 12),
                                  bg="#45475a", fg="#cdd6f4", insertbackground="#cdd6f4",
                                  relief="flat", bd=6)
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.msg_entry.bind("<Return>", lambda e: self._send_message())

        send_btn = tk.Button(input_bar, text="Send", font=(DEFAULT_FONT_FAMILY, 10, "bold"),
                             bg="#89b4fa", fg="#1e1e2e", relief="flat",
                             activebackground="#74c7ec", padx=14, cursor="hand2",
                             command=self._send_message)
        send_btn.pack(side="left")

        file_btn = tk.Button(input_bar, text="📎 File", font=(DEFAULT_FONT_FAMILY, 9),
                              bg="#313244", fg="#cdd6f4", relief="flat",
                              activebackground="#45475a", padx=10, cursor="hand2",
                              command=self._send_file_dialog)
        file_btn.pack(side="left", padx=(6, 0))
        self.file_btn = file_btn
        self._update_file_button_state()

        # Progress bar (hidden by default)
        self.progress_frame = tk.Frame(main, bg="#181825", height=4)
        self.progress_frame.pack(fill="x", side="bottom")
        
        self.progress_val = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_val,
                                            maximum=100, mode="determinate")
        # Style the progress bar
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TProgressbar", thickness=4, bordercolor="#181825", 
                        background="#89b4fa", troughcolor="#181825")
        self.progress_bar.pack(fill="x")
        self.progress_frame.pack_forget() # hide initially

        self._log_system("Welcome to LAN Office! Discovering peers on your network…")

    # ==========================================
    #  CHAT HELPERS
    # ==========================================
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
        self._save_message(sender_name, text, is_self=is_self)

    def _log_system(self, text):
        self.chat_display.config(state="normal")
        ts = time.strftime("%H:%M")
        self.chat_display.insert("end", f"[{ts}] ● {text}\n", "msg_system")
        self.chat_display.config(state="disabled")
        self.chat_display.see("end")
        self._save_message("SYSTEM", text, is_system=True)

    def _log_file(self, text, filename=None):
        self.chat_display.config(state="normal")
        self.chat_display.insert("end", f"  📁 {text}\n", "file_recv")
        self.chat_display.config(state="disabled")
        self.chat_display.see("end")
        self._save_message("FILE", text, filename=filename)

    def _open_settings(self):
        new_name = tk.simpledialog.askstring("Profile", "Change your display name:",
                                             initialvalue=self.username)
        if new_name and new_name.strip() and new_name.strip() != self.username:
            self.username = new_name.strip()
            self._save_config()
            self._log_system(f"You changed your name to {self.username}")
            # The next presence broadcast will update others

    def _open_download_settings(self):
        path = filedialog.askdirectory(title="Select Default Downloads Folder",
                                       initialdir=self.download_dir or os.path.expanduser("~"))
        if path:
            self.download_dir = path
            self._save_config()
            self._log_system(f"Downloads will now be saved to: {path}")

    # ==========================================
    #  PEER SELECTION (DM vs GROUP)
    # ==========================================
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
                     self._update_file_button_state()
                     self.chat_title.config(text=f"💬  DM → {info['name']}")
                     self.dm_clear_btn.pack(side="right", pady=6, padx=10)
                     return

    def _clear_dm_selection(self):
        self.selected_peer_ip = None
        self._update_file_button_state()
        self.peers_listbox.selection_clear(0, "end")
        self.chat_title.config(text="💬  Group Chat")
        self.dm_clear_btn.pack_forget()

    def _clear_chat_history(self):
        if messagebox.askyesno("Clear Chat", "Delete all chat history?"):
            self.chat_history.clear()
            if os.path.exists(CHAT_HISTORY_FILE):
                try:
                    os.remove(CHAT_HISTORY_FILE)
                except Exception as e:
                    self.logger.error(f"Failed to delete history file: {e}")
            self.chat_display.config(state="normal")
            self.chat_display.delete(1.0, "end")
            self.chat_display.config(state="disabled")
            self._log_system("Chat history cleared.")

    # -----------------------------------------
    #  SENDING
    # -----------------------------------------
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
        except Exception as e:
            self.logger.debug(f"TCP connection error to {ip}:{port}: {e}")

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
            self.logger.info(f"Sending file to {ip}: {filename}")

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
            self.root.after(0, self._show_progress, True)
            sent = 0
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    s.sendall(chunk)
                    sent += len(chunk)
                    pct = (sent / filesize) * 100
                    self.root.after(0, self.progress_val.set, pct)
            s.close()
            self.root.after(0, self._show_progress, False)

            self.root.after(0, self._log_file,
                            f"Sent '{filename}' ({self._fmt_size(filesize)}) to "
                            f"{self.peers.get(ip, {}).get('name', ip)}", filename=filename)
        except Exception as e:
            self.logger.exception(f"File send failed to {ip}: {filename}")
            self.root.after(0, self._log_system, f"File send failed: {e}")

    @staticmethod
    def _fmt_size(n):
        for unit in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} TB"

    def _show_progress(self, show=True):
        if show:
            self.progress_frame.pack(fill="x", side="bottom")
            self.progress_val.set(0)
        else:
            self.progress_frame.pack_forget()

    # ==========================================
    #  NETWORKING – START
    # ==========================================
    def _start_networking(self):
        self.logger.info("Starting networking threads...")
        self.running = True
        threading.Thread(target=self._broadcast_presence, daemon=True).start()
        threading.Thread(target=self._listen_presence,    daemon=True).start()
        threading.Thread(target=self._listen_chat,        daemon=True).start()
        threading.Thread(target=self._listen_file,        daemon=True).start()
        threading.Thread(target=self._prune_peers,        daemon=True).start()

    # -- Presence (UDP broadcast) -------------
    def _broadcast_presence(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        payload = json.dumps({"type": "presence", "name": self.username,
                              "ip": self.local_ip}).encode()
        while self.running:
            try:
                self.logger.debug("Broadcasting presence")
                sock.sendto(payload, (self.broadcast_addr, BROADCAST_PORT))
            except Exception as e:
                self.logger.error(f"Presence broadcast error: {e}", exc_info=True)
            time.sleep(BROADCAST_INTERVAL)
        # Send leave message before closing
        try:
            leave_payload = json.dumps({"type": "leave", "name": self.username,
                                        "ip": self.local_ip}).encode()
            sock.sendto(leave_payload, (self.broadcast_addr, BROADCAST_PORT))
        except Exception:
            self.logger.debug("Failed to send leave message")
        sock.close()

    def _listen_presence(self):
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
        self.root.after(0, self._on_peer_leave, ip, name)

    def _on_peer_join(self, ip, name):
        self.logger.info(f"Peer joined: {name} ({ip})")
        self._log_system(f"{name} joined the network.")
        self._refresh_peers_list()

    def _prune_peers(self):
        """Remove peers not seen for 15 seconds."""
        while self.running:
            time.sleep(5)
            now = time.time()
            stale = []
            with self.peers_lock:
                for ip, info in self.peers.copy().items():
                    if now - info["last_seen"] > 15:
                        stale.append((ip, info["name"]))
                        del self.peers[ip]
            for ip, name in stale:
                self.root.after(0, self._on_peer_leave, ip, name)

    def _on_peer_leave(self, ip, name):
        self.logger.info(f"Peer left: {name} ({ip})")
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

    # -- Chat (TCP listener) ------------------
    def _listen_chat(self):
        self.logger.info("Chat listener started")
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
            except Exception as e:
                self.logger.error(f"Chat listen error: {e}")
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
                self.logger.debug(f"Chat from {addr}: {msg['text']}")
                self.root.after(0, self._log_message,
                                msg["name"], msg["text"], False)
        except Exception:
            self.logger.exception("Chat handling error")
        finally:
            conn.close()

    # -- File transfer (TCP listener) ---------
    def _listen_file(self):
        self.logger.info("File transfer listener started")
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
            except Exception as e:
                self.logger.error(f"File listen error: {e}")
        srv.close()

    def _handle_file(self, conn, addr):
        try:
            meta = self._receive_file_meta(conn)
            if not meta:
                return

            filename = meta["filename"]
            filesize = meta["filesize"]
            sender = meta.get("sender", addr[0])
            self.logger.info(f"File transfer from {addr}: {filename}")

            save_path = self._get_save_path(filename, filesize, sender)
            if not save_path:
                conn.close()
                return

            self._receive_file_data(conn, save_path, filesize)
            self.root.after(0, self._log_file,
                            f"Received '{filename}' from {sender} → saved to {save_path}", filename=filename)
        except Exception:
            self.logger.exception("File receive error")
        finally:
            conn.close()

    def _receive_file_meta(self, conn):
        raw_len = conn.recv(4)
        if len(raw_len) < 4:
            return None
        meta_len = struct.unpack("!I", raw_len)[0]
        meta_data = b""
        while len(meta_data) < meta_len:
            chunk = conn.recv(min(BUFFER_SIZE, meta_len - len(meta_data)))
            if not chunk:
                break
            meta_data += chunk
        return json.loads(meta_data.decode())

    def _get_save_path(self, filename, filesize, sender):
        save_path_holder = [None]
        done_event = threading.Event()

        def ask_save():
            answer = messagebox.askyesno(
                "Incoming File",
                f"{sender} wants to send you:\n{filename} "
                f"({self._fmt_size(filesize)})\n\nAccept?")
            if answer:
                if self.download_dir and os.path.exists(self.download_dir):
                    p = os.path.join(self.download_dir, filename)
                    if os.path.exists(p):
                        base, ext = os.path.splitext(filename)
                        p = os.path.join(self.download_dir, f"{base}_{int(time.time())}{ext}")
                else:
                    p = filedialog.asksaveasfilename(initialfile=filename, title="Save file as")
                save_path_holder[0] = p
            done_event.set()

        self.root.after(0, ask_save)
        done_event.wait(timeout=60)
        return save_path_holder[0]

    def _receive_file_data(self, conn, save_path, filesize):
        received = 0
        self.root.after(0, self._show_progress, True)
        with open(save_path, "wb") as f:
            while received < filesize:
                chunk = conn.recv(min(BUFFER_SIZE, filesize - received))
                if not chunk:
                    break
                f.write(chunk)
                received += len(chunk)
                pct = (received / filesize) * 100
                self.root.after(0, self.progress_val.set, pct)
        self.root.after(0, self._show_progress, False)

    # -----------------------------------------
    #  CLEANUP
    # -----------------------------------------
    def on_close(self):
        self.running = False
        self.root.destroy()


# ---------------------------------------------
#  ENTRY POINT
# ---------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = LANOfficeApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
