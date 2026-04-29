# LAN Office - ZeroConf Migration

## What Changed

LAN Office has been upgraded from UDP broadcast discovery to **ZeroConf (Bonjour/mDNS)** service discovery for better reliability and cross-platform compatibility.

## Why ZeroConf?

### Advantages over UDP Broadcast:
- **🔧 Automatic discovery**: No need to calculate broadcast addresses
- **🌐 Cross-platform**: Works consistently across Windows, macOS, Linux
- **🔄 Self-healing**: Automatically handles network changes
- **📋 Structured data**: Services include IP, port, and metadata
- **🏢 Enterprise-ready**: Works across complex network topologies
- **📊 Better reliability**: Uses standard protocols (mDNS) instead of raw UDP

### Previous UDP Issues Fixed:
- Broadcast address calculation failures
- Firewall blocking issues
- Subnet configuration problems
- Inconsistent behavior across networks

## Technical Details

### Service Registration:
- **Service Type**: `_lanoffice._tcp.local.`
- **Service Name**: `{username}._lanoffice._tcp.local.`
- **Properties**: Version, IP address
- **Ports**: Chat and file transfer ports

### Discovery Process:
1. Register local service with ZeroConf
2. Browse for other `_lanoffice._tcp.local.` services
3. Automatically discover peers on the network
4. Update peer list when services appear/disappear

### Network Requirements:
- mDNS must be enabled on the network
- No special firewall rules needed (uses standard mDNS port 5353)
- Works across different subnets and VLANs

## Configuration

The settings window has been simplified:
- ✅ Display name
- ✅ TCP Chat Port
- ✅ TCP File Port
- ✅ Max history load

Removed settings:
- ❌ UDP Broadcast Port (no longer needed)
- ❌ Broadcast Interval (handled automatically)

## Testing

To test ZeroConf discovery:
```bash
python test_zeroconf.py
```

This will register a test service and show discovered services.

## Compatibility

- **Backwards compatible**: Can discover other ZeroConf-enabled LAN Office instances
- **Forward compatible**: Will work with future versions using the same service type
- **Cross-version**: Different versions can discover each other

## Troubleshooting

If discovery doesn't work:
1. Check if mDNS is enabled on your network
2. Verify no firewall blocks port 5353 (mDNS)
3. Check `lan_office.log` for ZeroConf errors
4. Try the test script to isolate issues

## Migration Notes

- No user data migration needed
- Existing chat history preserved
- Settings automatically updated (old broadcast settings ignored)
- All existing functionality maintained