"""
Migration Commands
Handle existing account migrations and OU moves
"""

import boto3
import click
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from lzaas.core.aft_manager import AFTManager
from lzaas.utils.validators import validate_email, validate_ou_name

console = Console()


@click.group()
def migrate():
    """Migrate existing accounts and manage OU moves"""
    pass


@migrate.command()
@click.option("--account-id", "-a", required=True, help="AWS Account ID to migrate")
@click.option("--account-name", "-n", required=True, help="Account name")
@click.option("--email", "-e", required=True, help="Account email address")
@click.option("--target-ou", "-o", required=True, help="Target Organizational Unit")
@click.option("--client-id", "-c", default="migrated", help="Client identifier")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without executing"
)
@click.pass_context
def account(ctx, account_id, account_name, email, target_ou, client_id, dry_run):
    """Migrate existing account to new OU via AFT"""

    # Validate inputs
    if not validate_email(email):
        console.print(f"[red]❌ Invalid email format: {email}[/red]")
        return

    if not validate_ou_name(target_ou):
        console.print(f"[red]❌ Invalid OU name: {target_ou}[/red]")
        return

    # Validate account ID format
    if not account_id.isdigit() or len(account_id) != 12:
        console.print(f"[red]❌ Invalid AWS Account ID format: {account_id}[/red]")
        return

    try:
        aft_manager = AFTManager(profile=ctx.obj["profile"], region=ctx.obj["region"])

        console.print(f"\n[bold cyan]🔄 Account Migration Plan[/bold cyan]")

        # Display migration details
        migration_table = Table(title="Migration Details")
        migration_table.add_column("Field", style="cyan", no_wrap=True)
        migration_table.add_column("Value", style="white")

        migration_table.add_row("Account ID", account_id)
        migration_table.add_row("Account Name", account_name)
        migration_table.add_row("Email", email)
        migration_table.add_row("Target OU", target_ou)
        migration_table.add_row("Client ID", client_id)
        migration_table.add_row("Operation", "OU Migration via AFT")

        console.print(migration_table)

        if dry_run:
            console.print(
                f"\n[yellow]🔍 DRY RUN MODE - No changes will be made[/yellow]"
            )

            # Show what would be created in AFT
            console.print(f"\n[bold]📋 AFT Account Request (Preview)[/bold]")
            aft_request = {
                "control_tower_parameters": {
                    "AccountEmail": email,
                    "AccountName": account_name,
                    "ManagedOrganizationalUnit": target_ou,
                    "SSOUserEmail": email,
                    "SSOUserFirstName": (
                        account_name.split()[0] if " " in account_name else account_name
                    ),
                    "SSOUserLastName": (
                        account_name.split()[-1] if " " in account_name else "User"
                    ),
                },
                "account_tags": {
                    "client": client_id,
                    "migration": "true",
                    "original_account_id": account_id,
                },
                "account_customizations_name": "migration-customization",
                "custom_fields": {
                    "migration_source": "existing_account",
                    "original_account_id": account_id,
                    "migration_date": "2025-01-10",
                },
            }

            import json

            console.print(f"[dim]{json.dumps(aft_request, indent=2)}[/dim]")

            console.print(f"\n[bold]⚠️  Important Notes for Migration:[/bold]")
            console.print(
                "• This creates a NEW account via AFT - it doesn't move the existing account"
            )
            console.print("• The existing account will remain in its current OU")
            console.print(
                "• You'll need to manually migrate resources from old to new account"
            )
            console.print(
                "• Consider using AWS Application Migration Service for resource migration"
            )
            console.print(
                "• Use 'lzaas migrate existing-ou' for direct OU moves without AFT"
            )

            return

        # Confirm before proceeding
        if not click.confirm(
            f"\n⚠️  This will create a NEW account via AFT. The existing account {account_id} will remain unchanged. Continue?"
        ):
            console.print("[yellow]Migration cancelled[/yellow]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating AFT migration request...", total=None)

            # Create account request for migration
            import uuid
            from datetime import datetime

            from lzaas.core.models import AccountRequest

            # Generate request ID for migration
            request_id = (
                f"migrate-{datetime.now().strftime('%Y-%m-%d')}-{str(uuid.uuid4())[:8]}"
            )

            migration_request = AccountRequest(
                request_id=request_id,
                template="client",  # Use client template for migrations
                email=email,
                name=account_name,
                client_id=client_id,
                requested_by=ctx.obj.get("user", "cli-user"),
                ou=target_ou,
                customizations={
                    "migration_source": "existing_account",
                    "original_account_id": account_id,
                    "migration_type": "ou_change",
                },
            )

            # Create the request
            result = aft_manager.create_account_request(migration_request)

            progress.remove_task(task)

        if result["success"]:
            console.print(
                f"\n[green]✅ Migration request created successfully![/green]"
            )
            console.print(f"[bold]Request ID:[/bold] {result['request_id']}")

            console.print(f"\n[bold cyan]📋 Next Steps:[/bold cyan]")
            console.print("1. Monitor the AFT pipeline for new account creation")
            console.print("2. Once new account is ready, plan resource migration")
            console.print(
                "3. Use AWS Application Migration Service for workload migration"
            )
            console.print("4. Update DNS, networking, and access configurations")
            console.print("5. Decommission old account after successful migration")

            console.print(f"\n[bold]Monitor progress:[/bold]")
            console.print(
                f"[dim]lzaas status check --request-id {result['request_id']}[/dim]"
            )
        else:
            console.print(f"[red]❌ Migration request failed: {result['error']}[/red]")

    except Exception as e:
        console.print(f"[red]❌ Error creating migration request: {str(e)}[/red]")


