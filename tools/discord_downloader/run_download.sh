#!/bin/bash
# =================================================================
# Discord Message Downloader - Linux/macOS Cron Runner
# =================================================================
#
# This script is designed to be used with cron to periodically
# download Discord messages.
#
# Setup Steps:
#   1. Make this script executable: chmod +x run_download.sh
#   2. Edit the variables below
#   3. Add to crontab (crontab -e):
#      # Run every 6 hours
#      0 */6 * * * /path/to/discord_downloader/run_download.sh
#
#      # Run daily at 8am
#      0 8 * * * /path/to/discord_downloader/run_download.sh
#
# =================================================================

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_PATH="python3"
LOG_FILE="${SCRIPT_DIR}/download_log.txt"

# --- Run the downloader ---
cd "$SCRIPT_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Discord download..." >> "$LOG_FILE"
$PYTHON_PATH discord_downloader.py --last-run >> "$LOG_FILE" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Download finished (exit code: $?)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
