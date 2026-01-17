import time
import sys
import random
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.markdown import Markdown

console = Console()

class NotionSidekick:
    def __init__(self):
        self.user_name = "Boss" 
        
    def fetch_tasks(self):
        """Simulate fetching from Notion"""
        return [
            {"id": 1, "title": "Reply to client emails", "energy": "low"},
            {"id": 2, "title": "Write quarterly report draft", "energy": "high"},
            {"id": 3, "title": "Fix the login bug", "energy": "high"}
        ]

    def ai_assist(self, task_title, request_type):
        """Simulate AI doing the work"""
        if request_type == "breakdown":
            if "email" in task_title.lower():
                return [
                    "Open Gmail (don't look at other emails!)",
                    "Search for 'Client X'",
                    "Hit Reply",
                    "Dictate the first sentence"
                ]
            else:
                return [
                    "Create a new file called 'draft.md'",
                    "Write the header",
                    "Dump 3 messy bullet points",
                    "Close eyes and breathe for 10s"
                ]
        elif request_type == "draft":
            return f"""
Subject: Re: Project Update

Hi [Name],

Thanks for checking in. We are making good progress on [Task A].
I expect to have the first version ready by [Date].

Best,
{self.user_name}
            """
        return "I'm here to help!"

def main():
    agent = NotionSidekick()
    
    console.clear()
    console.print(Panel.fit(f"[bold cyan]🚀 Sidekick Mode Activated[/bold cyan]\n[italic]Let's crush it, {agent.user_name}.[/italic]"))
    
    # 1. Fetch Phase
    with console.status("[bold green]Connecting to Notion Brain...[/bold green]", spinner="dots"):
        time.sleep(1.5) # Fake delay
        tasks = agent.fetch_tasks()

    console.print("\n[bold]🎯 Today's Mission Menu:[/bold]")
    for i, task in enumerate(tasks):
        icon = "🔋" if task['energy'] == "high" else "🪫"
        console.print(f"  [cyan]{i+1}.[/cyan] {task['title']}  [dim]({icon} energy)[/dim]")

    # 2. Choice Phase
    choice_idx = int(Prompt.ask("\nWhich one looks [bold red]least scary[/bold red] right now?", choices=["1", "2", "3"])) - 1
    current_task = tasks[choice_idx]
    
    console.print(Panel(f"[bold yellow]LOCKED ON TARGET:[/bold yellow] {current_task['title']}", expand=False))
    
    # 3. Initiation Phase (The Wall of Awful)
    if not Confirm.ask("Do you feel ready to start?"):
        console.print("\n[bold magenta]That's totally normal.[/bold magenta] Let's break it down so small it's ridiculous.")
        with console.status("De-scaring the task...", spinner="earth"):
            time.sleep(1)
            steps = agent.ai_assist(current_task['title'], "breakdown")
        
        console.print("\n[bold]👇 Your 5-Minute Plan:[/bold]")
        for step in steps:
            console.print(f"  [ ] {step}")
            
        Prompt.ask("\nPress [bold green]Enter[/bold green] when you've done just the FIRST step.")
        console.print("[bold green]🎉 BOOM! You started. That's the hardest part![/bold green]")

    # 4. Execution / Co-pilot Phase
    action = Prompt.ask("\nWhat do you need me to do?", choices=["Timer", "Draft content", "Cheer me up", "Done"], default="Draft content")
    
    if action == "Draft content":
        with console.status("Generating draft...", spinner="material"):
            time.sleep(2)
            draft = agent.ai_assist(current_task['title'], "draft")
        
        console.print(Panel(draft, title="🤖 AI Draft (Copy this!)", border_style="blue"))
        console.print("[italic]Use this as a starter. It doesn't have to be perfect.[/italic]")

    elif action == "Timer":
        seconds = 10
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task("Focus Sprint...", total=seconds)
            for _ in range(seconds):
                time.sleep(1)
        console.print("[bold]⏰ Ding! Sprint done. Take a breath.[/bold]")

    # 5. Closing
    console.print(f"\n[bold cyan]You are doing great, {agent.user_name}. One thing at a time.[/bold cyan] ✨")

if __name__ == "__main__":
    main()
