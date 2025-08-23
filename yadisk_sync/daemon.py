"""
Daemon process for Yandex.Disk synchronization.
"""

import os
import time
import signal
import threading
from pathlib import Path
from typing import Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger
import daemon
import daemon.pidfile

from .config import Config
from .client import YadiskClient


class FileChangeHandler(FileSystemEventHandler):
    """Handle file system changes for real-time sync."""
    
    def __init__(self, sync_manager: 'SyncManager'):
        self.sync_manager = sync_manager
        self.debounce_timer = None
        self.debounce_delay = 5  # seconds
    
    def on_created(self, event):
        if not event.is_directory:
            self._schedule_sync()
    
    def on_modified(self, event):
        if not event.is_directory:
            self._schedule_sync()
    
    def on_deleted(self, event):
        if not event.is_directory:
            self._schedule_sync()
    
    def on_moved(self, event):
        if not event.is_directory:
            self._schedule_sync()
    
    def _schedule_sync(self):
        """Schedule a sync operation with debouncing."""
        if self.debounce_timer:
            self.debounce_timer.cancel()
        
        self.debounce_timer = threading.Timer(self.debounce_delay, self.sync_manager.sync_all)
        self.debounce_timer.start()


class SyncManager:
    """Manages synchronization operations."""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = YadiskClient(config.token, verbose_connection_test=False)
        self.observer = None
        self.running = False
    
    def sync_all(self) -> None:
        """Sync all configured directories."""
        self.client.sync_all_directories(self.config)
    
    def start_file_watching(self) -> None:
        """Start watching files for changes."""
        if not self.config.daemon.watch_files:
            return
        
        self.observer = Observer()
        
        for sync_dir in self.config.sync_directories:
            local_path = self.config.get_full_local_path(sync_dir.local_path)
            
            if os.path.exists(local_path):
                handler = FileChangeHandler(self)
                self.observer.schedule(handler, local_path, recursive=True)
                logger.info(f"Started watching: {local_path}")
            else:
                logger.warning(f"Directory does not exist, skipping watch: {local_path}")
        
        self.observer.start()
        logger.info("File watching started")
    
    def stop_file_watching(self) -> None:
        """Stop watching files for changes."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("File watching stopped")
    
    def run_periodic_sync(self) -> None:
        """Run periodic synchronization."""
        self.running = True
        
        while self.running:
            try:
                self.sync_all()
                time.sleep(self.config.daemon.sync_interval)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                break
            except Exception as e:
                logger.error(f"Error in periodic sync: {e}")
                time.sleep(60)  # Wait before retrying
    
    def stop(self) -> None:
        """Stop the sync manager."""
        self.running = False
        self.stop_file_watching()


class YadiskSyncDaemon:
    """Main daemon class."""
    
    def __init__(self, config: Config):
        self.config = config
        self.sync_manager = SyncManager(config)
        self.daemon_context = None
    
    def start(self) -> None:
        """Start the daemon process."""
        logger.info("Starting Yandex.Disk Sync Daemon")
        
        # Create PID file directory if it doesn't exist
        pid_dir = os.path.dirname(self.config.daemon.pid_file)
        if pid_dir and not os.path.exists(pid_dir):
            os.makedirs(pid_dir, exist_ok=True)
        
        # Create log file directory if it doesn't exist
        log_dir = os.path.dirname(self.config.daemon.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Configure daemon context
        self.daemon_context = daemon.DaemonContext(
            working_directory=self.config.local_root,
            umask=0o002,
            pidfile=daemon.pidfile.TimeoutPIDLockFile(self.config.daemon.pid_file),
            signal_map={
                signal.SIGTERM: self._signal_handler,
                signal.SIGINT: self._signal_handler,
            }
        )
        
        with self.daemon_context:
            self._run_daemon()
    
    def _run_daemon(self) -> None:
        """Run the daemon process."""
        try:
            # Configure logging for daemon
            logger.remove()
            logger.add(
                self.config.daemon.log_file,
                rotation="10 MB",
                retention="7 days",
                level="INFO"
            )
            
            logger.info("Yandex.Disk Sync Daemon started")
            
            # Start file watching
            self.sync_manager.start_file_watching()
            
            # Run periodic sync
            self.sync_manager.run_periodic_sync()
            
        except Exception as e:
            logger.error(f"Daemon error: {e}")
        finally:
            self.sync_manager.stop()
            logger.info("Yadisk Sync Daemon stopped")
    
    def _signal_handler(self, signo, frame) -> None:
        """Handle termination signals."""
        logger.info(f"Received signal {signo}")
        self.sync_manager.stop()
    
    def stop(self) -> None:
        """Stop the daemon process."""
        if self.daemon_context and self.daemon_context.pidfile:
            try:
                with open(self.config.daemon.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Sent SIGTERM to daemon process {pid}")
                
                # Wait for process to terminate
                time.sleep(5)
                
                # Force kill if still running
                try:
                    os.kill(pid, signal.SIGKILL)
                    logger.info(f"Force killed daemon process {pid}")
                except ProcessLookupError:
                    pass
                    
            except (FileNotFoundError, ValueError, ProcessLookupError) as e:
                logger.error(f"Error stopping daemon: {e}")
    
    def status(self) -> bool:
        """Check if daemon is running."""
        try:
            with open(self.config.daemon.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is running
            os.kill(pid, 0)
            return True
        except (FileNotFoundError, ValueError, ProcessLookupError):
            return False




