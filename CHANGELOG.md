# Changelog

All notable changes to this project will be documented in this file. See [commit-and-tag-version](https://github.com/absolute-version/commit-and-tag-version) for commit guidelines.

## [0.7.0-alpha](https://github.com/meduseld404/meduseld-backend/compare/v0.6.0-alpha...v0.7.0-alpha) (2026-03-24)


### New Features

* **api:** Add admin users proxy via health.meduseld.io ([cb391df](https://github.com/meduseld404/meduseld-backend/commit/cb391dfc220ff1d940630218545d588cd85f3210))
* **api:** Add calendar events model and API endpoints ([2ba6ae6](https://github.com/meduseld404/meduseld-backend/commit/2ba6ae6d89bea9e4fbde5ecf5ffdf422e0cd0e7c))
* **api:** Add edit endpoint for calendar events ([99c0548](https://github.com/meduseld404/meduseld-backend/commit/99c05485a1ce1e07fd578f56d5fb926a1b32ecb0))
* **api:** Add has_jellyfin to user model and update steering docs ([c687886](https://github.com/meduseld404/meduseld-backend/commit/c6878861369feeab51ac5546365e9448618cbe76))
* **api:** Add RSVP support for calendar events ([f4c39bb](https://github.com/meduseld404/meduseld-backend/commit/f4c39bb8e4b3aa30653e43a03b614a6cda1a3955))
* **health:** Add calendar proxy routes through health.meduseld.io ([a1bfd2b](https://github.com/meduseld404/meduseld-backend/commit/a1bfd2b536325cb5494efbfcf51ade57c728d098))
* **panel:** Add dynamic version badge fetched from GitHub releases ([eee947c](https://github.com/meduseld404/meduseld-backend/commit/eee947c61d3328576d0eb3c803916d78a35d51f0))


### Bug Fixes

* **api:** Add debug logging to admin-users cookie auth ([e371c14](https://github.com/meduseld404/meduseld-backend/commit/e371c143d985c2829db7c96911984a75e2c33d78))
* **api:** Add DELETE to CORS allowed methods for calendar event deletion ([f457500](https://github.com/meduseld404/meduseld-backend/commit/f4575000bad874db9a0afb9c9512863d966c567a))
* **api:** Rename admin-users endpoint to avoid ad-blocker false positives ([0c2a008](https://github.com/meduseld404/meduseld-backend/commit/0c2a008b0997bc9afed85f9db09cb56799243022))
* **api:** Use get_or_create in cookie auth for first-time users ([9f43650](https://github.com/meduseld404/meduseld-backend/commit/9f43650b69573d29765cc43b7c3fadddb50fac5a))
* **api:** Use strptime for calendar date parsing and improve error logging ([4137409](https://github.com/meduseld404/meduseld-backend/commit/41374094c9ba06697e75f14eb65eba188f8ee1f0))
* **auth:** Accept cf_token via query param and request body ([5732eca](https://github.com/meduseld404/meduseld-backend/commit/5732eca595ea356b4050c646647f8cba70e4d442))
* **auth:** Route admin API through health host with X-CF-Authorization header ([3997dd2](https://github.com/meduseld404/meduseld-backend/commit/3997dd23fde4d965cd46f2dcdb9a9027b9dd92b5))
* **config:** Update contact email to admin@meduseld.io ([0eb4613](https://github.com/meduseld404/meduseld-backend/commit/0eb461323e6dd195d6611c925332b3823ff1e281))
* **panel:** Write stop marker to startup log for clean shutdown detection ([af19bfb](https://github.com/meduseld404/meduseld-backend/commit/af19bfb0f4e0fbe0d129d532e21aebbe70ae30cd))


### Styling

* **panel:** Add tooltip refresh after dynamic badge rendering ([3b70995](https://github.com/meduseld404/meduseld-backend/commit/3b7099513cc5dad7640819be60d16d236e694a8d))
* **panel:** Change version badge color to warning yellow to match quietarcade link ([031918e](https://github.com/meduseld404/meduseld-backend/commit/031918ecda7d7d0291b2f026f481cedc4e38168d))
* **panel:** Standardize terminal profile container and sync steering ([6286a90](https://github.com/meduseld404/meduseld-backend/commit/6286a90e648be8488f05f5055271333f8d79ad25))

## [0.6.0-alpha](https://github.com/meduseld404/meduseld-backend/compare/v0.5.0-alpha...v0.6.0-alpha) (2026-03-18)


### New Features

* **api:** Use Discord role for immediate admin detection on terminal page ([d6a040d](https://github.com/meduseld404/meduseld-backend/commit/d6a040d3f2b2387f370cf63a1fe6a054fbab1bd9))
* **auth:** Add /api/sync-identity endpoint for client-side Discord data sync ([eb57950](https://github.com/meduseld404/meduseld-backend/commit/eb57950dd0555c0ebc0a204c283886f3b1b41a78))
* **auth:** Add client-side Discord identity sync to panel page ([7fd9402](https://github.com/meduseld404/meduseld-backend/commit/7fd9402ebb636cdc108c29edfffd76aa6c13a27b))
* **auth:** Add PostgreSQL database and user authentication ([c3074c2](https://github.com/meduseld404/meduseld-backend/commit/c3074c2ed94102d2f2e99ede3201475ec042e83d))
* **auth:** Add role-based access control and admin user management API ([3f192e9](https://github.com/meduseld404/meduseld-backend/commit/3f192e925ce004d008e2eaef42f84b512772986f))
* **auth:** Auto-sync admin role from Discord on login ([4ee5c43](https://github.com/meduseld404/meduseld-backend/commit/4ee5c43b6d71e60f3ad85a4346e2694427ec2519))
* **auth:** Fetch Cloudflare Access identity endpoint for Discord user data ([4770095](https://github.com/meduseld404/meduseld-backend/commit/4770095db797482fd18b1e53ebbc3a1bcfa5ecc8))
* **backup:** Return backup filename in status response ([3b693a6](https://github.com/meduseld404/meduseld-backend/commit/3b693a6a48e5abc11599a05a439b20a975c89248))
* **config:** Add power consumption monitoring backend ([bfe888a](https://github.com/meduseld404/meduseld-backend/commit/bfe888ace0fcaac209b12558d4ac3e1a59d37e33))
* **monitoring:** Add standalone system monitoring microservice ([9611c4d](https://github.com/meduseld404/meduseld-backend/commit/9611c4db75921c4132c7ee5f6323cc89e2f80bbf))
* **panel:** Add logout button to profile dropdown ([85b4f32](https://github.com/meduseld404/meduseld-backend/commit/85b4f3265f4b1556b36265178ccc7cceee39c43c))
* **panel:** Add user profile display to control panel nav bar ([ee9963a](https://github.com/meduseld404/meduseld-backend/commit/ee9963a34a70aa957098cb982126e4563a0b34b0))
* **panel:** Move profile to rightmost position and add to terminal page ([4181961](https://github.com/meduseld404/meduseld-backend/commit/418196140c81c51dbed4d06cec2de404b2fe2130))
* **proxy:** Add Jellyfin auto-provisioning and SSO login ([907f002](https://github.com/meduseld404/meduseld-backend/commit/907f002367c8c2d1e0e82a4074b3d259f51268ef))


### Bug Fixes

* **api:** Add explicit CORS preflight handlers for cross-origin API endpoints ([f460666](https://github.com/meduseld404/meduseld-backend/commit/f460666a48fc95a55923c1919742e61373ea28ad))
* **api:** Create user on sync-identity if not exists ([533feda](https://github.com/meduseld404/meduseld-backend/commit/533feda1c6719f6fe80ac0fb3dc99ab5a3955d6b))
* **auth:** Add CORS credentials header for cross-origin /api/me requests ([0c67efd](https://github.com/meduseld404/meduseld-backend/commit/0c67efdb1a098f09a5e6cc2f49cd66947a77fe75))
* **auth:** Correct health bypass path in PUBLIC_PATHS ([cd7274c](https://github.com/meduseld404/meduseld-backend/commit/cd7274cf14693988aa34adc053cee265ed3e4dc0))
* **auth:** Fall back to CF_Authorization cookie for cross-origin API auth ([797e7e2](https://github.com/meduseld404/meduseld-backend/commit/797e7e21f3ad8a92195e3fb1adeab90e413715f8))
* **auth:** Look up user by email fallback to prevent duplicate accounts ([93140e4](https://github.com/meduseld404/meduseld-backend/commit/93140e48248f693e3d2689b9a2f5297cc9de33ca))
* **config:** Add contents read permission to auto-assign workflow ([53575d4](https://github.com/meduseld404/meduseld-backend/commit/53575d4a9a2b0611e730e97cb5b2598fad243859))
* **panel:** Distinguish idle shutdown from unexpected process death in logs ([c43a1d2](https://github.com/meduseld404/meduseld-backend/commit/c43a1d23ee8dd3bfb50c05108fdff8abebd5d41c))
* **panel:** Fix backup dropdown not opening ([e7340eb](https://github.com/meduseld404/meduseld-backend/commit/e7340ebdf322bd53600b5f21fb567777d20a9eeb))
* **panel:** Hide SSH terminal button for non-admin users ([677d4d4](https://github.com/meduseld404/meduseld-backend/commit/677d4d4681b9c367adff373cdd79f18521695c7d))
* **panel:** Suppress false process death alert on user-initiated kill ([11e4c09](https://github.com/meduseld404/meduseld-backend/commit/11e4c0944d9ad8d133261ddf966bec3881ffc9c5))


### Refactoring

* **auth:** Replace db.create_all with Alembic migrations ([bcd2bf3](https://github.com/meduseld404/meduseld-backend/commit/bcd2bf39d87ad93e6df049cb37e817da819c1879))
* **monitoring:** Replace silent exception passes with proper logging ([649d889](https://github.com/meduseld404/meduseld-backend/commit/649d8891d5610c5e18e5de441698b0cd091f21e3))
* **panel:** Use shared auth.js profile widget instead of custom Jinja ([49be14a](https://github.com/meduseld404/meduseld-backend/commit/49be14a034e8ae0be7a840a40d7a79500f7da244))


### Styling

* **panel:** Lighten username and role text in profile dropdown ([e79dd2b](https://github.com/meduseld404/meduseld-backend/commit/e79dd2bc094cf1859049213aba2b0d82aee751fe)), closes [#a0a0b8](https://github.com/meduseld404/meduseld-backend/issues/a0a0b8)
* **panel:** Match SSH button padding to Backup dropdown size ([9b2ddad](https://github.com/meduseld404/meduseld-backend/commit/9b2ddad9f2c5daa20897a80d455e4361874cfead))
* **panel:** Rename Startup Script Logs panel to Server Process Logs ([39981af](https://github.com/meduseld404/meduseld-backend/commit/39981af9701949a5246f166ea17aa847397aa0ef))


### Reverts

* **config:** Remove power monitoring from Flask app ([619ceb9](https://github.com/meduseld404/meduseld-backend/commit/619ceb987ff2c7783cc9d90c316f311d45c2de81))

## [0.5.0-alpha] - 2026-03-14

### New Features

- **Standalone Reboot Microservice**: New microservice on port 5002 for remote server reboots, independent of the main Flask app
- **Standalone Backup Microservice**: New microservice on port 5003 for triggering game save backups to Google Drive via systemd
- **Health Subdomain Proxy**: `health.meduseld.io/check/backup`, `/check/backup-status`, and `/check/reboot` now proxy to the standalone microservices
- **System Logs on Health Subdomain**: Moved system logs endpoint to `health.meduseld.io/check/system-logs` for public access
- **Idle Shutdown**: Server automatically shuts down after 15 minutes with 0 players online
- **Backup Dropdown Menu**: Consolidated backup buttons into a dropdown with "Download Backup" and "Backup to Cloud" options
- **Google Drive OAuth**: PKCE code_verifier persistence across OAuth flow for cloud backups
- **Snowmane SSH Access**: Added `snowmane.meduseld.io` to allowed hosts for SSH

### Bug Fixes

- **Restored Templates**: Recovered accidentally deleted `terminal.html` and `health.html` templates
- **Fixed Google Client Secret**: Removed hardcoded secret from config, now uses environment variable only
- **Fixed PKCE OAuth Flow**: Persist code_verifier across Google OAuth redirect for cloud backup
- **Fixed Public System Logs**: Added `/api/server-logs` endpoint that bypasses Cloudflare Access
- **Fixed journalctl Fallback**: Use journalctl when syslog file is unreadable
- **Removed Trivia Button**: Removed accidental trivia button from panel nav
- **Fixed Mobile Nav**: Improved header button layout and gap spacing on mobile
- **Fixed Dead Code**: Removed unused files and fixed dead code references

### UI/UX Improvements

- **SSH Commands Cheat Sheet**: Added detailed descriptions to all commands in the help modal
- **Improved Text Readability**: Better contrast in SSH commands modal
- **Bootstrap Icons Migration**: Replaced CoreUI icons with Bootstrap Icons throughout

### Configuration & Infrastructure

- **Removed Docker References**: Cleaned up deploy script and steering docs, removed Docker hostnames from nginx config
- **Removed Unused Nginx Config**: Cleaned up unused configuration files
- **Commitlint Enforcement**: Added commit message validation with git hooks
- **Steering Documentation**: Added page functionality reference and updated deployment docs with systemd details
- **Apple Touch Icon**: Updated icon styling for iOS glass theme

## [0.4.0-alpha] - 2026-03-13

### Bug Fixes

- **Fixed Panel Redirect Loop**: Resolved catch-all route causing panel.meduseld.io to redirect incorrectly on macOS browsers
- **Fixed System Logs API**: Updated `/api/server-logs` endpoint with proper error handling and permission checks
- **Fixed Log File Paths**: Changed to absolute paths for production environment (`/srv/meduseld/logs/webserver.log`)
- **Fixed Mobile Web App Meta Tag**: Replaced deprecated `apple-mobile-web-app-capable` with standard `mobile-web-app-capable` in base template

### Configuration Improvements

- **Absolute Log Paths**: Production logs now use `/srv/meduseld/logs/webserver.log` and `/var/log/syslog` for system logs
- **Log Directory Creation**: Automatically creates log directory if it doesn't exist on startup
- **Better Error Messages**: Enhanced error reporting for log file access issues

### Technical

- **CORS Support**: Improved cross-origin headers for system monitoring endpoints
- **Permission Handling**: Better detection and reporting of file permission issues
- **Route Organization**: Cleaned up catch-all route logic to prevent conflicts

## [0.3.0-alpha] - 2026-03-11

### Server Stability & Diagnostics

#### Enhanced Startup & Monitoring

- **Improved Start Script**: Complete rewrite with comprehensive error handling and diagnostics
- **Startup Log Persistence**: All server start/stop/crash events now persist in `/srv/games/icarus/startup.log`
- **Process Health Monitoring**: Automatic health checks every 5 minutes (CPU, RAM, threads)
- **Wine Error Logging**: Captures Wine errors while filtering out harmless warnings
- **Exit Code Detection**: Identifies crash types (SIGKILL, segfault, SIGTERM, clean shutdown)
- **Process Monitor**: Detects when server dies unexpectedly and logs the event
- **Stale Session Cleanup**: Automatically removes dead tmux sessions before starting

#### Startup Script Logs Panel

- New dedicated panel for startup/shutdown/crash history
- Color-coded separators matching control buttons (green=start, red=stop, purple=kill, dark red=crash)
- Shows Wine configuration, process health checks, and exit codes
- Clear logs button with archiving to `.old` file
- Real-time updates every 5 seconds

#### Bug Fixes

- **Fixed Wine Crash**: Resolved "Read access denied for device L:\\??\\Z:\\" error by setting `WINEDEBUG=-all`
- **Fixed systemd Killing Server**: Changed `KillMode=mixed` to `KillMode=process` to prevent webserver restarts from killing game server
- **Fixed Process Detection**: Enhanced `is_running()` to properly detect Wine-wrapped server process
- **Fixed Button Loading Delay**: Pass `server_state` to template for instant button state on page load

### UI/UX Improvements

#### Control Panel Enhancements

- **Player Count Display**: Shows current online players (X/8) via Steam Query Protocol
- **Download Backup Button**: Download save file (`Expedition 404.json`) with timestamp
- **Backup to Cloud Button**: Added (disabled/coming soon)
- **Button Layout**: Moved SSH Terminal and Download Backup to top right header
- **Responsive Header**: Added flex-wrap for better mobile button layout
- **Button Sizing**: Fixed control buttons to match server status panel height
- **Cursor Improvements**: Buttons now show pointer cursor on hover

#### Visual Updates

- **Graph Colors**: Server metrics in green, system metrics in yellow (both CPU and RAM graphs)
- **Update Badge**: Changed to blue background for "Update Available"
- **Up to Date Badge**: Changed to green background
- **Health Badge**: Color-coded text (Good=green, Warning=orange, Critical=red)
- **Log Separators**: Color-coded separators in game server logs for version changes, restarts, stops

#### SSH Terminal Page

- **Mobile Responsive**: Fixed button layout on mobile devices
- Buttons now properly align to top right on all screen sizes

### Technical Improvements

- Added Steam Query Protocol (A2S_INFO) implementation for player count
- Enhanced logging throughout startup process
- Better error messages and diagnostic information
- Improved process validation before reporting success
- Added socket and struct imports for network queries

## [0.2.0-alpha] - 2026-03-10

### Major Updates

#### Authentication & Security

- **Discord SSO Integration**: Replaced email OTP with Discord authentication via custom OIDC worker
- **Cloudflare Access**: Configured with Discord as identity provider
- **CORS Support**: Added proper CORS headers for cross-origin requests with credential support
- **Session Management**: Fixed cross-subdomain authentication issues

#### New Services

- **Service Page** (services.meduseld.io): Central hub for all services with status indicators
- **Health Monitoring** (health.meduseld.io): Dedicated health check system with Cloudflare Worker
- **Jellyfin Integration** (jellyfin.meduseld.io): Media streaming proxy through Flask app
- **User Profiles**: Discord-based user profile system with authentication state

#### Health & Monitoring

- Implemented health check worker to monitor all services
- Added `/health-check-b8f3a9c2` endpoint with Cloudflare Access bypass
- Created `/check/<service>` endpoints for service-specific health checks
- Real-time service status on service page (online/offline/tunnel down)
- Health check API at meduseld-health.404-41f.workers.dev

#### UI/UX Improvements

- Added SSH Terminal button to control panel
- Improved stat displays: CPU shown as cores used, RAM/disk shown as GB used/total
- Added detailed tooltips to all metrics and badges
- Visual log separators when server state changes
- Better cursor handling (pointer for buttons, text for logs, default elsewhere)
- Enhanced process detection to skip wrapper processes (tmux, wine, xvfb)

#### Bug Fixes

- Fixed panel.meduseld.io routing and 404 errors
- Fixed catch-all route to properly handle non-Jellyfin subdomains
- Resolved Cloudflare Access redirect loops
- Fixed server process detection for Wine-wrapped executables
- Improved disk usage calculation to sum all mounted partitions
- Fixed development mode detection and banner display

#### API & Endpoints

- Added `/me` endpoint for authentication status
- Added `/api/auth/profile` endpoint with CORS support
- Added OPTIONS handlers for preflight requests
- Improved error handling and logging

#### Configuration

- Added health.meduseld.io to allowed hosts
- Updated Cloudflare Tunnel config for all subdomains
- Configured Discord OIDC worker with environment variables

## [0.1.0-alpha] - 2026-03-09

### Alpha Release - Testing Phase

**Note**: This is an alpha release. All functionality needs to be verified before v1.0.0.

#### Infrastructure

- **Cloudflare Tunnel**: HTTPS, authentication, and routing
- **Cloudflare Access**: Email-based OTP authentication
- **ttyd**: Lightweight web terminal for SSH access
- **systemd**: Service management for Flask app and ttyd
- **Native Python**: Direct execution on Ubuntu Server

#### Features

- Web-based control panel at panel.meduseld.io
- Web-based SSH terminal at ssh.meduseld.io using ttyd
- Real-time server monitoring (CPU, RAM, disk, uptime)
- Historical metrics graphs (30-minute CPU/RAM charts)
- Game server control (start, stop, restart, force kill)
- Live log streaming from game server
- Update detection via Steam API
- Crash detection and automatic state management
- Activity logging for user actions
- Rate limiting on control endpoints
- Restart cooldown protection
- Thread health monitoring

#### Control Panel

- Server status with state machine (offline, starting, running, stopping, crashed)
- System metrics with color-coded health indicators
- Server-specific CPU and RAM usage
- Control buttons with state-aware enabling/disabling
- Live game server logs with auto-scroll
- Historical graphs using Chart.js
- Update availability notifications
- Uptime tracking

#### SSH Terminal

- Browser-based terminal access
- Login authentication (username/password)
- Full bash session with all commands
- Navigation buttons to return to service or panel
- Secure access through Cloudflare Tunnel

#### Security

- Cloudflare Access email-based authentication
- Rate limiting to prevent abuse
- Host validation for approved domains
- Restart cooldown to prevent spam
- Activity logging with IP tracking

#### Configuration

- Single config.py file for all settings
- Auto-detection of production vs development mode
- Environment-specific paths and settings
- Configurable monitoring thresholds
- Adjustable timeouts and intervals

#### API Endpoints

- POST /start - Start game server
- POST /stop - Stop game server
- POST /restart - Restart with update check
- POST /kill - Force kill server
- GET /api/stats - Server stats and metrics
- GET /api/logs - Game server logs
- GET /api/console - Console output
- GET /api/history - Historical metrics
- GET /api/check-update - Check for updates
- GET /api/activity - User activity log

#### Tech Stack

- Python 3.12 + Flask
- Bootstrap 5 + Chart.js
- ttyd (C-based terminal emulator)
- Ubuntu Server 24.04 LTS
- Cloudflare Tunnel (cloudflared)
- psutil for process monitoring
- Icarus Dedicated Server (via Wine)

#### Known Issues / To Verify

- [ ] Server start/stop/restart functionality
- [ ] Update detection and application
- [ ] Crash detection accuracy
- [ ] Historical metrics data collection
- [ ] SSH terminal stability
- [ ] Rate limiting effectiveness
- [ ] All API endpoints
- [ ] Cross-browser compatibility
- [ ] Mobile responsiveness
