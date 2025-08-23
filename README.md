# Yandex.Disk Sync Daemon

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

4. **Initialize configuration**:
   ```bash
   python main.py init
   ```

5. **Edit the configuration file** (`config.yaml`):
   - Set your `app_id` and `app_secret`
   - Configure your sync directories
   - Adjust daemon settings as needed

6. **Generate OAuth token**:
   ```bash
   python main.py get-token
   ```

## Configuration

The application uses a YAML configuration file (`config.yaml`) with the following structure:

```yaml
# Yandex.Disk OAuth token (auto-generated or manual)
token: "your_yandex_disk_token_here"

# Application credentials for OAuth token generation
app_id: "your_application_id_here"
app_secret: "your_application_secret_here"

# Root folder on Yandex.Disk
yadisk_root: "/myYaDisk"

# Local root directory
local_root: "/home/anton/myYaDisk"

# Sync directories configuration
sync_directories:
  - local_path: "documents"
    yadisk_path: "documents"
    sync_mode: "bidirectional"  # upload, download, bidirectional
    
  - local_path: "photos"
    yadisk_path: "photos"
    sync_mode: "upload"
    
  - local_path: "backups"
    yadisk_path: "backups"
    sync_mode: "download"

# Daemon settings
daemon:
  pid_file: "/tmp/yadisk_sync_daemon.pid"
  log_file: "/tmp/yadisk_sync_daemon.log"
  sync_interval: 300  # 5 minutes
  watch_files: true
  ignore_patterns:
    - "*.tmp"
    - "*.log"
    - ".DS_Store"
    - "__pycache__"
    - ".git"
    - ".venv"
```

### Configuration Options

#### OAuth Token Generation

- **`app_id`**: Your Yandex application ID
- **`app_secret`**: Your Yandex application secret
- **`token`**: OAuth token (can be generated automatically)

#### Sync Modes

- **`upload`**: Only upload local files to Yandex.Disk
- **`download`**: Only download files from Yandex.Disk to local
- **`bidirectional`**: Sync in both directions (simplified implementation)

#### Daemon Settings

- **`sync_interval`**: Time between periodic sync operations (in seconds)
- **`watch_files`**: Enable real-time file watching
- **`ignore_patterns`**: Files and directories to ignore during sync

## Usage

### Basic Commands

```bash
# Initialize a new configuration file
python main.py init

# Get OAuth token using application credentials
python main.py get-token

# Test the configuration and connection
python main.py test

# Start the daemon
python main.py start

# Stop the daemon
python main.py stop

# Check daemon status
python main.py status

# Restart the daemon
python main.py restart

# Perform a one-time sync
python main.py sync

# View daemon logs
python main.py logs
```

### Advanced Usage

```bash
# Use a custom configuration file
python main.py --config /path/to/config.yaml start

# Enable verbose logging
python main.py --verbose test

# Combine options
python main.py --config custom_config.yaml --verbose start
```

### Examples

1. **Initial Setup with OAuth**:
   ```bash
   # Initialize configuration
   python main.py init
   
   # Edit config.yaml with your app_id and app_secret
   nano config.yaml
   
   # Generate OAuth token
   python main.py get-token
   
   # Test the configuration
   python main.py test
   
   # Start the daemon
   python main.py start
   ```

2. **Manual Token Setup**:
   ```bash
   # Initialize configuration
   python main.py init
   
   # Edit config.yaml with your token directly
   nano config.yaml
   
   # Test the configuration
   python main.py test
   
   # Start the daemon
   python main.py start
   ```

3. **Monitor Sync Status**:
   ```bash
   # Check if daemon is running
   python main.py status
   
   # View recent logs
   python main.py logs
   
   # Perform manual sync
   python main.py sync
   ```

4. **Troubleshooting**:
   ```bash
   # Test connection with verbose output
   python main.py --verbose test
   
   # Check daemon logs
   python main.py logs
   
   # Restart daemon
   python main.py restart
   ```

## OAuth Token Generation

The application includes a built-in command to generate OAuth tokens:

```bash
python main.py get-token
```

This command will:
1. Load your `app_id` and `app_secret` from the configuration
2. Open a browser URL for authorization
3. Prompt you to enter the confirmation code
4. Generate and save the OAuth token to your configuration file

### Token Generation Process

1. **Prepare your credentials**: Add `app_id` and `app_secret` to `config.yaml`
2. **Run the command**: `python main.py get-token`
3. **Authorize**: Visit the provided URL and authorize your application
4. **Enter code**: Copy the confirmation code and enter it when prompted
5. **Token saved**: The token is automatically saved to your configuration

## File Structure

```
myYaDisk/
├── main.py                 # Main entry point
├── config.yaml            # Configuration file
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

## Troubleshooting

### Common Issues

1. **"Configuration file not found"**:
   - Run `python main.py init` to create a configuration file

2. **"Application ID and secret not found"**:
   - Add your `app_id` and `app_secret` to the configuration file
   - Or set your token directly in the `token` field

3. **"Invalid token"**:
   - Run `python main.py get-token` to generate a new token
   - Or verify your manual token is correct

4. **"Permission denied"**:
   - Check file permissions for local directories
   - Ensure the daemon has write access to log and PID files

5. **"Daemon not starting"**:
   - Check if another instance is already running
   - Verify the PID file location is writable
   - Check the log file for detailed error messages

6. **"Module not found"**:
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - For yadisk specifically: `pip install "yadisk[sync-defaults]>=3.4.0"`

### Getting Help

1. Run `python main.py --verbose test` for detailed connection information
2. Check the daemon logs with `python main.py logs`
3. Verify your configuration file syntax
4. Ensure all required directories exist and are accessible

## Development

### Running in Development Mode

```bash
# Install in development mode
pip install -e .

# Run with debug logging
python main.py --verbose test
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source. Please check the license file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error details
3. Verify your configuration
4. Create an issue with detailed information
