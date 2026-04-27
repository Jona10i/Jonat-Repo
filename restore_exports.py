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
                        f.write(f"[{timestamp}] ● {text}\n")
                    elif filename_attr:
                        f.write(f"[{timestamp}] 📁 {text}\n")
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
