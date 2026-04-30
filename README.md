# Office LAN Comm

LAN-first office communication and secure file transfer suite with a Discord-like UI.

## Included foundation

- Departments and channel-like rooms
- Username editing
- Admin broadcasts and notifications
- Chat bubbles and user list
- Online/offline file messages
- Reminder and scheduling payload support
- Tray/background operation
- Auto-start and minimize behavior
- Right-side docked window shell
- First-run storage directory selection
- Local audit logging
- Encryption hooks for secure transfer workflows

## Project structure

- `apps/server`: Node + Socket.IO LAN backend
- `apps/desktop`: Electron shell + React UI

## Quick start

1. Install dependencies:
   - `npm install`
2. Start both server and desktop app:
   - `npm run dev`

## Notes

- Default backend: `http://localhost:4010`
- Desktop UI docks on the right side by default.
- First run asks for preferred storage directory.
