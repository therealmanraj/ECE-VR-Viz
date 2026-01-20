import sys
from superset.app import create_app

app = create_app()


def check_user_permissions(username: str):
    """Check what permissions a user has"""
    with app.app_context():
        from superset import security_manager, db
        from superset.models.dashboard import Dashboard

        user = security_manager.find_user(username=username)

        if not user:
            print(f"❌ User '{username}' not found")
            return

        print(f"\n{'='*80}")
        print(f"USER: {user.username} ({user.first_name} {user.last_name})")
        print(f"Email: {user.email}")
        print(f"Active: {user.is_active}")
        print(f"{'='*80}\n")

        # Show roles
        print("ROLES:")
        for role in user.roles:
            print(f"  ✓ {role.name}")
        print()

        # Show all permissions from roles
        all_perms = set()
        for role in user.roles:
            for perm in role.permissions:
                all_perms.add(f"{perm.permission.name} on {perm.view_menu.name}")

        # Group by type
        dashboard_perms = [p for p in all_perms if "Dashboard" in p]
        chart_perms = [p for p in all_perms if "Chart" in p]
        dataset_perms = [p for p in all_perms if ("Dataset" in p or "Datasource" in p)]
        database_perms = [p for p in all_perms if "Database" in p]

        print("PERMISSIONS (from roles):")

        if dashboard_perms:
            print(f"\n  Dashboard Permissions ({len(dashboard_perms)}):")
            for perm in sorted(dashboard_perms):
                print(f"    • {perm}")

        if chart_perms:
            print(f"\n  Chart Permissions ({len(chart_perms)}):")
            for perm in sorted(chart_perms):
                print(f"    • {perm}")

        if dataset_perms:
            print(f"\n  Dataset/Datasource Permissions ({len(dataset_perms)}):")
            for perm in sorted(dataset_perms):
                print(f"    • {perm}")

        if database_perms:
            print(f"\n  Database Permissions ({len(database_perms)}):")
            for perm in sorted(database_perms):
                print(f"    • {perm}")

        print(f"\n  Total permissions: {len(all_perms)}")

        # Check dashboard access
        print(f"\n{'='*80}")
        print("DASHBOARD ACCESS:")
        print(f"{'='*80}\n")

        dashboards = db.session.query(Dashboard).all()

        if not dashboards:
            print("  No dashboards in system yet.\n")
            return

        accessible = []
        for dash in dashboards:
            owners = dash.owners or []
            roles = dash.roles or []

            is_owner = user in owners
            has_role_access = any(r in roles for r in user.roles)

            if is_owner or has_role_access:
                accessible.append(
                    {
                        "name": dash.dashboard_title,
                        "id": dash.id,
                        "is_owner": is_owner,
                        "roles": [r.name for r in roles],
                    }
                )

        if accessible:
            for d in accessible:
                access_type = []
                if d["is_owner"]:
                    access_type.append("✓ Owner")
                if d["roles"]:
                    access_type.append(f"✓ Via Role ({', '.join(d['roles'])})")

                print(f"  📊 {d['name']} (ID: {d['id']})")
                print(f"     Access: {' | '.join(access_type)}")
        else:
            print(f"  ❌ No dashboards accessible (Total dashboards: {len(dashboards)})")
        print()


def list_all_roles():
    """List all available roles and their permission counts"""
    with app.app_context():
        from superset import security_manager

        print(f"\n{'='*80}")
        print("ALL ROLES IN SYSTEM:")
        print(f"{'='*80}\n")

        roles = security_manager.get_all_roles()
        for role in roles:
            print(f"📋 {role.name:<20} perms={len(role.permissions)}")


def compare_roles(role1_name: str, role2_name: str):
    """Compare permissions between two roles"""
    with app.app_context():
        from superset import security_manager

        role1 = security_manager.find_role(role1_name)
        role2 = security_manager.find_role(role2_name)

        if not role1 or not role2:
            print("❌ One or both roles not found")
            return

        perms1 = {f"{p.permission.name} on {p.view_menu.name}" for p in role1.permissions}
        perms2 = {f"{p.permission.name} on {p.view_menu.name}" for p in role2.permissions}

        only_in_1 = perms1 - perms2
        only_in_2 = perms2 - perms1
        common = perms1 & perms2

        print(f"\n{'='*80}")
        print(f"COMPARING: {role1_name} vs {role2_name}")
        print(f"{'='*80}\n")

        print(f"Common permissions: {len(common)}")
        print(f"Only in {role1_name}: {len(only_in_1)}")
        print(f"Only in {role2_name}: {len(only_in_2)}")

        if only_in_1:
            print(f"\n🔵 ONLY in {role1_name}:")
            for perm in sorted(only_in_1)[:30]:
                print(f"  • {perm}")

        if only_in_2:
            print(f"\n🟢 ONLY in {role2_name}:")
            for perm in sorted(only_in_2)[:30]:
                print(f"  • {perm}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--roles":
            list_all_roles()
        elif sys.argv[1] == "--compare" and len(sys.argv) == 4:
            compare_roles(sys.argv[2], sys.argv[3])
        else:
            check_user_permissions(sys.argv[1])
    else:
        # If no args, list all users quickly
        with app.app_context():
            from superset import security_manager

            print("Checking all users...")
            for user in security_manager.get_all_users():
                print(f" - {user.username}")
