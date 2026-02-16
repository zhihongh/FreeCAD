#!/usr/bin/env python3
"""
Discord Channel Message Downloader

Downloads messages from specified Discord channels and saves them
as Markdown and/or JSON files. Designed to be run on a schedule
(via cron on Linux/macOS or Task Scheduler on Windows).

Usage:
    python discord_downloader.py                        # Download from all configured channels
    python discord_downloader.py --channel 123456789    # Download from a specific channel
    python discord_downloader.py --since 2025-01-01     # Download messages since a date
    python discord_downloader.py --last-run             # Download only new messages since last run

Requirements:
    pip install -r requirements.txt

Configuration:
    1. Create a Discord Bot at https://discord.com/developers/applications
    2. Enable MESSAGE_CONTENT intent in the Bot settings
    3. Invite the bot to your server with 'Read Message History' permission
    4. Set DISCORD_BOT_TOKEN in a .env file or environment variable
"""

import asyncio
import json
import os
import sys
import argparse
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import discord
    HAS_DISCORD = True
except ImportError:
    HAS_DISCORD = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

CONFIG_FILE = "downloader_config.json"
STATE_FILE = "downloader_state.json"

DEFAULT_CONFIG = {
    "output_dir": "discord_exports",
    "format": "both",
    "channels": [],
    "max_messages_per_run": 5000,
    "include_attachments": True,
    "include_embeds": True,
    "include_reactions": True,
}


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file, or create default."""
    path = Path(config_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        merged = {**DEFAULT_CONFIG, **user_config}
        return merged

    with open(path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
    logger.info(f"Created default config at {config_path}. Please edit it to add your channel IDs.")
    return DEFAULT_CONFIG


def load_state(state_path: str) -> Dict[str, Any]:
    """Load downloader state (tracks last downloaded message per channel)."""
    path = Path(state_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"channels": {}}


def save_state(state_path: str, state: Dict[str, Any]):
    """Save downloader state."""
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def format_message_md(msg: Dict[str, Any]) -> str:
    """Format a single message as Markdown."""
    lines = []
    timestamp = msg.get("timestamp", "")
    author = msg.get("author", "Unknown")
    content = msg.get("content", "")

    lines.append(f"### {author} — {timestamp}")
    lines.append("")

    if content:
        lines.append(content)
        lines.append("")

    attachments = msg.get("attachments", [])
    if attachments:
        lines.append("**Attachments:**")
        for att in attachments:
            name = att.get("filename", "file")
            url = att.get("url", "")
            lines.append(f"- [{name}]({url})")
        lines.append("")

    embeds = msg.get("embeds", [])
    if embeds:
        lines.append("**Embeds:**")
        for embed in embeds:
            title = embed.get("title", "")
            desc = embed.get("description", "")
            url = embed.get("url", "")
            if title:
                lines.append(f"- **{title}**" + (f" ([link]({url}))" if url else ""))
            if desc:
                lines.append(f"  {desc[:200]}...")
        lines.append("")

    reactions = msg.get("reactions", [])
    if reactions:
        reaction_str = " ".join(
            f"{r.get('emoji', '?')}×{r.get('count', 0)}" for r in reactions
        )
        lines.append(f"Reactions: {reaction_str}")
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def serialize_message(message: discord.Message, config: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a discord.Message object to a serializable dict."""
    data = {
        "id": str(message.id),
        "author": str(message.author),
        "author_id": str(message.author.id),
        "content": message.content,
        "timestamp": message.created_at.isoformat(),
        "edited_at": message.edited_at.isoformat() if message.edited_at else None,
        "type": str(message.type),
        "pinned": message.pinned,
    }

    if config.get("include_attachments", True) and message.attachments:
        data["attachments"] = [
            {
                "id": str(a.id),
                "filename": a.filename,
                "url": a.url,
                "size": a.size,
                "content_type": a.content_type,
            }
            for a in message.attachments
        ]

    if config.get("include_embeds", True) and message.embeds:
        data["embeds"] = [
            {
                "title": e.title,
                "description": e.description,
                "url": e.url,
                "type": e.type,
            }
            for e in message.embeds
        ]

    if config.get("include_reactions", True) and message.reactions:
        data["reactions"] = [
            {
                "emoji": str(r.emoji),
                "count": r.count,
            }
            for r in message.reactions
        ]

    if message.reference and message.reference.message_id:
        data["reply_to"] = str(message.reference.message_id)

    if message.thread:
        data["thread"] = {
            "id": str(message.thread.id),
            "name": message.thread.name,
        }

    return data


