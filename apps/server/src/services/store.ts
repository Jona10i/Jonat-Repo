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

type PresenceMap = Map<string, { username: string; online: boolean }>;

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
const presence: PresenceMap = new Map();

export const store = {
  listDepartments: () => departments,
  listMessagesByDepartment: (departmentId: string) =>
    messages.filter((m) => m.departmentId === departmentId).slice(-150),
  putPresence: (socketId: string, username: string, online = true) => {
    presence.set(socketId, { username, online });
  },
  removePresence: (socketId: string) => {
    presence.delete(socketId);
  },
  listPresence: () => Array.from(presence.values()),
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
