#!/usr/bin/env python3
"""
sync_watcher.py - Watch a local folder and rsync to a remote on any change.

Usage:
    python sync_watcher.py

Dependencies:
    pip install watchdog

Configuration: edit the CONFIG block below or pass env vars:
    LOCAL_DIR, REMOTE_HOST, REMOTE_USER, REMOTE_DIR, RSYNC_OPTS, DEBOUNCE
"""

import os
import subprocess
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ---------------------------------------------
# CONFIG - edit these or set as environment variables
# ---------------------------------------------
LOCAL_DIR = os.getenv("LOCAL_DIR", "./root/")  # folder to watch & sync
REMOTE_USER = os.getenv("REMOTE_USER", "user")  # SSH user
REMOTE_HOST = os.getenv("REMOTE_HOST", "192.168.1.17")  # SSH host or IP
REMOTE_DIR = os.getenv("REMOTE_DIR", "~/path/subpath")  # destination path
RSYNC_OPTS = os.getenv("RSYNC_OPTS", "-avz --mkpath --delete")  # rsync flags
DEBOUNCE = float(os.getenv("DEBOUNCE", "3.0"))  # seconds to wait before syncing

# SSH key path (optional - leave empty to use default ~/.ssh/id_rsa)
SSH_KEY = os.getenv("SSH_KEY", "")
# ---------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("sync_watcher")


def build_rsync_command() -> list[str]:
    """Build the rsync command list."""
    cmd = ["rsync"] + RSYNC_OPTS.split()

    if SSH_KEY:
        cmd += ["-e", f"ssh -i {SSH_KEY}"]

    # Trailing slash on source syncs *contents* of the folder
    src = str(LOCAL_DIR).rstrip("/") + "/"
    dst = f"{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_DIR}"

    cmd += [src, dst]
    return cmd


def run_rsync():
    """Execute rsync and log the result."""
    cmd = build_rsync_command()
    log.info("▶  rsync  →  %s@%s:%s", REMOTE_USER, REMOTE_HOST, REMOTE_DIR)
    log.debug("Command: %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        log.info("✔  Sync complete.")
    else:
        log.error(
            "✘  rsync failed (exit %d):\n%s", result.returncode, result.stderr.strip()
        )

    if result.stdout.strip():
        for line in result.stdout.strip().splitlines():
            log.debug("   %s", line)


class SyncHandler(FileSystemEventHandler):
    """Debounced file-system event handler that triggers rsync."""

    def __init__(self, debounce: float):
        super().__init__()
        self._debounce = debounce
        self._last_event = 0.0
        self._pending = False

    def _schedule_sync(self):
        """Record that a sync is needed; the main loop handles the debounce."""
        self._last_event = time.monotonic()
        self._pending = True

    def on_modified(self, event):
        if not event.is_directory:
            log.debug("MODIFIED  %s", event.src_path)
            self._schedule_sync()

    def on_created(self, event):
        if not event.is_directory:
            log.debug("CREATED   %s", event.src_path)
            self._schedule_sync()

    def on_deleted(self, event):
        log.debug("DELETED   %s", event.src_path)
        self._schedule_sync()

    def on_moved(self, event):
        log.debug("MOVED     %s → %s", event.src_path, event.dest_path)
        self._schedule_sync()

    def flush_if_ready(self):
        """Call from the main loop - syncs if debounce window has passed."""
        if self._pending and (time.monotonic() - self._last_event) >= self._debounce:
            self._pending = False
            run_rsync()


def validate_config():
    local = Path(LOCAL_DIR)
    if not local.exists():
        raise FileNotFoundError(f"LOCAL_DIR does not exist: {LOCAL_DIR}")
    if not local.is_dir():
        raise NotADirectoryError(f"LOCAL_DIR is not a directory: {LOCAL_DIR}")
    if REMOTE_HOST == "remote.server.com":
        log.warning(
            "REMOTE_HOST is still the default placeholder - edit CONFIG or set env vars."
        )


def main():
    validate_config()
    log.info("Watching  :  %s", LOCAL_DIR)
    log.info("Remote    :  %s@%s:%s", REMOTE_USER, REMOTE_HOST, REMOTE_DIR)
    log.info("Debounce  :  %.1f s  |  rsync opts: %s", DEBOUNCE, RSYNC_OPTS)

    handler = SyncHandler(debounce=DEBOUNCE)
    observer = Observer()
    observer.schedule(handler, path=LOCAL_DIR, recursive=True)
    observer.start()
    log.info("Observer started. Press Ctrl+C to stop.\n")

    try:
        while True:
            handler.flush_if_ready()
            time.sleep(0.5)
    except KeyboardInterrupt:
        log.info("Stopping…")
    finally:
        observer.stop()
        observer.join()
        log.info("Done.")


if __name__ == "__main__":
    main()
