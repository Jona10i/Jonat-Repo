import { useEffect, useMemo, useRef, useState, type ChangeEvent } from "react";
import { io, type Socket } from "socket.io-client";

type Department = { id: string; name: string };
type Message = {
  id: string;
  sender: string;
  text: string;
  kind: "message" | "broadcast" | "notification" | "reminder";
  createdAt: string;
  departmentId: string;
};
type Presence = {
  clientId: string;
  username: string;
  online: boolean;
  departmentId: string;
  lastSeenAt: string;
};
type DiscoveredServer = {
  id: string;
  name: string;
  host: string;
  port: number;
  url: string;
  lastSeenAt: string;
};
type ServerHealth = {
  status: "healthy" | "unreachable";
  latencyMs: number | null;
  onlineUsers: number | null;
  checkedAt: string;
};
type AutoSwitchNotice = {
  id: number;
  message: string;
};

function getOrCreateClientId() {
  const key = "officeLanCommClientId";
  const existing = window.localStorage.getItem(key);
  if (existing) {
    return existing;
  }
  const next = `client-${crypto.randomUUID()}`;
  window.localStorage.setItem(key, next);
  return next;
}

// Icon components
const Icons = {
  minimize: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
  maximize: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="2" y="2" width="12" height="12" stroke="currentColor" strokeWidth="2" fill="none" />
    </svg>
  ),
  close: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M3 3L13 13M13 3L3 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
  send: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 10L18 2L10 18L8 11L2 10Z" fill="currentColor" />
    </svg>
  ),
  attach: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M4 7V14C4 15.1 4.9 16 6 16H14C15.1 16 16 15.1 16 14V8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M7 5L13 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  user: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="10" cy="7" r="3.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="M3 17.5C3 14.5 6.13 12 10 12C13.87 12 17 14.5 17 17.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  users: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="7" cy="7" r="2.5" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="13" cy="7" r="2.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="M2 15.5C2 13.5 4.2 12 7 12C9.8 12 12 13.5 12 15.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M8 15.5C8 14 9.34 13 11 13C12.66 13 14 14 14 15.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  settings: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="10" cy="10" r="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M10 2V4M10 16V18M18 10H16M4 10H2M15.5 4.5L14.1 5.9M5.9 14.1L4.5 15.5M15.5 15.5L14.1 14.1M5.9 5.9L4.5 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  bell: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M15 7C15 5.67 14.5 4.5 13.71 3.71C12.89 2.89 11.76 2.5 10.5 2.5C9.24 2.5 8.11 2.89 7.29 3.71C6.5 4.5 6 5.67 6 7C6 13 3 15 3 15H17C17 15 14 13 15 7Z" stroke="currentColor" strokeWidth="1.5" />
      <path d="M12.73 17.5C12.5 18 11.85 18.5 10.73 18.5C9.6 18.5 8.95 18 8.73 17.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  check: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M17 6L8 15L3 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  broadcast: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="10" cy="5" r="2" fill="currentColor" />
      <path d="M3 15C5 12 7.5 11 10 11C12.5 11 15 12 17 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M2 18C4.5 14.5 7 13 10 13C13 13 15.5 14.5 18 18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  clock: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.5" />
      <path d="M10 6V10H13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  refresh: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M17 10C17 14 13.5 17 10 17C6.5 17 3 14 3 10C3 6.5 6 3 10 3C11.5 3 12.9 3.5 14 4.2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M16 2V5H13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
};