@migrate.command()
@click.option("--account-id", "-a", required=True, help="AWS Account ID to move")
@click.option("--target-ou", "-o", required=True, help="Target Organizational Unit")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without executing"
)
@click.pass_context
def existing_ou(ctx, account_id, target_ou, dry_run):
    """Move existing account to different OU (direct Organizations API)"""

    # Validate account ID format
    if not account_id.isdigit() or len(account_id) != 12:
        console.print(f"[red]❌ Invalid AWS Account ID format: {account_id}[/red]")
        return

    if not validate_ou_name(target_ou):
        console.print(f"[red]❌ Invalid OU name: {target_ou}[/red]")
        return

    try:
        # Initialize AWS Organizations client
        session = boto3.Session(
            profile_name=ctx.obj["profile"], region_name=ctx.obj["region"]
        )
        orgs_client = session.client("organizations")

        console.print(f"\n[bold cyan]🔄 Direct OU Move Operation[/bold cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Gathering account information...", total=None)

            # Get current account details
            try:
                account_info = orgs_client.describe_account(AccountId=account_id)
                account = account_info["Account"]
            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]❌ Failed to get account info: {str(e)}[/red]")
                return

            # Get current parent (OU or root)
            try:
                parents = orgs_client.list_parents(ChildId=account_id)
                current_parent = parents["Parents"][0] if parents["Parents"] else None
            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]❌ Failed to get current parent: {str(e)}[/red]")
                return

            # Find target OU
            try:
                # List all OUs to find the target
                target_ou_id = None
                paginator = orgs_client.get_paginator(
                    "list_organizational_units_for_parent"
                )

                # Get root ID first
                roots = orgs_client.list_roots()
                root_id = roots["Roots"][0]["Id"]

                # Search for OU by name
                def find_ou_by_name(parent_id, ou_name):
                    for page in paginator.paginate(ParentId=parent_id):
                        for ou in page["OrganizationalUnits"]:
                            if ou["Name"] == ou_name:
                                return ou["Id"]
                            # Recursively search in child OUs
                            child_ou_id = find_ou_by_name(ou["Id"], ou_name)
                            if child_ou_id:
                                return child_ou_id
                    return None

                target_ou_id = find_ou_by_name(root_id, target_ou)

                if not target_ou_id:
                    progress.remove_task(task)
                    console.print(f"[red]❌ Target OU '{target_ou}' not found[/red]")
                    return

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]❌ Failed to find target OU: {str(e)}[/red]")
                return

            progress.remove_task(task)

        # Display move details
        move_table = Table(title="OU Move Details")
        move_table.add_column("Field", style="cyan", no_wrap=True)
        move_table.add_column("Value", style="white")

        move_table.add_row("Account ID", account_id)
        move_table.add_row("Account Name", account["Name"])
        move_table.add_row("Account Email", account["Email"])
        move_table.add_row(
            "Current Parent", current_parent["Id"] if current_parent else "Unknown"
        )
        move_table.add_row("Target OU", f"{target_ou} ({target_ou_id})")
        move_table.add_row("Operation", "Direct OU Move")

        console.print(move_table)

        if dry_run:
            console.print(
                f"\n[yellow]🔍 DRY RUN MODE - No changes will be made[/yellow]"
            )
            console.print(f"\n[bold]Would execute:[/bold]")
            console.print(
                f"[dim]aws organizations move-account --account-id {account_id} --source-parent-id {current_parent['Id']} --destination-parent-id {target_ou_id}[/dim]"
            )
            return

        # Confirm before proceeding
        if not click.confirm(f"\n⚠️  Move account {account_id} to OU '{target_ou}'?"):
            console.print("[yellow]Move cancelled[/yellow]")
            return

        # Perform the move
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Moving account to new OU...", total=None)

            try:
                orgs_client.move_account(
                    AccountId=account_id,
                    SourceParentId=current_parent["Id"],
                    DestinationParentId=target_ou_id,
                )
                progress.remove_task(task)

                console.print(
                    f"\n[green]✅ Account successfully moved to OU '{target_ou}'![/green]"
                )

                console.print(f"\n[bold cyan]📋 Post-Move Checklist:[/bold cyan]")
                console.print("• Verify account appears in correct OU in AWS Console")
                console.print("• Update any automation that references the old OU")
                console.print("• Check that SCPs are applied correctly")
                console.print("• Verify IAM permissions and access patterns")
                console.print("• Update documentation and inventory systems")

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]❌ Failed to move account: {str(e)}[/red]")
                console.print(
                    f"[yellow]💡 This might be due to insufficient permissions or SCP restrictions[/yellow]"
                )

    except Exception as e:
        console.print(f"[red]❌ Error during OU move: {str(e)}[/red]")


