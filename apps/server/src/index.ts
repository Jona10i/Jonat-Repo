import cors from "cors";
import express from "express";
import { createServer } from "node:http";
import os from "node:os";
import { Bonjour } from "bonjour-service";
import { Server } from "socket.io";
import { store } from "./services/store.js";

const app = express();
app.use(cors());
app.use(express.json());

app.get("/health", (_, res) => {
  res.json({ ok: true, service: "office-lan-comm-server" });
});

app.get("/departments", (_, res) => {
  res.json(store.listDepartments());
});

app.get("/messages/:departmentId", (req, res) => {
  res.json(store.listMessagesByDepartment(req.params.departmentId));
});

const server = createServer(app);
const io = new Server(server, {
  cors: { origin: "*" }
});

io.on("connection", (socket) => {
  socket.on("presence:join", ({ username }) => {
    store.putPresence(socket.id, username, true);
    store.appendLog("presence.join", { username, socketId: socket.id });
    io.emit("presence:list", store.listPresence());
  });

  socket.on("username:update", ({ username }) => {
    store.putPresence(socket.id, username, true);
    store.appendLog("username.update", { username, socketId: socket.id });
    io.emit("presence:list", store.listPresence());
  });

  socket.on("department:join", ({ departmentId }) => {
    socket.join(departmentId);
    store.appendLog("department.join", { socketId: socket.id, departmentId });
    socket.emit("messages:seed", store.listMessagesByDepartment(departmentId));
  });

  socket.on("chat:send", ({ departmentId, sender, text }) => {
    const message = store.addMessage({
      departmentId,
      sender,
      text,
      kind: "message"
    });
    store.appendLog("chat.send", message);
    io.to(departmentId).emit("chat:new", message);
  });

  socket.on("admin:broadcast", ({ sender, text }) => {
    const message = store.addMessage({
      departmentId: "general",
      sender,
      text,
      kind: "broadcast"
    });
    store.appendLog("admin.broadcast", message);
    io.emit("chat:new", message);
    io.emit("notification:new", {
      title: "Admin Broadcast",
      body: text
    });
  });

  socket.on("schedule:reminder", ({ sender, text, departmentId }) => {
    const reminder = store.addMessage({
      sender,
      text: `[Reminder] ${text}`,
      departmentId,
      kind: "reminder"
    });
    store.appendLog("schedule.reminder", reminder);
    io.to(departmentId).emit("chat:new", reminder);
  });

  socket.on("disconnect", () => {
    store.removePresence(socket.id);
    store.appendLog("presence.leave", { socketId: socket.id });
    io.emit("presence:list", store.listPresence());
  });
});

const port = Number(process.env.PORT ?? 4010);
const bonjour = new Bonjour();

function resolveHost() {
  const interfaces = os.networkInterfaces();
  for (const entries of Object.values(interfaces)) {
    for (const entry of entries ?? []) {
      if (entry.family === "IPv4" && !entry.internal) {
        return entry.address;
      }
    }
  }
  return "127.0.0.1";
}

server.listen(port, "0.0.0.0", () => {
  const host = resolveHost();
  bonjour.publish({
    name: `Office LAN Comm @ ${host}`,
    type: "office-lan-comm",
    protocol: "tcp",
    port
  });
  console.log(`LAN server running on http://${host}:${port}`);
  console.log("ZeroConf service published: _office-lan-comm._tcp");
});

function shutdown() {
  bonjour.unpublishAll(() => {
    bonjour.destroy();
    process.exit(0);
  });
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
