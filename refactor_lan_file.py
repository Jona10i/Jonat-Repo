import os

path = r"c:\Users\HomePC\Downloads\Documents\lan_office-1.py"

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Refactor _handle_file
old_handle_file = """    def _handle_file(self, conn, addr):
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
            self.logger.info(f"File transfer from {addr}: {filename}")

            # Ask user where to save (on main thread)
            save_path_holder = [None]
            done_event = threading.Event()

            def ask_save():
                answer = messagebox.askyesno(
                    "Incoming File",
                    f"{sender} wants to send you:\\n{filename} "
                    f"({self._fmt_size(filesize)})\\n\\nAccept?")
                if answer:
                    if self.download_dir and os.path.exists(self.download_dir):
                        p = os.path.join(self.download_dir, filename)
                        # Check for collision
                        if os.path.exists(p):
                            base, ext = os.path.splitext(filename)
                            p = os.path.join(self.download_dir, f"{base}_{int(time.time())}{ext}")
                    else:
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

            self.root.after(0, self._log_file,
                            f"Received '{filename}' from {sender} → saved to {save_path}", filename=filename)
        except Exception:
            self.logger.exception("File receive error")
        finally:
            conn.close()"""

new_handle_file = """    def _handle_file(self, conn, addr):
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
                f"{sender} wants to send you:\\n{filename} "
                f"({self._fmt_size(filesize)})\\n\\nAccept?")
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
        self.root.after(0, self._show_progress, False)"""

if old_handle_file in content:
    content = content.replace(old_handle_file, new_handle_file)
    print("Refactored _handle_file")
else:
    print("Failed to find _handle_file")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