@migrate.command()
@click.option("--source", "-s", required=True, help="Source account name or ID")
@click.option("--target", "-t", required=True, help="Target OU name")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without executing"
)
@click.pass_context
def simple(ctx, source, target, dry_run):
    """Simple migration command for moving accounts to different OUs"""

    console.print(f"\n[bold cyan]🔄 Simple Account Migration[/bold cyan]")

    try:
        session = boto3.Session(
            profile_name=ctx.obj["profile"], region_name=ctx.obj["region"]
        )
        orgs_client = session.client("organizations")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Finding source account...", total=None)

            # Find source account
            account_id = None
            account_name = None

            if source.isdigit() and len(source) == 12:
                # Source is account ID
                account_id = source
                try:
                    account_info = orgs_client.describe_account(AccountId=account_id)
                    account_name = account_info["Account"]["Name"]
                except Exception as e:
                    progress.remove_task(task)
                    console.print(f"[red]❌ Account {account_id} not found: {str(e)}[/red]")
                    return
            else:
                # Source is account name - search for it
                try:
                    paginator = orgs_client.get_paginator('list_accounts')
                    for page in paginator.paginate():
                        for account in page['Accounts']:
                            if account['Name'].lower() == source.lower():
                                account_id = account['Id']
                                account_name = account['Name']
                                break
                        if account_id:
                            break

                    if not account_id:
                        progress.remove_task(task)
                        console.print(f"[red]❌ Account '{source}' not found[/red]")
                        return

                except Exception as e:
                    progress.remove_task(task)
                    console.print(f"[red]❌ Error searching for account: {str(e)}[/red]")
                    return

            progress.update(task, description="Finding target OU...")

            # Find target OU (reuse logic from existing_ou command)
            target_ou_id = None
            try:
                roots = orgs_client.list_roots()
                root_id = roots["Roots"][0]["Id"]

                def find_ou_by_name(parent_id, ou_name):
                    paginator = orgs_client.get_paginator("list_organizational_units_for_parent")
                    for page in paginator.paginate(ParentId=parent_id):
                        for ou in page["OrganizationalUnits"]:
                            if ou["Name"].lower() == ou_name.lower():
                                return ou["Id"]
                            child_ou_id = find_ou_by_name(ou["Id"], ou_name)
                            if child_ou_id:
                                return child_ou_id
                    return None

                target_ou_id = find_ou_by_name(root_id, target)

                if not target_ou_id:
                    progress.remove_task(task)
                    console.print(f"[red]❌ Target OU '{target}' not found[/red]")
                    console.print(f"[yellow]💡 Use 'lzaas migrate list-ous' to see available OUs[/yellow]")
                    return

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]❌ Error finding target OU: {str(e)}[/red]")
                return

            progress.update(task, description="Getting current location...")

            # Get current parent
            try:
                parents = orgs_client.list_parents(ChildId=account_id)
                current_parent = parents["Parents"][0] if parents["Parents"] else None
            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]❌ Failed to get current parent: {str(e)}[/red]")
                return

            progress.remove_task(task)

        # Display migration plan
        migration_table = Table(title="Migration Plan")
        migration_table.add_column("Field", style="cyan", no_wrap=True)
        migration_table.add_column("Value", style="white")

        migration_table.add_row("Source Account", f"{account_name} ({account_id})")
        migration_table.add_row("Target OU", f"{target} ({target_ou_id})")
        migration_table.add_row("Current Parent", current_parent["Id"] if current_parent else "Unknown")
        migration_table.add_row("Operation", "Direct OU Move")

        console.print(migration_table)

        if dry_run:
            console.print(f"\n[yellow]🔍 DRY RUN MODE - No changes will be made[/yellow]")
            console.print(f"\n[bold]Would execute:[/bold]")
            console.print(f"[dim]Move account {account_id} from {current_parent['Id']} to {target_ou_id}[/dim]")
            return

        # Confirm before proceeding
        if not click.confirm(f"\n⚠️  Move '{account_name}' to OU '{target}'?"):
            console.print("[yellow]Migration cancelled[/yellow]")
            return

        # Perform the move
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Moving account...", total=None)

            try:
                orgs_client.move_account(
                    AccountId=account_id,
                    SourceParentId=current_parent["Id"],
                    DestinationParentId=target_ou_id,
                )
                progress.remove_task(task)

                console.print(f"\n[green]✅ Successfully moved '{account_name}' to OU '{target}'![/green]")

                console.print(f"\n[bold cyan]📋 Next Steps:[/bold cyan]")
                console.print("• Verify account appears in correct OU in AWS Console")
                console.print("• Check that SCPs are applied correctly")
                console.print("• Update any automation referencing the old OU")
                console.print("• Verify IAM permissions still work as expected")

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]❌ Failed to move account: {str(e)}[/red]")

                # Provide helpful error context
                if "AccessDenied" in str(e):
                    console.print(f"[yellow]💡 Check that you have organizations:MoveAccount permission[/yellow]")
                elif "ConstraintViolation" in str(e):
                    console.print(f"[yellow]💡 This might be due to SCP restrictions or account constraints[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Error during migration: {str(e)}[/red]")