export function App() {
  const socketRef = useRef<Socket | null>(null);
  const [username, setUsername] = useState("NewUser");
  const [serverUrl, setServerUrl] = useState("http://localhost:4010");
  const [departments, setDepartments] = useState<Department[]>([]);
  const [selectedDepartment, setSelectedDepartment] = useState("general");
  const [messages, setMessages] = useState<Message[]>([]);
  const [presence, setPresence] = useState<Presence[]>([]);
  const [discoveredServers, setDiscoveredServers] = useState<DiscoveredServer[]>([]);
  const [serverHealthByUrl, setServerHealthByUrl] = useState<Record<string, ServerHealth>>({});
  const [connectionState, setConnectionState] = useState<"connecting" | "online" | "offline">("connecting");
  const [autoSwitchNotice, setAutoSwitchNotice] = useState<AutoSwitchNotice | null>(null);
  const [input, setInput] = useState("");
  const [storageDir, setStorageDir] = useState<string>("");
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [floatingBubble, setFloatingBubble] = useState(true);
  const [autoSelectBestServer, setAutoSelectBestServer] = useState(true);
  const [autoRefreshCriticalDiscovery, setAutoRefreshCriticalDiscovery] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [showOnlyOnlineUsers, setShowOnlyOnlineUsers] = useState(false);
  const typingTimerRef = useRef<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const selectedDepartmentRef = useRef(selectedDepartment);
  const clientIdRef = useRef(getOrCreateClientId());
  const lastAutoSwitchAtRef = useRef(0);
  const lastCriticalAutoRefreshAtRef = useRef(0);
  const [lastDiscoveryRefreshAt, setLastDiscoveryRefreshAt] = useState<number>(Date.now());
  const [refreshingDiscovery, setRefreshingDiscovery] = useState(false);
  const [refreshAgeSeconds, setRefreshAgeSeconds] = useState(0);
  const [lastCriticalAutoRefreshAt, setLastCriticalAutoRefreshAt] = useState<number | null>(null);
  const [isWindowMinimized, setIsWindowMinimized] = useState(false);

  useEffect(() => {
    selectedDepartmentRef.current = selectedDepartment;
  }, [selectedDepartment]);

  useEffect(() => {
    window.officeApi.onWindowState((state: string) => {
      setIsWindowMinimized(state === "minimized");
    });
  }, []);

  useEffect(() => {
    void window.officeApi.getServerUrl().then((url) => {
      if (url) {
        setServerUrl(url);
      }
    });
    void window.officeApi.getDiscoveredServers().then((servers) => setDiscoveredServers(servers));
    setLastDiscoveryRefreshAt(Date.now());
    window.officeApi.onServerUrl((url) => {
      if (url) {
        setServerUrl(url);
      }
    });
    window.officeApi.onServerList((servers) => {
      setDiscoveredServers(servers);
      setLastDiscoveryRefreshAt(Date.now());
    });

    void window.officeApi.getSettings().then((settings) => {
      const dir = settings.storageDirectory;
      if (typeof dir === "string") {
        setStorageDir(dir);
      }
      const autoSelect = settings.autoSelectBestServer;
      if (typeof autoSelect === "boolean") {
        setAutoSelectBestServer(autoSelect);
      }
      const autoRefreshCritical = settings.autoRefreshCriticalDiscovery;
      if (typeof autoRefreshCritical === "boolean") {
        setAutoRefreshCriticalDiscovery(autoRefreshCritical);
      }
    });

    window.officeApi.onStorageSelected((path) => setStorageDir(path));
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setRefreshAgeSeconds(Math.max(0, Math.floor((Date.now() - lastDiscoveryRefreshAt) / 1000)));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [lastDiscoveryRefreshAt]);

  useEffect(() => {
    void fetch(`${serverUrl}/departments`)
      .then((res) => res.json())
      .then((data: Department[]) => setDepartments(data))
      .catch(() => setDepartments([]));

    const socket = io(serverUrl, { autoConnect: true });
    socketRef.current = socket;
    setConnectionState("connecting");

    socket.on("connect", () => {
      setConnectionState("online");
      socket.emit("presence:join", {
        username,
        clientId: clientIdRef.current,
        departmentId: selectedDepartmentRef.current
      });
      socket.emit("department:join", {
        departmentId: selectedDepartmentRef.current,
        clientId: clientIdRef.current
      });
    });
    socket.on("disconnect", () => setConnectionState("offline"));

    socket.on("messages:seed", (seed: Message[]) => setMessages(seed));
    socket.on("chat:new", (message: Message) => {
      if (message.departmentId === selectedDepartmentRef.current || message.kind === "broadcast") {
        setMessages((prev) => [...prev, message]);
      }
      if (notificationsEnabled && message.sender !== username && "Notification" in window) {
        void Notification.requestPermission().then((perm) => {
          if (perm === "granted") {
            new Notification(`${message.sender} in ${message.departmentId}`, {
              body: message.text
            });
          }
        });
      }
    });

    socket.on("presence:list", (list: Presence[]) => setPresence(list));
    socket.on("notification:new", ({ title, body }: { title: string; body: string }) => {
      if (notificationsEnabled && "Notification" in window) {
        new Notification(title, { body });
      }
    });

    return () => {
      socket.off("connect");
      socket.off("disconnect");
      socket.off("messages:seed");
      socket.off("chat:new");
      socket.off("presence:list");
      socket.off("notification:new");
      socket.disconnect();
      socketRef.current = null;
    };
  }, [notificationsEnabled, serverUrl, username]);

  const displayedServers = useMemo(() => {
    if (discoveredServers.some((server) => server.url === serverUrl)) {
      return discoveredServers;
    }
    return [
      {
        id: `manual-${serverUrl}`,
        name: "Selected server",
        host: serverUrl.replace(/^https?:\/\//, ""),
        port: 0,
        url: serverUrl,
        lastSeenAt: new Date().toISOString()
      },
      ...discoveredServers
    ];
  }, [discoveredServers, serverUrl]);

  useEffect(() => {
    let isCancelled = false;

    const probeHealth = async (url: string) => {
      const startedAt = performance.now();
      try {
        const res = await fetch(`${url}/health`, { cache: "no-store" });
        if (!res.ok) {
          throw new Error(`Health status ${res.status}`);
        }
        const payload = (await res.json()) as { onlineUsers?: number };
        const latencyMs = Math.round(performance.now() - startedAt);
        if (isCancelled) {
          return;
        }
        setServerHealthByUrl((prev) => ({
          ...prev,
          [url]: {
            status: "healthy",
            latencyMs,
            onlineUsers: typeof payload.onlineUsers === "number" ? payload.onlineUsers : null,
            checkedAt: new Date().toISOString()
          }
        }));
      } catch {
        if (isCancelled) {
          return;
        }
        setServerHealthByUrl((prev) => ({
          ...prev,
          [url]: {
            status: "unreachable",
            latencyMs: null,
            onlineUsers: null,
            checkedAt: new Date().toISOString()
          }
        }));
      }
    };

    const runBatch = () => {
      displayedServers.forEach((server) => {
        void probeHealth(server.url);
      });
    };

    runBatch();
    const timer = window.setInterval(runBatch, 8000);
    return () => {
      isCancelled = true;
      window.clearInterval(timer);
    };
  }, [displayedServers]);

  useEffect(() => {
    if (!autoSelectBestServer) {
      return;
    }
    const now = Date.now();
    const cooldownMs = 15000;
    if (now - lastAutoSwitchAtRef.current < cooldownMs) {
      return;
    }

    const discoveredOnly = discoveredServers.filter((server) => !!server.url);
    if (!discoveredOnly.length) {
      return;
    }

    const healthyDiscovered = discoveredOnly
      .map((server) => ({
        server,
        health: serverHealthByUrl[server.url]
      }))
      .filter((entry) => entry.health?.status === "healthy");

    if (!healthyDiscovered.length) {
      return;
    }

    healthyDiscovered.sort((a, b) => {
      const latencyA = a.health?.latencyMs ?? Number.MAX_SAFE_INTEGER;
      const latencyB = b.health?.latencyMs ?? Number.MAX_SAFE_INTEGER;
      if (latencyA !== latencyB) {
        return latencyA - latencyB;
      }
      const usersA = a.health?.onlineUsers ?? 0;
      const usersB = b.health?.onlineUsers ?? 0;
      return usersB - usersA;
    });

    const best = healthyDiscovered[0];
    const currentHealth = serverHealthByUrl[serverUrl];
    const currentLatency = currentHealth?.latencyMs ?? Number.MAX_SAFE_INTEGER;
    const bestLatency = best.health?.latencyMs ?? Number.MAX_SAFE_INTEGER;
    const currentUnreachable = currentHealth?.status === "unreachable";
    const currentMissingFromDiscovery = !discoveredOnly.some((s) => s.url === serverUrl);
    const shouldSwitch =
      serverUrl !== best.server.url &&
      (currentUnreachable || bestLatency + 20 < currentLatency || currentMissingFromDiscovery);

    if (!shouldSwitch) {
      return;
    }

    lastAutoSwitchAtRef.current = now;
    void window.officeApi.setServerUrl(best.server.url);
    setServerUrl(best.server.url);
    const switchReason = currentUnreachable
      ? "current server became unreachable"
      : currentMissingFromDiscovery
        ? "current server disappeared from discovery"
        : "better latency was detected";
    setAutoSwitchNotice({
      id: now,
      message: `Auto-switched to ${best.server.name} (${best.server.host}) because ${switchReason}.`
    });
  }, [autoSelectBestServer, discoveredServers, serverHealthByUrl, serverUrl]);

  useEffect(() => {
    if (!autoSwitchNotice) {
      return;
    }
    const timer = window.setTimeout(() => setAutoSwitchNotice(null), 4500);
    return () => window.clearTimeout(timer);
  }, [autoSwitchNotice]);

  useEffect(() => {
    if (!autoRefreshCriticalDiscovery || refreshAgeSeconds <= 40 || refreshingDiscovery) {
      return;
    }
    const now = Date.now();
    const cooldownMs = 30000;
    if (now - lastCriticalAutoRefreshAtRef.current < cooldownMs) {
      return;
    }
    lastCriticalAutoRefreshAtRef.current = now;
    setRefreshingDiscovery(true);
    void window.officeApi
      .refreshDiscovery()
      .then((servers) => {
        setDiscoveredServers(servers);
        setLastDiscoveryRefreshAt(Date.now());
        setLastCriticalAutoRefreshAt(Date.now());
      })
      .finally(() => setRefreshingDiscovery(false));
  }, [autoRefreshCriticalDiscovery, refreshAgeSeconds, refreshingDiscovery]);

  useEffect(() => {
    return () => {
      if (typingTimerRef.current !== null) {
        window.clearTimeout(typingTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const socket = socketRef.current;
    if (!socket) {
      return;
    }
    socket.emit("department:join", {
      departmentId: selectedDepartment,
      clientId: clientIdRef.current
    });
  }, [selectedDepartment]);

  const onlineCount = useMemo(() => presence.filter((p) => p.online).length, [presence]);
  const discoveryStaleState = useMemo(() => {
    if (refreshAgeSeconds > 40) return "critical";
    if (refreshAgeSeconds > 20) return "warning";
    return "fresh";
  }, [refreshAgeSeconds]);
  const criticalAutoRefreshAgeSeconds = useMemo(() => {
    if (!lastCriticalAutoRefreshAt) {
      return null;
    }
    return Math.max(0, Math.floor((Date.now() - lastCriticalAutoRefreshAt) / 1000));
  }, [lastCriticalAutoRefreshAt, refreshAgeSeconds]);

  const handleInputChange = (value: string) => {
    setInput(value);
    setIsTyping(true);
    if (typingTimerRef.current !== null) {
      window.clearTimeout(typingTimerRef.current);
    }
    typingTimerRef.current = window.setTimeout(() => setIsTyping(false), 1100);
  };

  const triggerFilePicker = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    if (file) {
      setIsTyping(false);
      if (typingTimerRef.current !== null) {
        window.clearTimeout(typingTimerRef.current);
        typingTimerRef.current = null;
      }
    }
  };

  const clearTyping = () => {
    setIsTyping(false);
    if (typingTimerRef.current !== null) {
      window.clearTimeout(typingTimerRef.current);
      typingTimerRef.current = null;
    }
  };

  const sendMessage = () => {
    if (!input.trim() && !selectedFile) return;
    const text = selectedFile ? `📎 File attached: ${selectedFile.name}` : input.trim();
    socketRef.current?.emit("chat:send", {
      departmentId: selectedDepartment,
      sender: username,
      text
    });
    setInput("");
    setSelectedFile(null);
    clearTyping();
  };

  const sendBroadcast = () => {
    if (!input.trim()) return;
    socketRef.current?.emit("admin:broadcast", {
      sender: username,
      text: input.trim()
    });
    setInput("");
    clearTyping();
  };

  const scheduleReminder = () => {
    if (!input.trim()) return;
    socketRef.current?.emit("schedule:reminder", {
      sender: username,
      text: input.trim(),
      departmentId: selectedDepartment
    });
    setInput("");
    clearTyping();
  };

  const updateUsername = (next: string) => {
    setUsername(next);
    socketRef.current?.emit("username:update", { username: next, clientId: clientIdRef.current });
  };

  return (
    <div className="appShell">
      <div className="topologyLayer" />
      <header className="titleBar">
        <div className="titleBrand">
          <div className="titleBadge" />
          <div>
            <div className="appTitle">Liquid Glass LAN</div>
            <div className="appSubtitle">Real-time LAN messaging across your local network</div>
          </div>
        </div>
        <div className="windowControls">
          <button aria-label="Minimize" title="Minimize" className="windowButton minimize">{Icons.minimize}</button>
          <button aria-label="Restore" title="Restore" className="windowButton maximize">{Icons.maximize}</button>
          <button aria-label="Close" title="Close" className="windowButton close">{Icons.close}</button>
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar glassPanel">
          <h2>Departments</h2>
          {departments.map((d) => (
            <button
              key={d.id}
              className={d.id === selectedDepartment ? "active" : ""}
              onClick={() => {
                setSelectedDepartment(d.id);
                socketRef.current?.emit("department:join", { departmentId: d.id, clientId: clientIdRef.current });
              }}
            >
              #{d.name}
            </button>
          ))}
        <h3>User</h3>
        <input
          aria-label="Username"
          placeholder="Enter username"
          value={username}
          onChange={(e) => updateUsername(e.target.value)}
        />
        <h3>Storage</h3>
        <p className="small">{storageDir || "Not selected"}</p>
        <button onClick={() => window.officeApi.chooseStorageDirectory().then((p) => p && setStorageDir(p))}>
          Select Directory
        </button>
      </aside>

      <main className="chat">
        <header className="chatHeader">
          <div>#{selectedDepartment}</div>
          <div>{onlineCount} online</div>
        </header>

        <section className="messages">
          {isTyping ? (
            <div className="typingIndicator">
              <div className="typingText">Typing...</div>
              <div className="typingDots">
                <span />
                <span />
                <span />
              </div>
            </div>
          ) : null}
          {messages.map((m) => (
            <article key={m.id} className={`bubble ${m.kind} ${m.sender === username ? "sent" : "received"}`}>
              <div className="meta">
                <strong>{m.sender}</strong>
                <span>{new Date(m.createdAt).toLocaleTimeString()}</span>
              </div>
              <p>{m.text}</p>
            </article>
          ))}
        </section>

        <footer className="composer">
          <div className="composerTop">
            <input
              placeholder="Message, reminder, or admin broadcast..."
              value={input}
              onChange={(e) => handleInputChange(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            />
            <button type="button" className="attachButton" onClick={triggerFilePicker} title="Attach file">
              {Icons.attach}
            </button>
          </div>
          <input ref={fileInputRef} type="file" style={{ display: "none" }} onChange={handleFileChange} />
          {selectedFile ? (
            <div className="filePreview">
              <span>Attached: {selectedFile.name}</span>
              <button type="button" className="clearFile" onClick={() => setSelectedFile(null)}>
                Remove
              </button>
            </div>
          ) : null}
          <div className="actions">
            <button onClick={sendMessage} className="sendBtn" title="Send message">
              {Icons.send}
              Send
            </button>
            <button onClick={sendBroadcast} className="broadcastBtn" title="Send to all departments">
              {Icons.broadcast}
              Broadcast
            </button>
            <button onClick={scheduleReminder} className="reminderBtn" title="Schedule reminder">
              {Icons.clock}
              Reminder
            </button>
          </div>
        </footer>
      </main>

      <aside className="panel">
        <div className="userHeader">
          <h3>{Icons.users} User List</h3>
          <button
            type="button"
            className={`filterButton ${showOnlyOnlineUsers ? "active" : ""}`}
            onClick={() => setShowOnlyOnlineUsers((prev) => !prev)}
            title={showOnlyOnlineUsers ? "Show all users" : "Show only online users"}
          >
            {showOnlyOnlineUsers ? "Online only" : "All users"}
          </button>
        </div>
        {presence
          .filter((p) => (showOnlyOnlineUsers ? p.online : true))
          .map((p, idx) => (
            <div key={p.clientId || `${p.username}-${idx}`} className="userRow">
              <span className={p.online ? "dot on" : "dot off"} />
              {p.username} <span className="small">({p.departmentId})</span>
            </div>
          ))}

        <div className="networkWidget glassPanel">
          <div className="networkWidgetHeader">
            <span className={`pulseDot ${connectionState === "online" ? "online" : "offline"}`} />
            <div>
              <div>LAN Active</div>
              <div className="small">Network pulse and topology status</div>
            </div>
          </div>
          <div className="networkStats">
            <div>
              <span>Peers</span>
              <strong>{onlineCount}</strong>
            </div>
            <div>
              <span>Discovery</span>
              <strong>{refreshAgeSeconds}s</strong>
            </div>
          </div>
          <div className="waveform">
            <span /><span /><span /><span /><span />
          </div>
        </div>

        <h3>Settings</h3>
        <p className="small">Server: {serverUrl}</p>
        <p className="small">Connection: {connectionState}</p>
        <h3>LAN Servers</h3>
        <button
          onClick={() => {
            setRefreshingDiscovery(true);
            void window.officeApi
              .refreshDiscovery()
              .then((servers) => {
                setDiscoveredServers(servers);
                setLastDiscoveryRefreshAt(Date.now());
              })
              .finally(() => setRefreshingDiscovery(false));
          }}
          disabled={refreshingDiscovery}
          className="refreshBtn"
          title="Refresh server list"
        >
          {Icons.refresh}
          {refreshingDiscovery ? "Refreshing..." : "Refresh"}
        </button>
        <p className="small">Last refreshed {refreshAgeSeconds}s ago</p>
        {discoveryStaleState !== "fresh" ? (
          <p className={`small discoveryWarning ${discoveryStaleState}`}>
            {discoveryStaleState === "critical"
              ? "Discovery data is stale. LAN list may be outdated."
              : "Discovery data is aging. Consider refreshing."}
          </p>
        ) : null}
        {criticalAutoRefreshAgeSeconds !== null && criticalAutoRefreshAgeSeconds < 120 ? (
          <p className="small discoveryAutoRefreshNote">
            Auto-refresh triggered {criticalAutoRefreshAgeSeconds}s ago due to critical staleness.
          </p>
        ) : null}
        {displayedServers.length ? (
          displayedServers.map((server) => (
            <button
              key={server.id}
              className={`lanServerButton ${server.url === serverUrl ? "active" : ""}`}
              onClick={() => {
                void window.officeApi.setServerUrl(server.url);
                setServerUrl(server.url);
                setAutoSwitchNotice(null);
              }}
            >
              <span>{server.name}</span>
              <span className="small">
                {server.port > 0 ? `${server.host}:${server.port}` : server.host}
              </span>
              <span className="small">
                {serverHealthByUrl[server.url]?.status === "healthy"
                  ? `Healthy | ${serverHealthByUrl[server.url]?.latencyMs ?? "-"}ms | ${
                      serverHealthByUrl[server.url]?.onlineUsers ?? "-"
                    } online`
                  : "Unreachable"}
              </span>
            </button>
          ))
        ) : (
          <p className="small">No LAN servers discovered yet.</p>
        )}
        <label>
          <input
            type="checkbox"
            checked={notificationsEnabled}
            onChange={(e) => setNotificationsEnabled(e.target.checked)}
          />
          {Icons.bell} Notifications
        </label>
        <label>
          <input type="checkbox" checked={floatingBubble} onChange={(e) => setFloatingBubble(e.target.checked)} />
          Floating bubble mode
        </label>
        <label>
          <input
            type="checkbox"
            checked={autoSelectBestServer}
            onChange={(e) => {
              const enabled = e.target.checked;
              setAutoSelectBestServer(enabled);
              void window.officeApi.setSettings({ autoSelectBestServer: enabled });
            }}
          />
          Auto-select best LAN server
        </label>
        <label>
          <input
            type="checkbox"
            checked={autoRefreshCriticalDiscovery}
            onChange={(e) => {
              const enabled = e.target.checked;
              setAutoRefreshCriticalDiscovery(enabled);
              void window.officeApi.setSettings({ autoRefreshCriticalDiscovery: enabled });
            }}
          />
          Auto-refresh when discovery is critical
        </label>
        <p className="small">
          Confidentiality, encryption, logs, scheduling, offline queue, and secure file storage are scaffolded server-side
          and ready for deeper hardening.
        </p>
      </aside>

      {autoSwitchNotice ? (
        <div key={autoSwitchNotice.id} className="toastInfo" role="status" aria-live="polite">
          {autoSwitchNotice.message}
        </div>
      ) : null}

      {floatingBubble ? (
        <div className={`floatingBubble ${isWindowMinimized ? "expanded" : ""}`}>
          {isWindowMinimized ? (
            <div className="userListBubble">
              <div className="bubbleTitle">Active Users</div>
              <div className="bubbleUserList">
                {presence
                  .filter((p) => p.online)
                  .map((p, idx) => (
                    <div key={p.clientId || `${p.username}-${idx}`} className="bubbleUserRow">
                      <span className="dot on" />
                      <span className="name">{p.username}</span>
                      <span className="dept">{p.departmentId}</span>
                    </div>
                  ))}
              </div>
              <div className="bubbleFooter">Click tray to restore</div>
            </div>
          ) : (
            "LAN"
          )}
        </div>
      ) : null}
    </div>
  </div>
  );
}
