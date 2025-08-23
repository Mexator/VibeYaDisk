# Yandex.Disk Sync Daemon

Стандартная утилита от Яндекса не даёт синковать только конкретные папки. Ну я и навайбкодил обёртку вокруг [yadisk](https://github.com/ivknv/yadisk).

---

A Python CLI application that syncs directories with Yandex.Disk as a daemon process. This tool provides automatic synchronization between local directories and Yandex.Disk with support for different sync modes, file watching, and periodic sync operations.

## Features

- **Multiple Sync Modes**: Upload, download, or bidirectional synchronization
- **Daemon Process**: Runs as a background service with automatic restart capabilities
- **File Watching**: Real-time synchronization when files change
- **Periodic Sync**: Configurable interval-based synchronization
- **Configurable**: YAML-based configuration with flexible directory mapping
- **CLI Interface**: Easy-to-use command-line interface for management
- **Logging**: Comprehensive logging with rotation and retention
- **Error Handling**: Robust error handling and recovery mechanisms
- **Latest API**: Uses Yandex.Disk API v3.4.0 with modern Python features
- **OAuth Token Generation**: Built-in command to obtain OAuth tokens

## Installation

### Prerequisites

- Python 3.7 or higher
- Yandex.Disk application credentials (app_id and app_secret)

### Setup

1. **Clone or download the project**:

   ```bash
   cd /home/anton/myYaDisk
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   Or install with the latest yadisk library:

   ```bash
   pip install "yadisk[sync-defaults]>=3.4.0"
   pip install click pyyaml watchdog python-daemon psutil loguru
   ```

3. **Get your Yandex.Disk application credentials**:
   - Go to [Yandex.Disk REST API](https://yandex.ru/dev/disk/rest/)
   - Create an application and get your app_id and app_secret
   - These will be used to generate OAuth tokens

4. **Set up configuration**:

   ```bash
   cp config.yaml.example config.yaml
   nano config.yaml
   ```

5. **Configure your settings**:
   - Set your `app_id` and `app_secret` for OAuth token generation
   - Or set your `token` directly if you already have one
   - Configure your sync directories and preferences

6. **Generate OAuth token**:

   ```bash
   python main.py get-token
   ```

This will write token to config

## Configuration

The application uses a YAML configuration file (`config.yaml`) for all settings. A sample configuration file (`config.yaml.example`) is provided with examples and comments.


## Usage

### Basic Commands

You can run commands using any of these methods:

```bash
# Method 1: Using the installed command (after pip install -e .)
yadisk-sync get-token
yadisk-sync start
yadisk-sync stop

# Method 2: Using Python module syntax
python -m yadisk_sync get-token
python -m yadisk_sync start
python -m yadisk_sync stop

# Method 3: Using the launcher script
./yadisk-sync get-token
./yadisk-sync start
./yadisk-sync stop

# Method 4: From the project directory
python main.py get-token
python main.py start
python main.py stop
```

#### Available Commands

```bash
# Get OAuth token using application credentials
yadisk-sync get-token

# Test the configuration and connection
yadisk-sync test

# Start the daemon
yadisk-sync start

# Stop the daemon
yadisk-sync stop

# Check daemon status
yadisk-sync status

# Perform a one-time sync
yadisk-sync sync

# View daemon logs
yadisk-sync logs
```

## File Structure

```ls
myYaDisk/
├── main.py                 # Main entry point
├── config.yaml            # Configuration file (create from example)
├── config.yaml.example    # Sample configuration
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── yadisk_sync/          # Main package
    ├── __init__.py
    ├── config.py         # Configuration management
    ├── client.py         # Yandex.Disk client wrapper
    ├── daemon.py         # Daemon process management
    └── cli.py           # CLI interface
```

## How It Works

1. **Configuration Loading**: The application loads settings from `config.yaml`
2. **Token Management**: OAuth tokens can be generated automatically or set manually
3. **Connection Test**: Validates the Yandex.Disk token and connection
4. **File Watching**: Monitors configured directories for changes (if enabled)
5. **Periodic Sync**: Runs sync operations at configured intervals
6. **Sync Operations**:
   - Upload: Copies local files to Yandex.Disk
   - Download: Copies Yandex.Disk files to local
   - Bidirectional: Syncs in both directions

## Logging

The daemon logs to the configured log file with rotation:

- Log files are rotated when they reach 10 MB
- Logs are retained for 7 days
- Log level can be adjusted with the `--verbose` flag

## Error Handling

The application includes robust error handling:

- Automatic retry on network errors
- Graceful handling of missing directories
- Process recovery on crashes
- Detailed error logging

## Security Considerations

- Store your application credentials securely
- Use appropriate file permissions for configuration files
- Consider using environment variables for sensitive data
- Regularly rotate your OAuth tokens
- Never commit tokens or secrets to version control
