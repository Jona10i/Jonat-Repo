/// <reference types="vite/client" />

declare global {
  interface Window {
    officeApi: {
      getSettings: () => Promise<Record<string, unknown>>;
      setSettings: (updates: Record<string, unknown>) => Promise<Record<string, unknown>>;
      getServerUrl: () => Promise<string>;
      getDiscoveredServers: () => Promise<
        Array<{ id: string; name: string; host: string; port: number; url: string; lastSeenAt: string }>
      >;
      setServerUrl: (serverUrl: string) => Promise<string>;
      chooseStorageDirectory: () => Promise<string | null>;
      onStorageSelected: (handler: (path: string) => void) => void;
      onServerUrl: (handler: (serverUrl: string) => void) => void;
      onServerList: (
        handler: (servers: Array<{ id: string; name: string; host: string; port: number; url: string; lastSeenAt: string }>) => void
      ) => void;
    };
  }
}

export {};
