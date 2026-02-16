#!/usr/bin/env python3
"""
Unified Task Runner - Run local programs (exe) + Discord downloads on a schedule.

This script orchestrates multiple tasks in sequence:
  1. Run any local program (e.g., WeChat content downloader exe)
  2. Run the Discord channel message downloader
  3. Log results

Designed to be called from Windows Task Scheduler or Linux cron.

Usage:
    python task_runner.py                           # Run all tasks in tasks_config.json
    python task_runner.py --config my_tasks.json    # Use a custom config file
    python task_runner.py --dry-run                 # Show what would run without executing
    python task_runner.py --task wechat             # Run only the task named "wechat"
    python task_runner.py --task discord             # Run only the Discord download task

Configuration:
    Edit tasks_config.json to define your tasks. See tasks_config.example.json for format.
"""

import json
import os
import sys
import subprocess
import argparse
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

LOG_DIR = "logs"
TASKS_CONFIG = "tasks_config.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def setup_file_logging():
    """Add a file handler so logs are written to disk."""
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    log_path = Path(LOG_DIR) / f"task_runner_{date_str}.log"
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    )
    logging.getLogger().addHandler(file_handler)
    return log_path


def load_tasks_config(config_path: str) -> Dict[str, Any]:
    """Load the tasks configuration file."""
    path = Path(config_path)
    if not path.exists():
        logger.error(f"Config file not found: {config_path}")
        logger.info("Creating example config. Please edit it and re-run.")
        create_example_config(config_path)
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_example_config(config_path: str):
    """Create an example tasks config file."""
    example = {
        "_comment": "Task Runner Configuration / 任务运行器配置",
        "tasks": [
            {
                "name": "wechat",
                "enabled": True,
                "description": "下载微信内容 (WeChat content downloader)",
                "type": "exe",
                "path": "C:\\path\\to\\your\\wechat_downloader.exe",
                "args": [],
                "working_directory": "C:\\path\\to\\your\\",
                "timeout_seconds": 300,
                "wait_after_seconds": 5,
            },
            {
                "name": "discord",
                "enabled": True,
                "description": "下载 Discord 频道消息",
                "type": "python",
                "script": "discord_downloader.py",
                "args": ["--last-run"],
                "timeout_seconds": 600,
                "wait_after_seconds": 0,
            },
        ],
        "settings": {
            "stop_on_error": False,
            "notification_on_complete": False,
        },
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(example, f, indent=2, ensure_ascii=False)
    logger.info(f"Example config written to {config_path}")


def run_exe_task(task: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """
    Run an external executable (exe) task.

    Returns a result dict with status, duration, and output.
    """
    exe_path = task.get("path", "")
    args = task.get("args", [])
    working_dir = task.get("working_directory", None)
    timeout = task.get("timeout_seconds", 300)

    if not exe_path:
        return {"status": "error", "message": "No 'path' specified for exe task."}

    exe_path = os.path.expandvars(os.path.expanduser(exe_path))

    if not os.path.isfile(exe_path):
        return {
            "status": "error",
            "message": f"Executable not found: {exe_path}",
            "hint": "请检查 tasks_config.json 中的 path 是否正确指向你的 exe 文件",
        }

    cmd = [exe_path] + args
    cmd_str = " ".join(cmd)

    if dry_run:
        logger.info(f"  [DRY RUN] Would execute: {cmd_str}")
        logger.info(f"  [DRY RUN] Working directory: {working_dir or '(current)'}")
        return {"status": "dry_run", "command": cmd_str}

    logger.info(f"  Executing: {cmd_str}")
    if working_dir:
        logger.info(f"  Working directory: {working_dir}")

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        duration = time.time() - start_time

        if result.returncode == 0:
            logger.info(f"  Completed successfully in {duration:.1f}s")
        else:
            logger.warning(f"  Exited with code {result.returncode} in {duration:.1f}s")

        if result.stdout.strip():
            logger.info(f"  STDOUT: {result.stdout.strip()[:500]}")
        if result.stderr.strip():
            logger.warning(f"  STDERR: {result.stderr.strip()[:500]}")

        return {
            "status": "success" if result.returncode == 0 else "error",
            "return_code": result.returncode,
            "duration_seconds": round(duration, 2),
            "stdout": result.stdout.strip()[:1000],
            "stderr": result.stderr.strip()[:1000],
        }

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        logger.error(f"  TIMEOUT after {timeout}s")
        return {
            "status": "timeout",
            "duration_seconds": round(duration, 2),
            "message": f"Process timed out after {timeout} seconds.",
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"File not found: {exe_path}",
            "hint": "请确认文件路径正确，且文件存在",
        }
    except PermissionError:
        return {
            "status": "error",
            "message": f"Permission denied: {exe_path}",
            "hint": "请确认你有执行该文件的权限，或以管理员身份运行",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


def run_python_task(task: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """
    Run a Python script task.

    Returns a result dict with status, duration, and output.
    """
    script = task.get("script", "")
    args = task.get("args", [])
    timeout = task.get("timeout_seconds", 600)

    if not script:
        return {"status": "error", "message": "No 'script' specified for python task."}

    script_path = Path(script)
    if not script_path.is_absolute():
        script_path = Path(__file__).parent / script

    if not script_path.exists():
        return {
            "status": "error",
            "message": f"Script not found: {script_path}",
        }

    cmd = [sys.executable, str(script_path)] + args
    cmd_str = " ".join(cmd)

    if dry_run:
        logger.info(f"  [DRY RUN] Would execute: {cmd_str}")
        return {"status": "dry_run", "command": cmd_str}

    logger.info(f"  Executing: {cmd_str}")

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=str(Path(__file__).parent),
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        duration = time.time() - start_time

        if result.returncode == 0:
            logger.info(f"  Completed successfully in {duration:.1f}s")
        else:
            logger.warning(f"  Exited with code {result.returncode} in {duration:.1f}s")

        if result.stdout.strip():
            logger.info(f"  STDOUT: {result.stdout.strip()[:500]}")
        if result.stderr.strip():
            logger.warning(f"  STDERR: {result.stderr.strip()[:500]}")

        return {
            "status": "success" if result.returncode == 0 else "error",
            "return_code": result.returncode,
            "duration_seconds": round(duration, 2),
            "stdout": result.stdout.strip()[:1000],
            "stderr": result.stderr.strip()[:1000],
        }

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        logger.error(f"  TIMEOUT after {timeout}s")
        return {
            "status": "timeout",
            "duration_seconds": round(duration, 2),
            "message": f"Script timed out after {timeout} seconds.",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_shell_task(task: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """
    Run an arbitrary shell command task.

    Returns a result dict with status, duration, and output.
    """
    command = task.get("command", "")
    working_dir = task.get("working_directory", None)
    timeout = task.get("timeout_seconds", 300)

    if not command:
        return {"status": "error", "message": "No 'command' specified for shell task."}

    if dry_run:
        logger.info(f"  [DRY RUN] Would execute shell: {command}")
        return {"status": "dry_run", "command": command}

    logger.info(f"  Executing shell: {command}")

    start_time = time.time()
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        duration = time.time() - start_time

        if result.returncode == 0:
            logger.info(f"  Completed successfully in {duration:.1f}s")
        else:
            logger.warning(f"  Exited with code {result.returncode} in {duration:.1f}s")

        return {
            "status": "success" if result.returncode == 0 else "error",
            "return_code": result.returncode,
            "duration_seconds": round(duration, 2),
            "stdout": result.stdout.strip()[:1000],
            "stderr": result.stderr.strip()[:1000],
        }

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return {
            "status": "timeout",
            "duration_seconds": round(duration, 2),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


TASK_RUNNERS = {
    "exe": run_exe_task,
    "python": run_python_task,
    "shell": run_shell_task,
}


def run_all_tasks(
    config: Dict[str, Any],
    dry_run: bool = False,
    filter_task: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Run all enabled tasks in sequence."""
    tasks = config.get("tasks", [])
    settings = config.get("settings", {})
    stop_on_error = settings.get("stop_on_error", False)

    results = []

    for task in tasks:
        name = task.get("name", "unnamed")
        enabled = task.get("enabled", True)
        task_type = task.get("type", "exe")
        description = task.get("description", "")

        if filter_task and name != filter_task:
            continue

        if not enabled:
            logger.info(f"[SKIP] Task '{name}' is disabled.")
            results.append({"task": name, "status": "skipped"})
            continue

        logger.info(f"{'='*60}")
        logger.info(f"[TASK] {name}: {description}")
        logger.info(f"  Type: {task_type}")

        runner = TASK_RUNNERS.get(task_type)
        if not runner:
            logger.error(f"  Unknown task type: {task_type}")
            results.append({"task": name, "status": "error", "message": f"Unknown type: {task_type}"})
            continue

        result = runner(task, dry_run=dry_run)
        result["task"] = name
        results.append(result)

        wait = task.get("wait_after_seconds", 0)
        if wait > 0 and not dry_run:
            logger.info(f"  Waiting {wait}s before next task...")
            time.sleep(wait)

        if result.get("status") == "error" and stop_on_error:
            logger.error(f"  Stopping due to error (stop_on_error=true)")
            break

    return results


def print_summary(results: List[Dict[str, Any]]):
    """Print a summary of all task results."""
    logger.info(f"\n{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"{'='*60}")

    for r in results:
        name = r.get("task", "?")
        status = r.get("status", "?")
        duration = r.get("duration_seconds", "")
        duration_str = f" ({duration}s)" if duration else ""

        icon = {
            "success": "OK",
            "error": "FAIL",
            "timeout": "TIMEOUT",
            "skipped": "SKIP",
            "dry_run": "DRY",
        }.get(status, "?")

        logger.info(f"  [{icon}] {name}{duration_str}")

        if status == "error":
            msg = r.get("message", r.get("stderr", ""))
            if msg:
                logger.info(f"        {msg[:200]}")
            hint = r.get("hint", "")
            if hint:
                logger.info(f"        Hint: {hint}")

    total = len(results)
    ok = sum(1 for r in results if r.get("status") == "success")
    fail = sum(1 for r in results if r.get("status") in ("error", "timeout"))
    logger.info(f"\n  Total: {total} | Success: {ok} | Failed: {fail}")


def save_run_report(results: List[Dict[str, Any]]):
    """Save a JSON report of this run."""
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    report_path = Path(LOG_DIR) / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report = {
        "run_at": datetime.now().isoformat(),
        "results": results,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.info(f"Run report saved to {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Unified Task Runner: run local exe files + Python scripts on a schedule.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python task_runner.py                          # Run all enabled tasks
  python task_runner.py --dry-run                # Preview what would run
  python task_runner.py --task wechat            # Run only the "wechat" task
  python task_runner.py --task discord            # Run only the Discord task
  python task_runner.py --config my_tasks.json   # Use custom config

Configure your tasks in tasks_config.json. Supports:
  - exe: Run any Windows executable (.exe, .bat, .cmd)
  - python: Run a Python script
  - shell: Run a shell command
        """,
    )
    parser.add_argument(
        "--config",
        default=TASKS_CONFIG,
        help=f"Path to tasks config file (default: {TASKS_CONFIG})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without actually running",
    )
    parser.add_argument(
        "--task", "-t",
        type=str,
        help="Run only a specific named task",
    )
    parser.add_argument(
        "--no-log-file",
        action="store_true",
        help="Don't write logs to file",
    )

    args = parser.parse_args()

    if not args.no_log_file:
        log_path = setup_file_logging()
        logger.info(f"Logging to {log_path}")

    logger.info(f"Task Runner started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    config = load_tasks_config(args.config)

    if args.dry_run:
        logger.info("[DRY RUN MODE] No tasks will actually execute.\n")

    results = run_all_tasks(config, dry_run=args.dry_run, filter_task=args.task)

    print_summary(results)

    if not args.dry_run:
        save_run_report(results)

    logger.info(f"\nTask Runner finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    has_errors = any(r.get("status") in ("error", "timeout") for r in results)
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
