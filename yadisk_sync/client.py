"""
Yandex.Disk client wrapper for file operations.
"""

import os
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import yadisk
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed


class YadiskClient:
    """Wrapper for Yandex.Disk API client."""
    
    def __init__(self, token: str, verbose_connection_test: bool = False):
        """Initialize Yandex.Disk client."""
        self.client = yadisk.YaDisk(token=token)
        self._test_connection(verbose=verbose_connection_test)
        self.executor = ThreadPoolExecutor(max_workers=32)
    
    def _test_connection(self, verbose: bool = False) -> None:
        """Test connection to Yandex.Disk."""
        try:
            # Check if token is valid
            disk_info = self.client.get_disk_info()
            if verbose:
                logger.info("Successfully connected to Yandex.Disk")
                logger.info(f"Total space: {disk_info.total_space / (1024**3):.2f} GB")
                logger.info(f"Used space: {disk_info.used_space / (1024**3):.2f} GB")
        except Exception as e:
            logger.error(f"Failed to connect to Yandex.Disk: {e}")
            raise
    
    def list_files(self, path: str) -> List[Dict]:
        """List files in a directory on Yandex.Disk."""
        try:
            files = []
            for item in self.client.listdir(self._normalize_api_path(path)):
                files.append({
                    'name': item.name,
                    'path': item.path,
                    'type': item.type,
                    'size': item.size,
                    'modified': item.modified,
                    'md5': item.md5
                })
            return files
        except Exception as e:
            logger.error(f"Failed to list files in {path}: {e}")
            return []
    
    def upload_file(self, local_path: str, remote_path: str, overwrite: bool = True) -> bool:
        """Upload a file to Yandex.Disk."""
        try:
            if not os.path.exists(local_path):
                logger.error(f"Local file does not exist: {local_path}")
                return False
            
            # Create remote directory if it doesn't exist
            remote_dir = os.path.dirname(remote_path)
            if remote_dir and not self.path_exists(remote_dir):
                self.create_directory(remote_dir)
            
            self.client.upload(local_path, self._normalize_api_path(remote_path), overwrite=overwrite)
            logger.info(f"Uploaded: {local_path} -> {remote_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str, overwrite: bool = True) -> bool:
        """Download a file from Yandex.Disk."""
        try:
            # Create local directory if it doesn't exist
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir, exist_ok=True)
            
            self.client.download(self._normalize_api_path(remote_path), local_path)
            logger.info(f"Downloaded: {remote_path} -> {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download {remote_path}: {e}")
            return False
    
    def trash_file(self, path: str) -> bool:
        """Move a file or directory to trash on Yandex.Disk."""
        try:
            self.client.remove(self._normalize_api_path(path), permanently=False)
            logger.info(f"Moved to trash: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to move to trash {path}: {e}")
            return False
    
    def create_directory(self, path: str) -> bool:
        """Create a directory on Yandex.Disk."""
        try:
            self.client.mkdir(self._normalize_api_path(path))
            logger.info(f"Created directory: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False
    
    def path_exists(self, path: str) -> bool:
        """Check if a path exists on Yandex.Disk."""
        try:
            self.client.get_meta(self._normalize_api_path(path))
            return True
        except Exception:
            return False
    
    def get_file_hash(self, local_path: str) -> str:
        """Calculate MD5 hash of a local file."""
        hash_md5 = hashlib.md5()
        try:
            with open(local_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {local_path}: {e}")
            return ""
    
    def _normalize_api_path(self, path: str) -> str:
        """Normalize path for API calls by removing disk: prefix if present."""
        if path.startswith('disk:'):
            return path[5:]
        return path
    
    def _get_metadata_dir(self) -> str:
        """Get the metadata directory path for a given local directory."""
        metadata_dir = os.path.join(Path.home(), ".yadisk-sync", "metadata")
        os.makedirs(metadata_dir, exist_ok=True)
        return metadata_dir
    
    def _get_sync_state_file(self, local_dir: str) -> str:
        """Get the path to the sync state file for a directory."""
        # Create a metadata directory outside of the synced directory
        metadata_dir = self._get_metadata_dir()

        # Use a hash of the directory path to create a unique filename
        dir_hash = hashlib.md5(local_dir.encode()).hexdigest()
        return os.path.join(metadata_dir, f"sync_state_{dir_hash}.json")
    
    def _load_sync_state(self, local_dir: str) -> Dict:
        """Load the previous sync state for a directory."""
        state_file = self._get_sync_state_file(local_dir)
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load sync state from {state_file}: {e}")
        return {}
    
    def _save_sync_state(self, local_dir: str, state: Dict) -> None:
        """Save the current sync state for a directory."""
        state_file = self._get_sync_state_file(local_dir)
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save sync state to {state_file}: {e}")

    def sync_all_directories(self, config) -> bool:
        """Sync all configured directories."""
        logger.info("Starting full sync operation")
        success = True
        
        for sync_dir in config.sync_directories:
            try:
                local_path = config.get_full_local_path(sync_dir.local_path)
                remote_path = config.get_full_yadisk_path(sync_dir.yadisk_path)
                
                logger.info(f"Syncing: {local_path} <-> {remote_path}")
                sync_success = self.sync_directory(
                    local_path, 
                    remote_path, 
                    sync_dir.sync_mode
                )
                
                if sync_success:
                    logger.info(f"Successfully synced: {sync_dir.local_path}")
                else:
                    logger.error(f"Failed to sync: {sync_dir.local_path}")
                    success = False
                    
            except Exception as e:
                logger.error(f"Error syncing {sync_dir.local_path}: {e}")
                success = False
        
        return success

    def sync_directory(self, local_dir: str, remote_dir: str, sync_mode: str = "bidirectional") -> bool:
        """Sync a directory between local and remote."""
        logger.info(f"Syncing directory: {local_dir} <-> {remote_dir} (mode: {sync_mode})")
        
        if sync_mode == "upload":
            return self._sync_upload(local_dir, remote_dir)
        elif sync_mode == "download":
            return self._sync_download(local_dir, remote_dir)
        else:  # bidirectional
            return self._sync_bidirectional(local_dir, remote_dir)
    
    def _sync_upload(self, local_dir: str, remote_dir: str) -> bool:
        """Upload local directory to Yandex.Disk."""
        if not os.path.exists(local_dir):
            logger.error(f"Local directory does not exist: {local_dir}")
            return False
        
        success = True
        for root, dirs, files in os.walk(local_dir):
            # Create remote directories
            for dir_name in dirs:
                local_path = os.path.join(root, dir_name)
                remote_path = os.path.join(remote_dir, os.path.relpath(local_path, local_dir))
                remote_path = remote_path.replace('\\', '/')
                
                if not self.path_exists(remote_path):
                    if not self.create_directory(remote_path):
                        success = False
            
            # Upload files
            for file_name in files:
                local_path = os.path.join(root, file_name)
                remote_path = os.path.join(remote_dir, os.path.relpath(local_path, local_dir))
                remote_path = remote_path.replace('\\', '/')
                
                if not self.upload_file(local_path, remote_path):
                    success = False
        
        return success
    
    def _sync_download(self, local_dir: str, remote_dir: str) -> bool:
        """Download remote directory to local."""
        if not self.path_exists(remote_dir):
            logger.error(f"Remote directory does not exist: {remote_dir}")
            return False
        
        success = True
        remote_files = self.list_files(remote_dir)
        
        for file_info in remote_files:
            if file_info['type'] == 'dir':
                # Create local directory
                local_path = os.path.join(local_dir, file_info['name'])
                if not os.path.exists(local_path):
                    os.makedirs(local_path, exist_ok=True)
                
                # Recursively sync subdirectory
                remote_subdir = os.path.join(remote_dir, file_info['name'])
                if not self._sync_download(local_path, remote_subdir):
                    success = False
            else:
                # Download file
                local_path = os.path.join(local_dir, file_info['name'])
                remote_path = file_info['path']  # Use original path with disk: prefix for API calls
                
                if not self.download_file(remote_path, local_path):
                    success = False
        
        return success
    
    def _sync_bidirectional(self, local_dir: str, remote_dir: str) -> bool:
        """Bidirectional sync between local and remote directories."""
        logger.info(f"Starting bidirectional sync: {local_dir} <-> {remote_dir}")
        
        # Load previous sync state
        previous_state = self._load_sync_state(local_dir)
        
        # Ensure both directories exist
        if not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)
            logger.info(f"Created local directory: {local_dir}")
        
        if not self.path_exists(remote_dir):
            self.create_directory(remote_dir)
            logger.info(f"Created remote directory: {remote_dir}")
        
        success = True
        
        # Get local files
        local_files = {}
        try:
            for file_name in os.listdir(local_dir):
                local_path = os.path.join(local_dir, file_name)
                if os.path.isfile(local_path):
                    rel_path = file_name
                    remote_path = os.path.join(remote_dir, rel_path).replace('\\', '/')
                    try:
                        stat = os.stat(local_path)
                        local_files[rel_path] = {
                            'path': local_path,
                            'remote_path': remote_path,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime),
                            'hash': self.get_file_hash(local_path)
                        }
                    except Exception as e:
                        logger.error(f"Failed to get local file info for {local_path}: {e}")
                        success = False
        except Exception as e:
            logger.error(f"Failed to list files in {local_dir}: {e}")
            success = False
        # Get remote files
        remote_files = {}
        try:
            remote_items = self.list_files(remote_dir)
            for item in remote_items:
                if item['type'] == 'file':
                    # Handle disk: prefix in remote paths
                    remote_path = item['path']
                    if remote_path.startswith('disk:'):
                        remote_path = remote_path[5:]  # Remove 'disk:' prefix
                    
                    # Extract the filename from the remote path
                    remote_filename = os.path.basename(remote_path)
                    # For files directly in the remote directory, use just the filename
                    if remote_path == f"{remote_dir}/{remote_filename}":
                        rel_path = remote_filename
                    else:
                        # For files in subdirectories, calculate relative path properly
                        rel_path = remote_path.replace(remote_dir + '/', '')
                    
                    local_path = os.path.join(local_dir, rel_path)
                    
                    remote_files[rel_path] = {
                        'path': local_path,
                        'remote_path': item['path'],  # Keep original path for API calls
                        'size': item['size'],
                        'modified': item['modified'],
                        'hash': item['md5']
                    }
        except Exception as e:
            logger.error(f"Failed to get remote files: {e}")
            success = False
        
        # Compare and sync files
        all_files = set(local_files.keys()) | set(remote_files.keys())
        for rel_path in all_files:
            local_file = local_files.get(rel_path)
            remote_file = remote_files.get(rel_path)
            if not self._sync_file(rel_path, local_file, remote_file, previous_state):
                success = False
        
        # Handle directories recursively
        local_dirs, remote_dirs = self._load_dirs(local_dir, remote_dir)

        all_dirs = local_dirs | remote_dirs
        futures = []
        for rel_dir in all_dirs:
            futures.append(self.executor.submit(self._sync_directory_entry, rel_dir, local_dir, remote_dir, previous_state))
        for future in as_completed(futures):
            if not future.result():
                success = False

        # reload dirs after possible deletion
        local_dirs, remote_dirs = self._load_dirs(local_dir, remote_dir)
        
        # Sync subdirectories
        all_dirs = local_dirs | remote_dirs
        futures = []
        for rel_dir in all_dirs:
            local_subdir = os.path.join(local_dir, rel_dir)
            remote_subdir = os.path.join(remote_dir, rel_dir).replace('\\', '/')
            futures.append(self.executor.submit(self._sync_bidirectional, local_subdir, remote_subdir))
        for future in as_completed(futures):
            if not future.result():
                success = False
        
        # Save current state for next sync
        current_state = {}
        for rel_path, info in local_files.items():
            current_state[rel_path] = {**info, "type": "file"}
        for rel_dir in local_dirs:
            if rel_dir not in current_state:
                current_state[rel_dir] = {"type": "dir"}
        self._save_sync_state(local_dir, current_state)
        
        if success:
            logger.info(f"Bidirectional sync completed successfully: {local_dir} <-> {remote_dir}")
        else:
            logger.error(f"Bidirectional sync completed with errors: {local_dir} <-> {remote_dir}")
        
        return success

    def _load_dirs(self, local_dir, remote_dir):
        local_dirs = set()
        remote_dirs = set()

        # Walk local directories
        for root, dirs, files in os.walk(local_dir):
            for d in dirs:
                dir_path = os.path.relpath(os.path.join(root, d), local_dir)
                local_dirs.add(dir_path)

        # List remote directories
        try:
            items = self.client.listdir(remote_dir)
            for item in items:
                if item['type'] == 'dir':
                    remote_path = item['path']
                    if remote_path.startswith('disk:'):
                        remote_path = remote_path[5:]
                    remote_dirname = os.path.basename(remote_path)
                    if remote_path == f"{remote_dir}/{remote_dirname}":
                        rel_path = remote_dirname
                    else:
                        rel_path = remote_path.replace(remote_dir + '/', '')
                    remote_dirs.add(rel_path)
        except Exception as e:
            logger.error(f"Failed to list remote directories: {e}")

        return (local_dirs, remote_dirs)

    def _sync_file(self, rel_path, local_file, remote_file, previous_state):
        """Sync a single file between local and remote."""
        success = True
        if local_file and remote_file:
            # File exists on both sides - compare hashes and timestamps
            if local_file['hash'] == remote_file['hash']:
                logger.debug(f"Files identical: {rel_path}")
                return True
            # Files are different, compare timestamps
            local_time = local_file['modified']
            if local_time.tzinfo is not None:
                local_time = local_time.replace(tzinfo=None)
            remote_time = remote_file['modified']
            if isinstance(remote_time, str):
                try:
                    remote_time = datetime.fromisoformat(remote_time.replace('Z', '+00:00'))
                    remote_time = remote_time.replace(tzinfo=None)
                except ValueError:
                    remote_time = datetime.fromtimestamp(0)
            elif isinstance(remote_time, datetime):
                if remote_time.tzinfo is not None:
                    remote_time = remote_time.replace(tzinfo=None)
            else:
                remote_time = datetime.fromtimestamp(0)
            if local_time > remote_time:
                logger.info(f"Uploading newer local file: {rel_path}")
                if not self.upload_file(local_file['path'], local_file['remote_path']):
                    success = False
            elif remote_time > local_time:
                logger.info(f"Downloading newer remote file: {rel_path}")
                if not self.download_file(remote_file['remote_path'], remote_file['path']):
                    success = False
            else:
                logger.warning(f"Conflict detected for {rel_path} - same timestamp but different content")
                logger.info(f"Resolving conflict by uploading local file: {rel_path}")
                if not self.upload_file(local_file['path'], local_file['remote_path']):
                    success = False
        elif local_file:
            if rel_path in previous_state:
                logger.info(f"Remote file was deleted, removing local file: {rel_path}")
                try:
                    os.remove(local_file['path'])
                except Exception as e:
                    logger.error(f"Failed to remove local file {local_file['path']}: {e}")
                    success = False
            else:
                logger.info(f"Uploading new local file: {rel_path}")
                if not self.upload_file(local_file['path'], local_file['remote_path']):
                    success = False
        elif remote_file:
            if rel_path in previous_state:
                logger.info(f"Local file was deleted, moving remote file to trash: {rel_path}")
                if not self.trash_file(remote_file['remote_path']):
                    success = False
            else:
                logger.info(f"Downloading new remote file: {rel_path}")
                if not self.download_file(remote_file['remote_path'], remote_file['path']):
                    success = False
        return success

    def _sync_directory_entry(self, rel_dir, local_dir, remote_dir, previous_state):
        success = True
        local_subdir = os.path.join(local_dir, rel_dir)
        remote_subdir = os.path.join(remote_dir, rel_dir).replace('\\', '/')
        local_exists = os.path.isdir(local_subdir)
        remote_exists = self.path_exists(remote_subdir)
        was_present = rel_dir in previous_state and previous_state[rel_dir].get('type') == 'dir'
    
        # Directory exists locally but not remotely
        if local_exists and not remote_exists:
            if was_present:
                # Deleted remotely, so remove locally if empty
                if not os.listdir(local_subdir):
                    logger.info(f"Remote directory was deleted, removing local empty directory: {local_subdir}")
                    try:
                        os.rmdir(local_subdir)
                    except Exception as e:
                        logger.error(f"Failed to remove local directory {local_subdir}: {e}")
                        success = False
            else:
                # New local directory, create remotely
                logger.info(f"Creating remote directory: {remote_subdir}")
                if not self.create_directory(remote_subdir):
                    success = False
    
        # Directory exists remotely but not locally
        elif remote_exists and not local_exists:
            if was_present:
                # Deleted locally, so remove remotely if empty
                remote_items = self.list_files(remote_subdir)
                if not remote_items:
                    logger.info(f"Local directory was deleted, removing remote empty directory: {remote_subdir}")
                    try:
                        self.client.remove(self._normalize_api_path(remote_subdir), permanently=True)
                    except Exception as e:
                        logger.error(f"Failed to remove remote directory {remote_subdir}: {e}")
                        success = False
            else:
                # New remote directory, create locally
                logger.info(f"Creating local directory: {local_subdir}")
                try:
                    os.makedirs(local_subdir, exist_ok=True)
                except Exception as e:
                    logger.error(f"Failed to create local directory {local_subdir}: {e}")
                    success = False
    
        # Directory exists on both sides: nothing to do
        return success        