def write_markdown(messages: List[Dict[str, Any]], channel_name: str, output_path: Path):
    """Write messages to a Markdown file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Discord Channel: #{channel_name}\n\n")
        f.write(f"**Exported at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total messages:** {len(messages)}\n\n")
        f.write("---\n\n")
        for msg in messages:
            f.write(format_message_md(msg))


def write_json(messages: List[Dict[str, Any]], channel_name: str, output_path: Path):
    """Write messages to a JSON file."""
    export_data = {
        "channel": channel_name,
        "exported_at": datetime.now().isoformat(),
        "message_count": len(messages),
        "messages": messages,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)


async def download_channel(
    channel: discord.TextChannel,
    config: Dict[str, Any],
    after: Optional[datetime] = None,
    before: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Download messages from a single channel."""
    messages = []
    max_msgs = config.get("max_messages_per_run", 5000)

    kwargs = {"limit": max_msgs, "oldest_first": True}
    if after:
        kwargs["after"] = discord.Object(id=int(discord_snowflake_from_datetime(after)))
    if before:
        kwargs["before"] = discord.Object(id=int(discord_snowflake_from_datetime(before)))

    count = 0
    async for message in channel.history(**kwargs):
        msg_data = serialize_message(message, config)
        messages.append(msg_data)
        count += 1
        if count % 500 == 0:
            logger.info(f"  Downloaded {count} messages from #{channel.name}...")

    logger.info(f"  Total: {count} messages from #{channel.name}")
    return messages


def discord_snowflake_from_datetime(dt: datetime) -> int:
    """Convert a datetime to a Discord snowflake ID (approximate)."""
    discord_epoch = 1420070400000
    unix_ms = int(dt.timestamp() * 1000)
    return (unix_ms - discord_epoch) << 22


class DownloaderBot(discord.Client):
    """A minimal Discord bot that downloads messages and exits."""

    def __init__(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        target_channels: Optional[List[int]] = None,
        since: Optional[datetime] = None,
        use_last_run: bool = False,
        **kwargs,
    ):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, **kwargs)

        self.config = config
        self.state = state
        self.target_channels = target_channels
        self.since = since
        self.use_last_run = use_last_run
        self.output_dir = Path(config.get("output_dir", "discord_exports"))

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}")
        try:
            await self.run_download()
        except Exception as e:
            logger.error(f"Download failed: {e}", exc_info=True)
        finally:
            await self.close()

    async def run_download(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)

        channels_to_download = []

        if self.target_channels:
            for cid in self.target_channels:
                ch = self.get_channel(cid)
                if ch and isinstance(ch, discord.TextChannel):
                    channels_to_download.append(ch)
                else:
                    logger.warning(f"Channel {cid} not found or not a text channel.")
        elif self.config.get("channels"):
            for cid in self.config["channels"]:
                ch = self.get_channel(int(cid))
                if ch and isinstance(ch, discord.TextChannel):
                    channels_to_download.append(ch)
                else:
                    logger.warning(f"Configured channel {cid} not found or not a text channel.")
        else:
            for guild in self.guilds:
                for ch in guild.text_channels:
                    if ch.permissions_for(guild.me).read_message_history:
                        channels_to_download.append(ch)

        if not channels_to_download:
            logger.warning("No channels to download. Check your config or channel IDs.")
            return

        logger.info(f"Will download from {len(channels_to_download)} channel(s).")

        for channel in channels_to_download:
            after_dt = self.since
            channel_id_str = str(channel.id)

            if self.use_last_run and channel_id_str in self.state.get("channels", {}):
                last_ts = self.state["channels"][channel_id_str].get("last_message_time")
                if last_ts:
                    after_dt = datetime.fromisoformat(last_ts)
                    logger.info(f"Resuming #{channel.name} from {after_dt.isoformat()}")

            logger.info(f"Downloading #{channel.name} (ID: {channel.id})...")
            messages = await download_channel(channel, self.config, after=after_dt)

            if not messages:
                logger.info(f"  No new messages in #{channel.name}.")
                continue

            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(
                c for c in channel.name if c.isalnum() or c in ("-", "_")
            )
            base_name = f"{safe_name}_{date_str}"

            fmt = self.config.get("format", "both")
            if fmt in ("markdown", "both"):
                md_path = self.output_dir / f"{base_name}.md"
                write_markdown(messages, channel.name, md_path)
                logger.info(f"  Saved Markdown: {md_path}")

            if fmt in ("json", "both"):
                json_path = self.output_dir / f"{base_name}.json"
                write_json(messages, channel.name, json_path)
                logger.info(f"  Saved JSON: {json_path}")

            if messages:
                last_msg_time = messages[-1].get("timestamp", "")
                if "channels" not in self.state:
                    self.state["channels"] = {}
                self.state["channels"][channel_id_str] = {
                    "name": channel.name,
                    "last_message_time": last_msg_time,
                    "last_download": datetime.now().isoformat(),
                    "messages_downloaded": len(messages),
                }

        self.state["last_run"] = datetime.now().isoformat()
        save_state(STATE_FILE, self.state)
        logger.info("Download complete. State saved.")


