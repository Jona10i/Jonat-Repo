import fs from "node:fs";
import path from "node:path";
import { v4 as uuidv4 } from "uuid";

export type Department = {
  id: string;
  name: string;
};

export type ChatMessage = {
  id: string;
  departmentId: string;
  sender: string;
  text: string;
  createdAt: string;
  kind: "message" | "broadcast" | "notification" | "reminder";
};

type PresenceEntry = {
  clientId: string;
  username: string;
  online: boolean;
  departmentId: string;
  lastSeenAt: string;
};

const dataDir = path.resolve(process.cwd(), "data");
const logsPath = path.join(dataDir, "logs.ndjson");

if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

const departments: Department[] = [
  { id: "general", name: "General" },
  { id: "engineering", name: "Engineering" },
  { id: "hr", name: "HR" },
  { id: "ops", name: "Operations" }
];

const messages: ChatMessage[] = [];
const presenceByClient: Map<string, PresenceEntry> = new Map();
const socketToClient: Map<string, string> = new Map();

export const store = {
  listDepartments: () => departments,
  listMessagesByDepartment: (departmentId: string) =>
    messages.filter((m) => m.departmentId === departmentId).slice(-150),
  putPresence: (socketId: string, username: string, online = true) => {
    const clientId = socketToClient.get(socketId) ?? socketId;
    socketToClient.set(socketId, clientId);
    presenceByClient.set(clientId, {
      clientId,
      username,
      online,
      departmentId: "general",
      lastSeenAt: new Date().toISOString()
    });
  },
  joinPresence: (socketId: string, clientId: string, username: string, departmentId: string) => {
    socketToClient.set(socketId, clientId);
    presenceByClient.set(clientId, {
      clientId,
      username,
      online: true,
      departmentId,
      lastSeenAt: new Date().toISOString()
    });
  },
  updatePresenceUsername: (clientId: string, username: string) => {
    const current = presenceByClient.get(clientId);
    if (!current) {
      return;
    }
    presenceByClient.set(clientId, {
      ...current,
      username,
      online: true,
      lastSeenAt: new Date().toISOString()
    });
  },
  updatePresenceDepartment: (clientId: string, departmentId: string) => {
    const current = presenceByClient.get(clientId);
    if (!current) {
      return;
    }
    presenceByClient.set(clientId, {
      ...current,
      departmentId,
      online: true,
      lastSeenAt: new Date().toISOString()
    });
  },
  removePresence: (socketId: string) => {
    const clientId = socketToClient.get(socketId);
    socketToClient.delete(socketId);
    if (!clientId) {
      return;
    }
    const current = presenceByClient.get(clientId);
    if (!current) {
      return;
    }
    presenceByClient.set(clientId, {
      ...current,
      online: false,
      lastSeenAt: new Date().toISOString()
    });
  },
  listPresence: () =>
    Array.from(presenceByClient.values()).sort((a, b) => {
      if (a.online !== b.online) {
        return a.online ? -1 : 1;
      }
      return a.username.localeCompare(b.username);
    }),
  countOnlinePresence: () => Array.from(presenceByClient.values()).filter((entry) => entry.online).length,
  addMessage: (
    payload: Omit<ChatMessage, "id" | "createdAt"> & { id?: string; createdAt?: string }
  ) => {
    const message: ChatMessage = {
      id: payload.id ?? uuidv4(),
      createdAt: payload.createdAt ?? new Date().toISOString(),
      departmentId: payload.departmentId,
      sender: payload.sender,
      text: payload.text,
      kind: payload.kind
    };
    messages.push(message);
    return message;
  },
  appendLog: (event: string, details: unknown) => {
    const line = JSON.stringify({
      at: new Date().toISOString(),
      event,
      details
    });
    fs.appendFileSync(logsPath, `${line}\n`);
  }
};
