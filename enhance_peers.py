#!/usr/bin/env python3
"""Enhance the peers section with visual avatars and better UI"""

# Read the file
with open('meeting_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Old peers section
old_peers = '''    def _build_ios26_peers_section(self):
        """Build iOS 26 style peers section"""
        peers_frame = tk.Frame(self.content_frame, bg=IOS26_COLORS["bg_primary"])
        peers_frame.pack(fill="x", pady=(16, 0))
        
        # Section title
        peers_title = tk.Label(peers_frame, text="Online Users",
                              font=(DEFAULT_FONT_FAMILY, 13, "bold"),
                              bg=IOS26_COLORS["bg_primary"], fg=IOS26_COLORS["text_secondary"])
        peers_title.pack(anchor="w", pady=(0, 8))
        
        # Peers list
        self.peers_listbox = tk.Listbox(peers_frame,
                                       bg=IOS26_COLORS["bg_secondary"],
                                       fg=IOS26_COLORS["text_primary"],
                                       selectbackground=IOS26_COLORS["system_blue"],
                                       selectforeground=IOS26_COLORS["text_primary"],
                                       relief="flat", borderwidth=0,
                                       font=(DEFAULT_FONT_FAMILY, 12),
                                       activestyle="none", highlightthickness=0,
                                       height=4)
        self.peers_listbox.pack(fill="x")
        self.peers_listbox.bind("<<ListboxSelect>>", self._on_peer_select)'''

# New enhanced peers section
new_peers = '''    def _build_ios26_peers_section(self):
        """Build iOS 26 style peers section with enhanced visual presentation"""
        # Main container
        peers_container = tk.Frame(self.content_frame, bg=IOS26_COLORS["bg_primary"])
        peers_container.pack(fill="x", pady=(16, 0))
        
        # Header with online indicator
        header_frame = tk.Frame(peers_container, bg=IOS26_COLORS["bg_primary"])
        header_frame.pack(fill="x", pady=(0, 12))
        
        # Online status dot
        online_dot = tk.Canvas(header_frame, width=10, height=10, 
                              bg=IOS26_COLORS["bg_primary"], highlightthickness=0)
        online_dot.pack(side="left", padx=(0, 8))
        online_dot.create_oval(2, 2, 8, 8, fill=IOS26_COLORS["system_green"], outline="")
        
        peers_title = tk.Label(header_frame, text="Online Users",
                              font=(DEFAULT_FONT_FAMILY, 14, "bold"),
                              bg=IOS26_COLORS["bg_primary"], fg=IOS26_COLORS["text_primary"])
        peers_title.pack(side="left")
        
        # User count badge
        self.peers_count_label = tk.Label(header_frame, text="0",
                                         font=(DEFAULT_FONT_FAMILY, 11, "bold"),
                                         bg=IOS26_COLORS["bg_tertiary"],
                                         fg=IOS26_COLORS["text_secondary"],
                                         padx=8, pady=2)
        self.peers_count_label.pack(side="right")
        
        # Scrollable frame for peers
        canvas = tk.Canvas(peers_container, bg=IOS26_COLORS["bg_primary"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(peers_container, orient="vertical", command=canvas.yview)
        self.peers_frame = tk.Frame(canvas, bg=IOS26_COLORS["bg_primary"])
        
        self.peers_frame.bind("<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.peers_frame, anchor="nw", width=360)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Store peer widgets
        self.peer_widgets = {}
        
        # Show empty state
        self._show_empty_peers_state()
    
    def _show_empty_peers_state(self):
        """Show empty state when no peers online"""
        for widget in self.peers_frame.winfo_children():
            widget.destroy()
        
        empty_label = tk.Label(self.peers_frame, 
                              text="No users online\\nJoin the network to see others",
                              font=(DEFAULT_FONT_FAMILY, 12),
                              bg=IOS26_COLORS["bg_primary"], 
                              fg=IOS26_COLORS["text_tertiary"],
                              justify="center")
        empty_label.pack(pady=20)
    
    def _get_avatar_color(self, name):
        """Generate consistent avatar color from name"""
        colors = [
            IOS26_COLORS["system_blue"],
            IOS26_COLORS["system_green"],
            IOS26_COLORS["system_purple"],
            IOS26_COLORS["system_pink"],
            IOS26_COLORS["system_orange"],
            IOS26_COLORS["system_teal"],
            IOS26_COLORS["system_indigo"],
            IOS26_COLORS["system_red"],
        ]
        hash_val = sum(ord(c) for c in name) if name else 0
        return colors[hash_val % len(colors)]
    
    def _get_initials(self, name):
        """Get initials from name"""
        if not name:
            return "?"
        parts = name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return name[:2].upper() if len(name) >= 2 else name.upper()
    
    def _create_peer_widget(self, ip, name):
        """Create a visual peer widget with avatar"""
        # Container frame
        peer_frame = tk.Frame(self.peers_frame, bg=IOS26_COLORS["bg_secondary"],
                             padx=12, pady=8)
        peer_frame.pack(fill="x", pady=(0, 4))
        peer_frame.bind("<Button-1>", lambda e, ip=ip: self._select_peer(ip))
        
        # Avatar circle with initials
        avatar_size = 40
        avatar_canvas = tk.Canvas(peer_frame, width=avatar_size, height=avatar_size,
                                 bg=IOS26_COLORS["bg_secondary"], highlightthickness=0,
                                 cursor="hand2")
        avatar_canvas.pack(side="left", padx=(0, 12))
        
        # Draw avatar circle
        avatar_color = self._get_avatar_color(name)
        avatar_canvas.create_oval(2, 2, avatar_size-2, avatar_size-2, 
                                  fill=avatar_color, outline="")
        
        # Add initials
        initials = self._get_initials(name)
        avatar_canvas.create_text(avatar_size//2, avatar_size//2, text=initials,
                                  font=(DEFAULT_FONT_FAMILY, 14, "bold"),
                                  fill=IOS26_COLORS["text_primary"])
        
        # Click handler for avatar
        avatar_canvas.bind("<Button-1>", lambda e, ip=ip: self._select_peer(ip))
        
        # Info container
        info_frame = tk.Frame(peer_frame, bg=IOS26_COLORS["bg_secondary"])
        info_frame.pack(side="left", fill="both", expand=True)
        info_frame.bind("<Button-1>", lambda e, ip=ip: self._select_peer(ip))
        
        # Name label
        name_label = tk.Label(info_frame, text=name,
                             font=(DEFAULT_FONT_FAMILY, 14, "bold"),
                             bg=IOS26_COLORS["bg_secondary"], 
                             fg=IOS26_COLORS["text_primary"],
                             anchor="w", cursor="hand2")
        name_label.pack(fill="x")
        name_label.bind("<Button-1>", lambda e, ip=ip: self._select_peer(ip))
        
        # IP label with online indicator
        ip_frame = tk.Frame(info_frame, bg=IOS26_COLORS["bg_secondary"])
        ip_frame.pack(fill="x")
        
        # Small online dot
        online_canvas = tk.Canvas(ip_frame, width=8, height=8,
                                 bg=IOS26_COLORS["bg_secondary"], highlightthickness=0)
        online_canvas.pack(side="left", padx=(0, 6))
        online_canvas.create_oval(1, 1, 7, 7, fill=IOS26_COLORS["system_green"], outline="")
        
        ip_label = tk.Label(ip_frame, text=ip,
                           font=(DEFAULT_FONT_FAMILY, 11),
                           bg=IOS26_COLORS["bg_secondary"], 
                           fg=IOS26_COLORS["text_secondary"])
        ip_label.pack(side="left")
        
        # Hover effects
        def on_enter(e, f=peer_frame, n=name_label, a=avatar_canvas, i=ip_frame):
            f.configure(bg=IOS26_COLORS["bg_tertiary"])
            n.configure(bg=IOS26_COLORS["bg_tertiary"])
            a.configure(bg=IOS26_COLORS["bg_tertiary"])
            i.configure(bg=IOS26_COLORS["bg_tertiary"])
            for child in i.winfo_children():
                if hasattr(child, 'configure'):
                    try:
                        child.configure(bg=IOS26_COLORS["bg_tertiary"])
                    except:
                        pass
        
        def on_leave(e, f=peer_frame, n=name_label, a=avatar_canvas, i=ip_frame):
            f.configure(bg=IOS26_COLORS["bg_secondary"])
            n.configure(bg=IOS26_COLORS["bg_secondary"])
            a.configure(bg=IOS26_COLORS["bg_secondary"])
            i.configure(bg=IOS26_COLORS["bg_secondary"])
            for child in i.winfo_children():
                if hasattr(child, 'configure'):
                    try:
                        child.configure(bg=IOS26_COLORS["bg_secondary"])
                    except:
                        pass
        
        for widget in [peer_frame, name_label, avatar_canvas, info_frame]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
        
        return peer_frame
    
    def _select_peer(self, ip):
        """Select a peer by IP"""
        self.selected_peer_ip = ip
        self.status_label.config(text=f"Selected: {self.peers.get(ip, {}).get('name', ip)}",
                                fg=IOS26_COLORS["system_blue"])'''

if old_peers in content:
    content = content.replace(old_peers, new_peers)
    print("Enhanced peers section added")
else:
    print("WARNING: Could not find old peers section")

# Now update _refresh_peers_display
old_refresh = '''    def _refresh_peers_display(self, peer_list):
        """Refresh peers display"""
        try:
            if hasattr(self, 'peers_listbox'):
                self.peers_listbox.delete(0, "end")
                for ip, info in peer_list:
                    display = f"{info.get('name', 'Unknown')} ({ip})"
                    self.peers_listbox.insert("end", display)
        except Exception as e:
            self.logger.debug(f"Refresh peers error: {e}")'''

new_refresh = '''    def _refresh_peers_display(self, peer_list):
        """Refresh peers display with visual widgets"""
        try:
            if hasattr(self, 'peers_frame'):
                # Clear existing widgets
                for widget in self.peers_frame.winfo_children():
                    widget.destroy()
                
                # Update count
                if hasattr(self, 'peers_count_label'):
                    self.peers_count_label.config(text=str(len(peer_list)))
                
                # Show empty state or peer widgets
                if not peer_list:
                    self._show_empty_peers_state()
                else:
                    for ip, info in peer_list:
                        name = info.get('name', 'Unknown')
                        self._create_peer_widget(ip, name)
                        
        except Exception as e:
            self.logger.debug(f"Refresh peers error: {e}")'''

if old_refresh in content:
    content = content.replace(old_refresh, new_refresh)
    print("Updated refresh peers display")
else:
    print("WARNING: Could not find old refresh method")

# Write the enhanced file
with open('meeting_assistant.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nPeers section enhanced!")
