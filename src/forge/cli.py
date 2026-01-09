"""Forge CLI"""
import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from forge import Forge
from forge.agents import ALL_AGENTS

app = typer.Typer(name="forge", help="Multi-agent AI engineering platform")
console = Console()


@app.command()
def agents():
    """List all available agents."""
    table = Table(title="Available Agents")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    
    for name, definition in ALL_AGENTS.items():
        desc = definition.description[:60] + "..." if len(definition.description) > 60 else definition.description
        table.add_row(name, desc)
    
    console.print(table)


@app.command()
def analyze(
    path: Optional[str] = typer.Argument(None, help="Path to project to analyze"),
):
    """Analyze a project for issues."""
    target = Path(path) if path else Path.cwd()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing project...", total=None)
        
        forge = Forge(working_dir=target)
        result = asyncio.run(forge.analyze(target))
        
        progress.update(task, completed=True)
    
    if result.success:
        console.print("\n[green]Analysis complete![/green]\n")
        console.print(result.output)
        console.print(f"\n[dim]Cost: ${result.cost_usd:.4f} | Tokens: {result.tokens_used}[/dim]")
    else:
        console.print(f"\n[red]Analysis failed:[/red] {result.error}")


@app.command()
def fix(
    issue: str = typer.Argument(..., help="Description of the issue to fix"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Path to project"),
):
    """Fix a specific issue in the project."""
    target = Path(path) if path else Path.cwd()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Fixing: {issue[:50]}...", total=None)
        
        forge = Forge(working_dir=target)
        result = asyncio.run(forge.fix(issue, target))
        
        progress.update(task, completed=True)
    
    if result.success:
        console.print("\n[green]Fix applied![/green]\n")
        console.print(result.output)
        console.print(f"\n[dim]Cost: ${result.cost_usd:.4f} | Tokens: {result.tokens_used}[/dim]")
    else:
        console.print(f"\n[red]Fix failed:[/red] {result.error}")


@app.command()
def run(
    goal: str = typer.Argument(..., help="High-level goal for the workflow"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Path to project"),
):
    """Run a complete workflow based on a goal."""
    target = Path(path) if path else Path.cwd()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Running workflow: {goal[:50]}...", total=None)
        
        forge = Forge(working_dir=target)
        result = asyncio.run(forge.run(goal, target))
        
        progress.update(task, completed=True)
    
    if result.success:
        console.print(f"\n[green]Workflow complete![/green] ({result.steps_completed}/{result.total_steps} steps)\n")
        for step_name, step_result in result.results.items():
            console.print(f"[cyan]{step_name}:[/cyan]")
            console.print(step_result.output[:500] + "..." if len(step_result.output) > 500 else step_result.output)
            console.print()
        console.print(f"\n[dim]Total cost: ${result.total_cost_usd:.4f} | Tokens: {result.total_tokens}[/dim]")
    else:
        console.print(f"\n[red]Workflow failed at step {result.steps_completed}:[/red] {result.error}")


@app.command()
def cost():
    """Show cost summary."""
    forge = Forge()
    summary = forge.get_cost_summary()
    
    table = Table(title="Cost Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Total Cost", f"${summary['total_cost_usd']:.4f}")
    table.add_row("Budget", f"${summary['budget_usd']:.2f}")
    table.add_row("Remaining", f"${summary['remaining_usd']:.2f}")
    table.add_row("Usage", f"{summary['usage_percent']:.1f}%")
    table.add_row("Total Entries", str(summary['total_entries']))
    
    console.print(table)


if __name__ == "__main__":
    app()
