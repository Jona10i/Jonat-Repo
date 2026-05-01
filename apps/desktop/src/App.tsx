import { useEffect, useMemo, useRef, useState } from "react";
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
  const selectedDepartmentRef = useRef(selectedDepartment);
  const clientIdRef = useRef(getOrCreateClientId());
  const lastAutoSwitchAtRef = useRef(0);
  const lastCriticalAutoRefreshAtRef = useRef(0);
  const [lastDiscoveryRefreshAt, setLastDiscoveryRefreshAt] = useState<number>(Date.now());
  const [refreshingDiscovery, setRefreshingDiscovery] = useState(false);
  const [refreshAgeSeconds, setRefreshAgeSeconds] = useState(0);
  const [lastCriticalAutoRefreshAt, setLastCriticalAutoRefreshAt] = useState<number | null>(null);

  useEffect(() => {
    selectedDepartmentRef.current = selectedDepartment;
  }, [selectedDepartment]);

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

  const sendMessage = () => {
    if (!input.trim()) return;
    socketRef.current?.emit("chat:send", {
      departmentId: selectedDepartment,
      sender: username,
      text: input.trim()
    });
    setInput("");
  };

  const sendBroadcast = () => {
    if (!input.trim()) return;
    socketRef.current?.emit("admin:broadcast", {
      sender: username,
      text: input.trim()
    });
    setInput("");
  };

  const scheduleReminder = () => {
    if (!input.trim()) return;
    socketRef.current?.emit("schedule:reminder", {
      sender: username,
      text: input.trim(),
      departmentId: selectedDepartment
    });
    setInput("");
  };

  const updateUsername = (next: string) => {
    setUsername(next);
    socketRef.current?.emit("username:update", { username: next, clientId: clientIdRef.current });
  };

  return (
    <div className="layout">
      <aside className="sidebar">
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
          {messages.map((m) => (
            <article key={m.id} className={`bubble ${m.kind}`}>
              <div className="meta">
                <strong>{m.sender}</strong>
                <span>{new Date(m.createdAt).toLocaleTimeString()}</span>
              </div>
              <p>{m.text}</p>
            </article>
          ))}
        </section>

        <footer className="composer">
          <input
            placeholder="Message, reminder, or admin broadcast..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <div className="actions">
            <button onClick={sendMessage}>Send</button>
            <button onClick={sendBroadcast}>Broadcast</button>
            <button onClick={scheduleReminder}>Reminder</button>
          </div>
        </footer>
      </main>

      <aside className="panel">
        <h3>User List</h3>
        {presence.map((p, idx) => (
          <div key={p.clientId || `${p.username}-${idx}`} className="userRow">
            <span className={p.online ? "dot on" : "dot off"} />
            {p.username} <span className="small">({p.departmentId})</span>
          </div>
        ))}

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
        >
          {refreshingDiscovery ? "Refreshing..." : "Refresh Discovery"}
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
          Notifications / Pop-ups
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

      {floatingBubble ? <div className="floatingBubble">LAN</div> : null}
    </div>
  );
}
