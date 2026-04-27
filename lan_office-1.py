import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, ttk
import socket
import threading
import json
import os
import time
import struct
import hashlib
import logging
import traceback

# ---------------------------------------------
#  CONFIGURATION
# ---------------------------------------------
DEFAULT_FONT_FAMILY = "Segoe UI"
BROADCAST_PORT  = 55000   # UDP â€“ user discovery / presence
CHAT_PORT       = 55001   # TCP â€“ chat messages
FILE_PORT       = 55002   # TCP â€“ file transfers
BROADCAST_INTERVAL = 5    # seconds between presence broadcasts
CHAT_HISTORY_FILE = "chat_history.jsonl"
MAX_HISTORY_LOAD = 100
BUFFER_SIZE     = 4096
CONFIG_FILE     = "lan_config.json"
APP_NAME        = "LAN Office"
ALL_FILES       = "All files"
SUCCESS_TITLE   = "Export Successful"
ERROR_TITLE     = "Export Error"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_broadcast_address(local_ip):
    parts = local_ip.split('.')
    parts[-1] = '255'
    return '.'.join(parts)

class LANOfficeApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("900x600")
        self.root.configure(bg="#1e1e2e")

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

        tk.Label(self.login_frame, text=APP_NAME, font=(DEFAULT_FONT_FAMILY, 28, "bold"),
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

        join_btn = tk.Button(self.login_frame, text="Join Network â†’",
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
                self._log_file(f"Received '{msg['filename']}' from {msg['sender']} â†’ saved to [previous location]", filename=msg["filename"])
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

        self.chat_title = tk.Label(header, text="ðŸ’¬  Group Chat",
                                   font=(DEFAULT_FONT_FAMILY, 12, "bold"),
                                   bg="#181825", fg="#cdd6f4", padx=16)
        self.chat_title.pack(side="left", pady=10)

        settings_btn = tk.Button(header, text="ðŸ‘¤ Profile", font=(DEFAULT_FONT_FAMILY, 9),
                                 bg="#313244", fg="#cdd6f4", relief="flat",
                                 activebackground="#45475a", padx=10, cursor="hand2",
                                 command=self._open_settings)
        settings_btn.pack(side="right", pady=10, padx=10)

        clear_btn = tk.Button(header, text="ðŸ—‘ï¸ Clear", font=(DEFAULT_FONT_FAMILY, 9),
                              bg="#313244", fg="#cdd6f4", relief="flat",
                              activebackground="#45475a", padx=10, cursor="hand2",
                              command=self._clear_chat_history)
        clear_btn.pack(side="right", pady=10, padx=(0, 6))

        export_btn = tk.Button(header, text="ðŸ“¤ Export", font=(DEFAULT_FONT_FAMILY, 9),
                          bg="#313244", fg="#cdd6f4", relief="flat",
                          activebackground="#45475a", padx=10, cursor="hand2",
                          command=self._export_chat_history)
        export_btn.pack(side="right", pady=10, padx=(0, 6))

        dl_btn = tk.Button(header, text="ðŸ“‚ Folder", font=(DEFAULT_FONT_FAMILY, 9),
                            bg="#313244", fg="#cdd6f4", relief="flat",
                            activebackground="#45475a", padx=10, cursor="hand2",
                            command=self._open_download_settings)
        dl_btn.pack(side="right", pady=10)

        self.dm_clear_btn = tk.Button(header, text="â† Back to Group",
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

        file_btn = tk.Button(input_bar, text="ðŸ“Ž File", font=(DEFAULT_FONT_FAMILY, 9),
                              bg="#313244", fg="#cdd6f4", relief="flat",
                              activebackground="#45475a", padx=10, cursor="hand2",
                              command=self._send_file_dialog)
        file_btn.pack(side="left", padx=(6, 0))
        self.file_btn = file_btn
        self._update_file_button_state()

        # Progress bar (hidden by default)
        self.progress_frame = tk.Frame(main, bg="#181825", height=4)
        self.progress_frame.pack(fill="x", side="bottom")
        
        # Cancel button
        self.cancel_btn = tk.Button(self.progress_frame, text="âœ• Cancel", font=("Segoe UI", 9),
                                    bg="#f38ba8", fg="#1e1e2e", relief="flat", padx=8, cursor="hand2",
                                    command=self._cancel_file_transfer)
        
        self.progress_val = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_val,
                                            maximum=100, mode="determinate")
        # Style the progress bar
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TProgressbar", thickness=4, bordercolor="#181825", 
                        background="#89b4fa", troughcolor="#181825")
        self.cancel_btn.pack(side="right", padx=8)
        self.progress_bar.pack(fill="x", side="left", expand=True)
        self.progress_frame.pack_forget() # hide initially

        self._log_system("Welcome to LAN Office! Discovering peers on your networkâ€¦")

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
        self.chat_display.insert("end", f"[{ts}] â— {text}\n", "msg_system")
        self.chat_display.config(state="disabled")
        self.chat_display.see("end")
        self._save_message("SYSTEM", text, is_system=True)

    def _log_file(self, text, filename=None):
        self.chat_display.config(state="normal")
        self.chat_display.insert("end", f"  ðŸ“ {text}\n", "file_recv")
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
                 display = f"ðŸŸ¢ {info['name']}"
                 if display == label:
                     self.selected_peer_ip = ip
                     self._update_file_button_state()
                     self.chat_title.config(text=f"ðŸ’¬  DM â†’ {info['name']}")
                     self.dm_clear_btn.pack(side="right", pady=6, padx=10)
                     return

    def _clear_dm_selection(self):
        self.selected_peer_ip = None
        self._update_file_button_state()
        self.peers_listbox.selection_clear(0, "end")
        self.chat_title.config(text="ðŸ’¬  Group Chat")
        self.dm_clear_btn.pack_forget()

    def _update_file_button_state(self):
        """Enable the file button only when a recipient is selected."""
        if hasattr(self, 'file_btn'):
            state = "normal" if self.selected_peer_ip else "disabled"
            self.file_btn.config(state=state)

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

    def _export_chat_history(self):
        if not self.chat_history:
            messagebox.showinfo("No History", "There is no chat history to export.")
            return
            
        export_window = tk.Toplevel(self.root)
        export_window.title("Export Chat History")
        export_window.geometry("400x300")
        export_window.configure(bg="#1e1e2e")
        export_window.transient(self.root)
        export_window.grab_set()
        
        # Center the window
        export_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (export_window.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (export_window.winfo_height() // 2)
        export_window.geometry(f"+{x}+{y}")
        
        # Title
        tk.Label(export_window, text="Export Chat History", 
                font=(DEFAULT_FONT_FAMILY, 14, "bold"),
                bg="#1e1e2e", fg="#cdd6f4").pack(pady=(20, 10))
        
        tk.Label(export_window, text="Choose export format:", 
                font=(DEFAULT_FONT_FAMILY, 11),
                bg="#1e1e2e", fg="#cdd6f4").pack(pady=(0, 20))
        
        # Button frame
        btn_frame = tk.Frame(export_window, bg="#1e1e2e")
        btn_frame.pack(pady=20)
        
        # Export buttons
        tk.Button(btn_frame, text="Export as Text (.txt)", 
                 font=(DEFAULT_FONT_FAMILY, 10),
                 bg="#313244", fg="#cdd6f4", relief="flat",
                 activebackground="#45475a", padx=10, pady=5,
                 command=lambda: [export_window.destroy(), self._export_as_text()]).pack(pady=5, fill="x", padx=20)
                 
        tk.Button(btn_frame, text="Export as JSON (.json)", 
                 font=(DEFAULT_FONT_FAMILY, 10),
                 bg="#313244", fg="#cdd6f4", relief="flat",
                 activebackground="#45475a", padx=10, pady=5,
                 command=lambda: [export_window.destroy(), self._export_as_json()]).pack(pady=5, fill="x", padx=20)
                 
        tk.Button(btn_frame, text="Export as CSV (.csv)", 
                 font=(DEFAULT_FONT_FAMILY, 10),
                 bg="#313244", fg="#cdd6f4", relief="flat",
                 activebackground="#45475a", padx=10, pady=5,
                 command=lambda: [export_window.destroy(), self._export_as_csv()]).pack(pady=5, fill="x", padx=20)
                 
        tk.Button(btn_frame, text="Cancel", 
                 font=(DEFAULT_FONT_FAMILY, 10),
                 bg="#313244", fg="#cdd6f4", relief="flat",
                 activebackground="#45475a", padx=10, pady=5,
                 command=export_window.destroy).pack(pady=(20, 5), fill="x", padx=20)

    def _export_as_text(self):
        if not self.chat_history:
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), (ALL_FILES, "*.*")],
            title="Export chat history as text"
        )
        if not filename:
            return
            
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("LAN Office Chat History Export\n")
                f.write("=" * 40 + "\n\n")
                for msg in self.chat_history:
                    timestamp = msg.get("time_str", "Unknown")
                    sender = msg.get("sender", "Unknown")
                    text = msg.get("text", "")
                    is_system = msg.get("is_system", False)
                    filename_attr = msg.get("filename")
                    
                    if is_system:
                        f.write(f"[{timestamp}] â— {text}\n")
                    elif filename_attr:
                        f.write(f"[{timestamp}] ðŸ“ {text}\n")
                    else:
                        f.write(f"[{timestamp}] {sender}: {text}\n")
                        
            messagebox.showinfo(SUCCESS_TITLE, f"Chat history exported to:\n{filename}")
            self._log_system(f"Exported chat history to {os.path.basename(filename)}")
        except Exception as e:
            messagebox.showerror(ERROR_TITLE, f"Failed to export chat history:\n{str(e)}")

    def _export_as_json(self):
        if not self.chat_history:
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), (ALL_FILES, "*.*")],
            title="Export chat history as JSON"
        )
        if not filename:
            return
            
        try:
            export_data = {
                "export_info": {
                    "app": APP_NAME,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_messages": len(self.chat_history)
                },
                "messages": self.chat_history
            }
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            messagebox.showinfo(SUCCESS_TITLE, f"Chat history exported to:\n{filename}")
            self._log_system(f"Exported chat history to {os.path.basename(filename)}")
        except Exception as e:
            messagebox.showerror(ERROR_TITLE, f"Failed to export chat history:\n{str(e)}")

    def _export_as_csv(self):
        if not self.chat_history:
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), (ALL_FILES, "*.*")],
            title="Export chat history as CSV"
        )
        if not filename:
            return
            
        try:
            import csv
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Sender", "Message", "Is System", "Filename"])
                for msg in self.chat_history:
                    writer.writerow([
                        msg.get("time_str", ""),
                        msg.get("sender", ""),
                        msg.get("text", ""),
                        "Yes" if msg.get("is_system", False) else "No",
                        msg.get("filename", "")
                    ])
            messagebox.showinfo(SUCCESS_TITLE, f"Chat history exported to:\n{filename}")
            self._log_system(f"Exported chat history to {os.path.basename(filename)}")
        except Exception as e:
            messagebox.showerror(ERROR_TITLE, f"Failed to export chat history:\n{str(e)}")

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
            threading.Thread(target=self._tcp_send,
                             args=(self.selected_peer_ip, CHAT_PORT, payload),
                             daemon=True).start()
        else:
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
            s.sendall(struct.pack("!I", len(data)) + data)
            s.close()
        except Exception:
            pass

    def _send_file_dialog(self):
        target_ip = self.selected_peer_ip
        if not self.selected_peer_ip:
            messagebox.showinfo("Select a recipient", "Click a user in the sidebar first.")
            return

        path = filedialog.askopenfilename(title="Select a file to send")
        if not path:
            return

        self.cancel_transfer = False
        threading.Thread(target=self._send_file, args=(target_ip, path), daemon=True).start()

    def _send_file(self, ip, path):
        try:
            self.cancel_transfer = False
            filename = os.path.basename(path)
            filesize = os.path.getsize(path)
            checksum = self._compute_checksum(path)

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(30)
            s.connect((ip, FILE_PORT))

            meta = json.dumps({
                "filename": filename,
                "filesize": filesize,
                "sender": self.username,
                "checksum": checksum
            }).encode()
            s.sendall(struct.pack("!I", len(meta)) + meta)

            self.root.after(0, self._show_progress, True)
            sent = 0
            with open(path, "rb") as f:
                while True:
                    if self.cancel_transfer: break
                    chunk = f.read(BUFFER_SIZE)
                    if not chunk: break
                    s.sendall(chunk)
                    sent += len(chunk)
                    pct = (sent / filesize) * 100
                    self.root.after(0, self.progress_val.set, pct)
            s.close()
            self.root.after(0, self._show_progress, False)
            self.root.after(0, self._log_file, f"Sent '{filename}' to {self.peers.get(ip, {}).get('name', ip)}")
        except Exception as e:
            self.root.after(0, self._log_system, f"File send failed: {e}")

    @staticmethod
    def _fmt_size(n):
         for unit in ("B", "KB", "MB", "GB"):
             if n < 1024: return f"{n:.1f} {unit}"
             n /= 1024
         return f"{n:.1f} TB"

    @staticmethod
    def _compute_checksum(filepath):
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk: break
                sha256.update(chunk)
        return sha256.hexdigest()

    def _show_progress(self, show=True):
        if show:
            self.progress_frame.pack(fill="x", side="bottom")
            self.progress_val.set(0)
            self.cancel_btn.pack(side="right", padx=8)
            self.progress_bar.pack(fill="x", side="left", expand=True)
        else:
            self.cancel_btn.pack_forget()
            self.progress_frame.pack_forget()

    def _cancel_file_transfer(self):
        self.cancel_transfer = True
        self._show_progress(False)
        self._log_system("File transfer cancelled.")

    # ==========================================
    #  NETWORKING â€“ START
    # ==========================================
    def _start_networking(self):
        self.running = True
        threading.Thread(target=self._broadcast_presence, daemon=True).start()
        threading.Thread(target=self._listen_presence,    daemon=True).start()
        threading.Thread(target=self._listen_chat,        daemon=True).start()
        threading.Thread(target=self._listen_file,        daemon=True).start()
        threading.Thread(target=self._prune_peers,        daemon=True).start()

    def _broadcast_presence(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        payload = json.dumps({"type": "presence", "name": self.username, "ip": self.local_ip}).encode()
        while self.running:
            try:
                sock.sendto(payload, (self.broadcast_addr, BROADCAST_PORT))
            except Exception: pass
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
                    self._update_peer_presence(addr[0], msg.get("name", addr[0]))
                elif msg.get("type") == "leave":
                    self._remove_peer(addr[0], msg.get("name", addr[0]))
            except socket.timeout: pass
            except Exception: pass
        sock.close()

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
            if ip in self.peers: del self.peers[ip]
        self.root.after(0, self._on_peer_leave, ip, name)

    def _on_peer_join(self, ip, name):
        self._log_system(f"{name} joined the network.")
        self._refresh_peers_list()

    def _prune_peers(self):
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
        self._log_system(f"{name} left the network.")
        self._refresh_peers_list()

    def _refresh_peers_list(self):
        self.peers_listbox.delete(0, "end")
        with self.peers_lock:
            for ip, info in self.peers.items():
                self.peers_listbox.insert("end", f"ðŸŸ¢ {info['name']}")
        count = self.peers_listbox.size()
        self.peer_status_label.config(text=f"{count} user{'s' if count != 1 else ''} online")

    def _listen_chat(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("", CHAT_PORT))
        srv.listen(10)
        srv.settimeout(1)
        while self.running:
            try:
                conn, addr = srv.accept()
                threading.Thread(target=self._handle_chat, args=(conn, addr), daemon=True).start()
            except socket.timeout: pass
            except Exception: pass
        srv.close()

    def _handle_chat(self, conn, addr):
        try:
            raw_len = conn.recv(4)
            if len(raw_len) < 4: return
            msg_len = struct.unpack("!I", raw_len)[0]
            data = b""
            while len(data) < msg_len:
                chunk = conn.recv(min(BUFFER_SIZE, msg_len - len(data)))
                if not chunk: break
                data += chunk
            msg = json.loads(data.decode())
            if msg.get("type") == "chat":
                self.root.after(0, self._log_message, msg["name"], msg["text"], False)
        except Exception: pass
        finally: conn.close()

    def _listen_file(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("", FILE_PORT))
        srv.listen(5)
        srv.settimeout(1)
        while self.running:
            try:
                conn, addr = srv.accept()
                threading.Thread(target=self._handle_file, args=(conn, addr), daemon=True).start()
            except socket.timeout: pass
            except Exception: pass
        srv.close()

    def _handle_file(self, conn, addr):
        try:
            self.cancel_transfer = False
            raw_len = conn.recv(4)
            if len(raw_len) < 4: return
            meta_len = struct.unpack("!I", raw_len)[0]
            meta_data = b""
            while len(meta_data) < meta_len:
                chunk = conn.recv(min(BUFFER_SIZE, meta_len - len(meta_data)))
                if not chunk: break
                meta_data += chunk
            meta = json.loads(meta_data.decode())
            filename = meta["filename"]
            filesize = meta["filesize"]
            sender = meta.get("sender", addr[0])
            checksum = meta.get("checksum")

            save_path = self._get_save_path(filename, filesize, sender)
            if not save_path:
                conn.close()
                return

            received = 0
            self.root.after(0, self._show_progress, True)
            with open(save_path, "wb") as f:
                while received < filesize:
                    if self.cancel_transfer: break
                    chunk = conn.recv(min(BUFFER_SIZE, filesize - received))
                    if not chunk: break
                    f.write(chunk)
                    received += len(chunk)
                    pct = (received / filesize) * 100
                    self.root.after(0, self.progress_val.set, pct)
            self.root.after(0, self._show_progress, False)
            if checksum and self._compute_checksum(save_path) == checksum:
                self.root.after(0, self._log_system, f"âœ“ Verified: {filename}")
            self.root.after(0, self._log_file, f"Received '{filename}' from {sender} â†’ saved to {save_path}")
        except Exception: pass
        finally: conn.close()

    def _get_save_path(self, filename, filesize, sender):
        save_path_holder = [None]
        done_event = threading.Event()
        def ask_save():
            answer = messagebox.askyesno("Incoming File", f"{sender} wants to send you:\n{filename} ({self._fmt_size(filesize)})\nAccept?")
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

    def on_close(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = LANOfficeApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