@migrate.command()
@click.pass_context
def list_ous(ctx):
    """List all available Organizational Units"""

    try:
        session = boto3.Session(
            profile_name=ctx.obj["profile"], region_name=ctx.obj["region"]
        )
        orgs_client = session.client("organizations")

        console.print(f"\n[bold cyan]📋 Available Organizational Units[/bold cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching organizational structure...", total=None)

            # Get root
            roots = orgs_client.list_roots()
            root_id = roots["Roots"][0]["Id"]
            root_name = roots["Roots"][0]["Name"]

            # Recursively get all OUs
            def get_ous_recursive(parent_id, parent_name, level=0):
                ous = []
                try:
                    paginator = orgs_client.get_paginator(
                        "list_organizational_units_for_parent"
                    )
                    for page in paginator.paginate(ParentId=parent_id):
                        for ou in page["OrganizationalUnits"]:
                            indent = "  " * level
                            ous.append(
                                {
                                    "name": ou["Name"],
                                    "id": ou["Id"],
                                    "level": level,
                                    "display": f"{indent}├─ {ou['Name']} ({ou['Id']})",
                                }
                            )
                            # Recursively get child OUs
                            child_ous = get_ous_recursive(
                                ou["Id"], ou["Name"], level + 1
                            )
                            ous.extend(child_ous)
                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Could not list OUs for {parent_name}: {str(e)}[/yellow]"
                    )
                return ous

            # Get all OUs
            all_ous = get_ous_recursive(root_id, root_name, 0)

            progress.remove_task(task)

        # Display organizational structure
        console.print(f"\n[bold]🏗️  Root: {root_name} ({root_id})[/bold]")

        if not all_ous:
            console.print("[yellow]No Organizational Units found[/yellow]")
        else:
            for ou in all_ous:
                console.print(ou["display"])

        console.print(f"\n[dim]💡 Use OU names (not IDs) with migration commands[/dim]")
        console.print(
            f"[dim]Example: lzaas migrate existing-ou --account-id 198610579545 --target-ou Sandbox[/dim]"
        )

    except Exception as e:
        console.print(f"[red]❌ Error listing OUs: {str(e)}[/red]")
