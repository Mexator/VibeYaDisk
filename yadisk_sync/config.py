"""
Configuration management for Yandex.Disk Sync Daemon.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class SyncDirectory:
    """Represents a directory to be synced."""
    local_path: str
    yadisk_path: str
    sync_mode: str  # upload, download, bidirectional


@dataclass
class DaemonConfig:
    """Daemon-specific configuration."""
    pid_file: str
    log_file: str
    sync_interval: int


@dataclass
class Config:
    """Main configuration class."""
    token: str
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    yadisk_root: str = "/myYaDisk"
    local_root: str = "/home/anton/myYaDisk"
    sync_directories: List[SyncDirectory] = None
    daemon: DaemonConfig = None

    @classmethod
    def load(cls, config_path: str) -> 'Config':
        """Load configuration from YAML file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return cls._from_dict(data)
    
    @classmethod
    def _from_dict(cls, data: Dict) -> 'Config':
        """Create Config instance from dictionary."""
        # Validate required fields
        required_fields = ['token', 'sync_directories', 'daemon']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Parse sync directories
        sync_dirs = []
        for sync_data in data['sync_directories']:
            sync_dirs.append(SyncDirectory(
                local_path=sync_data['local_path'],
                yadisk_path=sync_data['yadisk_path'],
                sync_mode=sync_data.get('sync_mode', 'bidirectional')
            ))
        
        # Parse daemon config
        daemon_data = data['daemon']
        daemon_config = DaemonConfig(
            pid_file=daemon_data.get('pid_file', '/tmp/yadisk_sync_daemon.pid'),
            log_file=daemon_data.get('log_file', '/tmp/yadisk_sync_daemon.log'),
            sync_interval=daemon_data.get('sync_interval', 300)
        )
        
        return cls(
            token=data['token'],
            app_id=data.get('app_id'),
            app_secret=data.get('app_secret'),
            yadisk_root=data.get('yadisk_root', '/myYaDisk'),
            local_root=data.get('local_root', os.getcwd()),
            sync_directories=sync_dirs,
            daemon=daemon_config
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.token or self.token == "your_yandex_disk_token_here":
            raise ValueError("Please set a valid Yandex.Disk token in the configuration")
        
        if not self.yadisk_root:
            raise ValueError("Yandex.Disk root path cannot be empty")
        
        if not self.sync_directories:
            raise ValueError("At least one sync directory must be configured")
        
        # Validate sync directories
        for sync_dir in self.sync_directories:
            if sync_dir.sync_mode not in ['upload', 'download', 'bidirectional']:
                raise ValueError(f"Invalid sync mode: {sync_dir.sync_mode}")
        
        # Validate daemon config
        if self.daemon.sync_interval < 60:
            logger.warning("Sync interval is very short (< 60 seconds)")
    
    def get_full_local_path(self, relative_path: str) -> str:
        """Get full local path for a relative path."""
        return os.path.join(self.local_root, relative_path)
    
    def get_full_yadisk_path(self, relative_path: str) -> str:
        """Get full Yandex.Disk path for a relative path."""
        return os.path.join(self.yadisk_root, relative_path).replace('\\', '/')
    
    def save(self, config_path: str) -> None:
        """Save configuration to YAML file."""
        config_data = {
            'token': self.token,
            'app_id': self.app_id,
            'app_secret': self.app_secret,
            'yadisk_root': self.yadisk_root,
            'local_root': self.local_root,
            'sync_directories': [
                {
                    'local_path': sync_dir.local_path,
                    'yadisk_path': sync_dir.yadisk_path,
                    'sync_mode': sync_dir.sync_mode
                }
                for sync_dir in self.sync_directories
            ],
            'daemon': {
                'pid_file': self.daemon.pid_file,
                'log_file': self.daemon.log_file,
                'sync_interval': self.daemon.sync_interval
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
