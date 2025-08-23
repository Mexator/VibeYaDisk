"""
CLI interface for Yandex.Disk Sync Daemon.
"""

import os
import sys
import yadisk
from pathlib import Path
import click
from loguru import logger

from .config import Config
from .daemon import YadiskSyncDaemon
from .client import YadiskClient


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    logger.remove()
    
    if verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")


@click.group()
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config, verbose):
    """Yandex.Disk Sync Daemon CLI tool."""
    setup_logging(verbose)
    
    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config


@cli.command()
@click.pass_context
def get_token(ctx):
    """Get Yandex.Disk OAuth token using application credentials."""
    try:
        config_path = ctx.obj['config_path']
        
        # Load existing config if it exists
        if os.path.exists(config_path):
            config = Config.load(config_path)
            if not config.app_id or not config.app_secret:
                logger.error("Application ID and secret not found in configuration.")
                logger.info("Please add your app_id and app_secret to the config file first.")
                sys.exit(1)
        else:
            logger.error(f"Configuration file not found: {config_path}")
            logger.info("Please run 'python main.py init' first to create a configuration file.")
            sys.exit(1)
        
        logger.info("Starting OAuth token generation...")
        
        
        client = yadisk.Client(config.app_id, config.app_secret)
        
        # Get authorization URL
        url = client.get_code_url()
        
        logger.info(f"Please visit the following URL to authorize the application:")
        logger.info(f"{url}")
        logger.info("")
        code = input("Enter the confirmation code: ")
        
        try:
            response = client.get_token(code)
        except yadisk.exceptions.BadRequestError:
            logger.error("Invalid confirmation code.")
            sys.exit(1)
        
        client.token = response.access_token
        
        if client.check_token():
            logger.info("Successfully received token!")
            token = response.access_token
        else:
            logger.error("Something went wrong with token validation.")
            sys.exit(1)
        
        if token:
            # Update the configuration with the new token
            config.token = token
            config.save(config_path)
            logger.info(f"Token saved to configuration file: {config_path}")
        else:
            logger.error("Failed to obtain token.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to get token: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def start(ctx):
    """Start the Yandex.Disk sync daemon."""
    try:
        config_path = ctx.obj['config_path']
        config = Config.load(config_path)
        config.validate()
        
        daemon = YadiskSyncDaemon(config)
        daemon.start()
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start daemon: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def stop(ctx):
    """Stop the Yandex.Disk sync daemon."""
    try:
        config_path = ctx.obj['config_path']
        config = Config.load(config_path)
        
        daemon = YadiskSyncDaemon(config)
        daemon.stop()
        
        logger.info("Daemon stopped successfully")
        
    except Exception as e:
        logger.error(f"Failed to stop daemon: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Check the status of the Yandex.Disk sync daemon."""
    try:
        config_path = ctx.obj['config_path']
        config = Config.load(config_path)
        
        daemon = YadiskSyncDaemon(config)
        
        if daemon.status():
            logger.info("Daemon is running")
            # Try to get PID
            try:
                with open(config.daemon.pid_file, 'r') as f:
                    pid = f.read().strip()
                    logger.info(f"Daemon PID: {pid}")
            except:
                pass
        else:
            logger.info("Daemon is not running")
            
    except Exception as e:
        logger.error(f"Failed to check daemon status: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def restart(ctx):
    """Restart the Yandex.Disk sync daemon."""
    try:
        config_path = ctx.obj['config_path']
        config = Config.load(config_path)
        
        daemon = YadiskSyncDaemon(config)
        
        # Stop if running
        if daemon.status():
            logger.info("Stopping daemon...")
            daemon.stop()
        
        # Start daemon
        logger.info("Starting daemon...")
        daemon.start()
        
    except Exception as e:
        logger.error(f"Failed to restart daemon: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def sync(ctx):
    """Perform a one-time sync operation."""
    try:
        config_path = ctx.obj['config_path']
        config = Config.load(config_path)
        config.validate()
        
        logger.info("Starting one-time sync operation")
        
        client = YadiskClient(config.token, verbose_connection_test=False)
        
        for sync_dir in config.sync_directories:
            try:
                local_path = config.get_full_local_path(sync_dir.local_path)
                remote_path = config.get_full_yadisk_path(sync_dir.yadisk_path)
                
                logger.info(f"Syncing: {local_path} <-> {remote_path}")
                success = client.sync_directory(
                    local_path, 
                    remote_path, 
                    sync_dir.sync_mode
                )
                
                if success:
                    logger.info(f"Successfully synced: {sync_dir.local_path}")
                else:
                    logger.error(f"Failed to sync: {sync_dir.local_path}")
                    
            except Exception as e:
                logger.error(f"Error syncing {sync_dir.local_path}: {e}")
        
        logger.info("One-time sync operation completed")
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to perform sync: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def test(ctx):
    """Test the Yandex.Disk connection and configuration."""
    try:
        config_path = ctx.obj['config_path']
        config = Config.load(config_path)
        config.validate()
        
        logger.info("Testing Yandex.Disk connection...")
        
        client = YadiskClient(config.token, verbose_connection_test=True)
        
        # Connection test already logged disk info in verbose mode
        
        # Test root directory
        root_path = config.yadisk_root
        if client.path_exists(root_path):
            logger.info(f"Root directory exists: {root_path}")
        else:
            logger.info(f"Root directory does not exist, will be created: {root_path}")
        
        # Test sync directories
        for sync_dir in config.sync_directories:
            local_path = config.get_full_local_path(sync_dir.local_path)
            remote_path = config.get_full_yadisk_path(sync_dir.yadisk_path)
            
            logger.info(f"Sync directory: {sync_dir.local_path}")
            logger.info(f"  Local path: {local_path}")
            logger.info(f"  Remote path: {remote_path}")
            logger.info(f"  Sync mode: {sync_dir.sync_mode}")
            
            if os.path.exists(local_path):
                logger.info(f"  Local directory exists")
            else:
                logger.warning(f"  Local directory does not exist")
        
        logger.info("Configuration test completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def logs(ctx):
    """Show daemon logs."""
    try:
        config_path = ctx.obj['config_path']
        config = Config.load(config_path)
        
        log_file = config.daemon.log_file
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                click.echo(f.read())
        else:
            logger.warning(f"Log file does not exist: {log_file}")
            
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize a new configuration file."""
    config_path = ctx.obj['config_path']
    
    if os.path.exists(config_path):
        if not click.confirm(f"Configuration file {config_path} already exists. Overwrite?"):
            return
    
    # Create sample config
    sample_config = """# Yandex.Disk Sync Daemon Configuration

# Yandex.Disk OAuth token
# Get this from: https://yandex.ru/dev/disk/rest/
# Or run: python main.py get-token
token: "your_yandex_disk_token_here"

# Application credentials for OAuth token generation
# Get these from: https://yandex.ru/dev/disk/rest/
app_id: "your_application_id_here"
app_secret: "your_application_secret_here"

# Root folder on Yandex.Disk where files will be synced
yadisk_root: "/myYaDisk"

# Local root directory
local_root: "/home/anton/myYaDisk"

# Sync directories configuration
sync_directories:
  - local_path: "documents"
    yadisk_path: "documents"
    sync_mode: "bidirectional"
    
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
  sync_interval: 300
"""
    
    try:
        with open(config_path, 'w') as f:
            f.write(sample_config)
        
        logger.info(f"Configuration file created: {config_path}")
        logger.info("Please edit the configuration file and set your:")
        logger.info("1. app_id and app_secret (for token generation)")
        logger.info("2. Or set your Yandex.Disk token directly")
        logger.info("3. Configure your sync directories")
        
    except Exception as e:
        logger.error(f"Failed to create configuration file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()
