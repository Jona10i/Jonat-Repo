/// <reference types="vite/client" />

declare global {
  interface Window {
    officeApi: {
      getSettings: () => Promise<Record<string, unknown>>;
      setSettings: (updates: Record<string, unknown>) => Promise<Record<string, unknown>>;
      getServerUrl: () => Promise<string>;
      chooseStorageDirectory: () => Promise<string | null>;
      onStorageSelected: (handler: (path: string) => void) => void;
      onServerUrl: (handler: (serverUrl: string) => void) => void;
    };
  }
}

export {};