def main():
    if not HAS_DISCORD:
        print("Error: discord.py is required. Install it with:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Download Discord channel messages to Markdown/JSON files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python discord_downloader.py                          # Download all accessible channels
  python discord_downloader.py --channel 123456789      # Download specific channel
  python discord_downloader.py --since 2025-01-01       # Messages since a date
  python discord_downloader.py --last-run               # Only new messages since last run
  python discord_downloader.py --list-channels          # List available channels and exit

Scheduling (Windows):
  Use the included run_download.bat with Windows Task Scheduler

Scheduling (Linux/macOS):
  Add to crontab: 0 */6 * * * cd /path/to/discord_downloader && python discord_downloader.py --last-run
        """,
    )
    parser.add_argument(
        "--channel", "-c",
        type=int,
        action="append",
        help="Channel ID to download (can specify multiple times)",
    )
    parser.add_argument(
        "--since", "-s",
        type=str,
        help="Download messages since this date (YYYY-MM-DD format)",
    )
    parser.add_argument(
        "--last-run",
        action="store_true",
        help="Only download messages since last successful run",
    )
    parser.add_argument(
        "--config",
        default=CONFIG_FILE,
        help=f"Path to config file (default: {CONFIG_FILE})",
    )
    parser.add_argument(
        "--list-channels",
        action="store_true",
        help="List available channels and exit",
    )
    parser.add_argument(
        "--token",
        type=str,
        help="Discord bot token (overrides DISCORD_BOT_TOKEN env var)",
    )

    args = parser.parse_args()

    token = args.token or os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("Error: Discord bot token is required.")
        print("Set DISCORD_BOT_TOKEN in .env file or pass via --token")
        print("")
        print("To create a bot token:")
        print("  1. Go to https://discord.com/developers/applications")
        print("  2. Create a new application")
        print("  3. Go to Bot section, click 'Reset Token' to get a token")
        print("  4. Enable MESSAGE_CONTENT intent under 'Privileged Gateway Intents'")
        print("  5. Use OAuth2 URL Generator to invite bot with 'Read Message History' permission")
        sys.exit(1)

    config = load_config(args.config)
    state = load_state(STATE_FILE)

    since_dt = None
    if args.since:
        try:
            since_dt = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Error: Invalid date format '{args.since}'. Use YYYY-MM-DD.")
            sys.exit(1)

    if args.list_channels:
        lister = ChannelLister(token)
        asyncio.run(lister.start(token))
        return

    bot = DownloaderBot(
        config=config,
        state=state,
        target_channels=args.channel,
        since=since_dt,
        use_last_run=args.last_run,
    )

    logger.info("Starting Discord downloader...")
    bot.run(token, log_handler=None)


class ChannelLister(discord.Client):
    """Helper bot that lists all accessible channels and exits."""

    def __init__(self, token: str):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self._token = token

    async def on_ready(self):
        print(f"\nLogged in as: {self.user}\n")
        print("Available Channels:")
        print("=" * 60)
        for guild in self.guilds:
            print(f"\nServer: {guild.name} (ID: {guild.id})")
            print("-" * 40)
            for ch in guild.text_channels:
                perms = ch.permissions_for(guild.me)
                readable = "OK" if perms.read_message_history else "NO ACCESS"
                print(f"  #{ch.name:<30} ID: {ch.id}  [{readable}]")
        print("\n" + "=" * 60)
        print("Use channel IDs above with --channel or in config file.")
        await self.close()


if __name__ == "__main__":
    main()
