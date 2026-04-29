# LAN Office Executable

## Overview
LAN Office is a local network communication and file transfer tool packaged as a standalone Windows executable.

## Features
- **ZeroConf Service Discovery**: Automatically discovers other LAN Office instances on the network
- **Real-time Chat**: Send messages to other users
- **File Transfer**: Send files between connected users
- **Direct Messages**: Chat with specific users privately
- **Network Monitoring**: Shows online users and connection status
- **Persistent Settings**: Remembers username and download preferences

## Installation
No installation required! Simply run `LANOffice.exe` from anywhere on your system.

## System Requirements
- Windows 10/11
- Network connectivity (WiFi or Ethernet)
- mDNS/Bonjour service enabled (usually enabled by default)

## Usage

### First Time Setup
1. Run `LANOffice.exe`
2. Enter your display name in the login screen
3. Click "Join Network →"

### Basic Chat
1. Select a user from the sidebar (left panel)
2. Type your message in the input box at the bottom
3. Press Enter or click Send

### File Transfer
1. Select a user from the sidebar
2. Click the "📎 File" button
3. Choose a file to send
4. The recipient will be prompted to accept

### Direct Messages
1. Click on a user in the sidebar to enter DM mode
2. The title will change to "💬 DM → [username]"
3. Messages will go only to that user
4. Click "← Back to Group" to return to group chat

### Settings
- Click the "👤 Profile" button to change your name
- Click "📂 Folder" to set the default download location
- Settings are automatically saved

## Network Discovery
LAN Office uses ZeroConf (Bonjour) technology for automatic peer discovery:
- **Service Type**: `_lanoffice._tcp.local.`
- **Ports**: 55001 (chat), 55002 (file transfer)
- **Discovery**: Works across subnets and network configurations

## Troubleshooting

### Can't see other users?
- Ensure both computers are on the same network
- Check if mDNS is enabled in your network settings
- Try disabling/enabling WiFi
- Check Windows Firewall settings

### File transfer not working?
- Ensure the recipient accepts the file transfer
- Check download folder permissions
- Verify sufficient disk space

### Application won't start?
- Check if ports 55001-55002 are available
- Try running as administrator
- Check Windows Event Viewer for errors

## File Locations
When run, LAN Office creates these files in the same directory:
- `lan_config.json` - User settings and preferences
- `chat_history.jsonl` - Chat message history
- `lan_office.log` - Application logs for troubleshooting

## Security Notes
- Only communicates with other LAN Office instances
- Files are transferred directly between users (no server)
- All traffic stays on your local network
- No data is sent to external servers

## Technical Details
- **Built with**: PyInstaller
- **Dependencies**: tkinter, zeroconf, PIL, winsound
- **Executable size**: ~21MB (includes all dependencies)
- **Platform**: Windows 64-bit

## Version Information
- LAN Office v1.0 with ZeroConf discovery
- Built on: 2026-04-29
- Python: 3.14.4

## Support
If you encounter issues:
1. Check the `lan_office.log` file for error messages
2. Ensure network connectivity
3. Try restarting the application
4. Verify no other applications are using ports 55001-55002

## License
LAN Office is free software for local network communication.