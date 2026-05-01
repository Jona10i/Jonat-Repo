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
  const [connectionState, setConnectionState] = useState<"connecting" | "online" | "offline">("connecting");
  const [input, setInput] = useState("");
  const [storageDir, setStorageDir] = useState<string>("");
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [floatingBubble, setFloatingBubble] = useState(true);
  const selectedDepartmentRef = useRef(selectedDepartment);
  const clientIdRef = useRef(getOrCreateClientId());

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
    window.officeApi.onServerUrl((url) => {
      if (url) {
        setServerUrl(url);
      }
    });
    window.officeApi.onServerList((servers) => setDiscoveredServers(servers));

    void window.officeApi.getSettings().then((settings) => {
      const dir = settings.storageDirectory;
      if (typeof dir === "string") {
        setStorageDir(dir);
      }
    });

    window.officeApi.onStorageSelected((path) => setStorageDir(path));
  }, []);

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
        {discoveredServers.length ? (
          discoveredServers.map((server) => (
            <button
              key={server.id}
              className={server.url === serverUrl ? "active" : ""}
              onClick={() => {
                void window.officeApi.setServerUrl(server.url);
                setServerUrl(server.url);
              }}
            >
              {server.name}
              <span className="small">
                {server.host}:{server.port}
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
        <p className="small">
          Confidentiality, encryption, logs, scheduling, offline queue, and secure file storage are scaffolded server-side
          and ready for deeper hardening.
        </p>
      </aside>

      {floatingBubble ? <div className="floatingBubble">LAN</div> : null}
    </div>
  );
}
