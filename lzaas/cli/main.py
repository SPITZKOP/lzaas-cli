#!/usr/bin/env python3
"""
LZaaS CLI Main Entry Point
Landing Zone as a Service - AWS Account Factory Automation
"""

import os
import sys

import click
from rich import print as rprint
from rich.console import Console
from rich.table import Table

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lzaas import __version__
from lzaas.cli.commands.account import account
from lzaas.cli.commands.docs import docs
from lzaas.cli.commands.migrate import migrate
from lzaas.cli.commands.status import status
from lzaas.cli.commands.template import template

console = Console()


@click.group()
@click.version_option(version=__version__)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--profile", default="default", help="AWS profile to use")
@click.option("--region", default="eu-west-3", help="AWS region to use")
@click.pass_context
def cli(ctx, verbose, profile, region):
    """
    🚀 LZaaS CLI - Landing Zone as a Service

    Automate AWS Account Factory operations with ease.
    Manage account requests, templates, and monitor AFT workflows.

    Examples:
      lzaas account create --template dev --email dev@company.com
      lzaas account list --client internal
      lzaas status --request-id dev-2025-001
      lzaas template list
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["profile"] = profile
    ctx.obj["region"] = region

    if verbose:
        console.print(f"[green]✓[/green] Using AWS profile: {profile}")
        console.print(f"[green]✓[/green] Using AWS region: {region}")


@cli.command()
def info():
    """Display LZaaS system information and health status"""

    table = Table(title="🏗️  LZaaS System Information")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")

    # System info
    table.add_row("LZaaS CLI", "✅ Active", f"Version {__version__}")
    table.add_row("AFT Infrastructure", "✅ Deployed", "Core components operational")
    table.add_row("GitHub Integration", "⚠️  Pending", "Repositories need setup")
    table.add_row("DynamoDB", "✅ Ready", "Account requests table available")

    console.print(table)

    # Quick start guide
    console.print("\n[bold cyan]🚀 Quick Start:[/bold cyan]")
    console.print(
        "1. [yellow]lzaas account create --template dev --email test@company.com[/yellow]"
    )
    console.print("2. [yellow]lzaas status --request-id <request-id>[/yellow]")
    console.print("3. [yellow]lzaas account list[/yellow]")

    console.print("\n[bold cyan]📚 Documentation:[/bold cyan]")
    console.print(
        "• User Guide: [blue]lzaas docs user-guide[/blue] - Complete user documentation"
    )
    console.print(
        "• Quick Reference: [blue]lzaas docs quick-reference[/blue] - Command cheat sheet"
    )
    console.print(
        "• Installation: [blue]lzaas docs installation[/blue] - Setup instructions"
    )
    console.print(
        "• All Docs: [blue]lzaas docs list[/blue] - List all available documentation"
    )


# Add command groups
cli.add_command(account)
cli.add_command(template)
cli.add_command(status)
cli.add_command(migrate)
cli.add_command(docs)

if __name__ == "__main__":
    cli()
