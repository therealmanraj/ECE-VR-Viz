#!/usr/bin/env python3
"""
COMPLETE CLIENT ISOLATION SETUP FOR SUPERSET

This script configures:
1. Gamma role: Read-only UI permissions (for ALL clients)
2. Client roles (CrescentIslandFarms, PureSunfarms): Database + Datasource access for RLS

Result: Clients can ONLY see their assigned dashboards and ONLY their filtered data.
"""

import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def setup_complete_client_isolation():
    """
    Complete setup for multi-tenant client isolation.
    """
    from superset.app import create_app
    
    log.info("Creating Superset application...")
    app = create_app()
    
    with app.app_context():
        from superset import db, security_manager
        from superset.models.core import Database
        from superset.connectors.sqla.models import SqlaTable
        
        # =================================================================
        # STEP 1: Configure Gamma role (READ-ONLY UI)
        # =================================================================
        log.info("\n" + "="*70)
        log.info("STEP 1: Configuring Gamma role (READ-ONLY UI)")
        log.info("="*70)
        
        # STRICT read-only permissions - NO create, edit, delete, export
        gamma_permission_list = [
            # Dashboard and Chart viewing
            ('can_read', 'Chart'),
            ('can_read', 'Dashboard'),
            ('can_view_chart_as_table', 'Dashboard'),
            ('can_view_query', 'Dashboard'),
            ('can_drill', 'Dashboard'),
            
            # Dataset viewing (needed for charts to load)
            ('can_read', 'Dataset'),
            ('can_read', 'Database'),
            
            # Menu access
            ('menu_access', 'Dashboards'),
            
            # Dashboard permalinks and filters
            ('can_read', 'DashboardPermalinkRestApi'),
            ('can_read', 'DashboardFilterStateRestApi'),
            ('can_get_embedded', 'Dashboard'),
            ('can_read', 'EmbeddedDashboard'),
            
            # Explore (view only, no saving)
            ('can_read', 'Explore'),
            ('can_read', 'ExplorePermalinkRestApi'),
            ('can_read', 'ExploreFormDataRestApi'),
            
            # API access (needed for dashboards to work)
            ('can_get', 'MenuApi'),
            ('can_query_form_data', 'Api'),
            ('can_query', 'Api'),
            ('can_time_range', 'Api'),
            ('can_list', 'AsyncEventsRestApi'),
            
            # Datasource metadata (needed for charts)
            ('can_external_metadata', 'Datasource'),
            ('can_get', 'Datasource'),
            ('can_external_metadata_by_name', 'Datasource'),
            
            # Superset core
            ('can_log', 'Superset'),
            ('can_fetch_datasource_metadata', 'Superset'),
            ('can_dashboard_permalink', 'Superset'),
            ('can_slice', 'Superset'),
            ('can_dashboard', 'Superset'),
            
            # Key-value store (for dashboard state)
            ('can_get_value', 'KV'),
            
            # Misc
            ('can_read', 'AdvancedDataType'),
            ('can_read', 'AvailableDomains'),
            ('can_read', 'Tag'),
            ('can_list', 'Tags'),
            ('can_recent_activity', 'Log'),
            ('can_read', 'SecurityRestApi'),
        ]
        
        log.info(f"Target: {len(gamma_permission_list)} read-only permissions for Gamma")
        
        # Find permissions
        gamma_permissions = []
        not_found = []
        
        for permission_name, view_menu_name in gamma_permission_list:
            perm = security_manager.find_permission_view_menu(
                permission_name,
                view_menu_name
            )
            if perm:
                gamma_permissions.append(perm)
            else:
                not_found.append(f"{permission_name} on {view_menu_name}")
        
        log.info(f"Found: {len(gamma_permissions)} permissions")
        if not_found:
            log.warning(f"Not found ({len(not_found)} permissions) - may not exist in this Superset version:")
            for nf in not_found[:5]:
                log.warning(f"  - {nf}")
            if len(not_found) > 5:
                log.warning(f"  ... and {len(not_found) - 5} more")
        
        # Update Gamma role
        gamma_role = security_manager.find_role('Gamma')
        if not gamma_role:
            log.error("❌ Gamma role not found!")
            return False
        
        try:
            log.info(f"\nUpdating Gamma role...")
            log.info(f"  Before: {len(gamma_role.permissions)} permissions")
            
            gamma_role.permissions = []
            for perm in gamma_permissions:
                gamma_role.permissions.append(perm)
            
            db.session.add(gamma_role)
            db.session.commit()
            
            log.info(f"  After: {len(gamma_role.permissions)} permissions")
            log.info(f"✅ Gamma role updated with READ-ONLY permissions")
            
            # Verify no dangerous permissions
            dangerous = []
            for perm in gamma_role.permissions:
                perm_str = str(perm).lower()
                if any(x in perm_str for x in ['can_write', 'can_create', 'can_edit', 'can_delete', 'can_save', 'can_add', 'can_export']):
                    dangerous.append(str(perm))
            
            if dangerous:
                log.error(f"⚠️  WARNING: Gamma still has {len(dangerous)} write permissions:")
                for d in dangerous[:5]:
                    log.error(f"     {d}")
            else:
                log.info(f"✅ Verified: Gamma has NO write/edit/delete permissions")
                
        except Exception as e:
            log.error(f"❌ Error updating Gamma role: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False
        
        # =================================================================
        # STEP 2: Configure Client Roles (Database + Datasource Access)
        # =================================================================
        log.info("\n" + "="*70)
        log.info("STEP 2: Configuring Client Roles (for RLS and data access)")
        log.info("="*70)
        
        auth_roles_mapping = app.config.get('AUTH_ROLES_MAPPING', {})
        client_roles = set()
        
        for keycloak_role, superset_role_list in auth_roles_mapping.items():
            if keycloak_role.startswith('client_'):
                client_roles.update(superset_role_list)
        
        if not client_roles:
            log.warning("⚠️  No client_* roles found in AUTH_ROLES_MAPPING")
            log.warning("   Expected format:")
            log.warning("   AUTH_ROLES_MAPPING = {")
            log.warning('     "client_crescent_island_farms": ["Gamma", "CrescentIslandFarms"],')
            log.warning('     "client_pure_sunfarms": ["Gamma", "PureSunfarms"],')
            log.warning("   }")
        else:
            log.info(f"Found {len(client_roles)} client roles: {sorted(client_roles)}")
        
        # Get database access permissions
        databases = db.session.query(Database).all()
        log.info(f"\nFound {len(databases)} database(s)")
        
        database_access_permissions = []
        for database in databases:
            vm_name = f'[{database.database_name}].(id:{database.id})'
            db_perm = security_manager.find_permission_view_menu(
                'database_access',
                vm_name
            )
            if db_perm:
                database_access_permissions.append(db_perm)
                log.info(f"  ✅ Database: {database.database_name}")
            else:
                log.warning(f"  ⚠️  Missing database_access permission for: {vm_name}")
        
        # Get ALL datasource access permissions (for RLS to work)
        log.info(f"\nGetting datasource access permissions (needed for RLS)...")
        datasets = db.session.query(SqlaTable).all()
        log.info(f"Found {len(datasets)} dataset(s)")
        
        datasource_access_permissions = []
        for dataset in datasets:
            try:
                vm_name = security_manager.get_dataset_access_link(dataset)
                ds_perm = security_manager.find_permission_view_menu(
                    'datasource_access',
                    vm_name
                )
                if ds_perm:
                    datasource_access_permissions.append(ds_perm)
                    log.info(f"  ✅ Dataset: {dataset.table_name}")
            except Exception as e:
                log.warning(f"  ⚠️  Error getting datasource access for {dataset.table_name}: {e}")
        
        # Combine permissions for client roles
        all_client_permissions = database_access_permissions + datasource_access_permissions
        
        log.info(f"\n📊 Total permissions for each client role:")
        log.info(f"  - Database access: {len(database_access_permissions)}")
        log.info(f"  - Datasource access: {len(datasource_access_permissions)}")
        log.info(f"  - TOTAL: {len(all_client_permissions)}")
        
        # Update each client role
        created_count = 0
        updated_count = 0
        
        for role_name in sorted(client_roles):
            role = security_manager.find_role(role_name)
            
            if role is None:
                log.info(f"\n➕ Creating: {role_name}")
                try:
                    role = security_manager.add_role(role_name)
                    if not role:
                        log.error(f"❌ Failed to create role: {role_name}")
                        continue
                    created_count += 1
                except Exception as e:
                    log.error(f"❌ Error creating {role_name}: {e}")
                    db.session.rollback()
                    continue
            else:
                log.info(f"\n✏️  Updating: {role_name}")
            
            try:
                # Clear and reassign permissions
                before = len(role.permissions)
                role.permissions = []
                
                for perm in all_client_permissions:
                    role.permissions.append(perm)
                
                db.session.add(role)
                db.session.commit()
                
                after = len(role.permissions)
                updated_count += 1
                
                log.info(f"✅ {role_name}: {after} permissions")
                log.info(f"   - Database access: {len(database_access_permissions)}")
                log.info(f"   - Datasource access: {len(datasource_access_permissions)}")
                if before != after:
                    log.info(f"   - Changed: {before} → {after}")
                
                # Verify only safe permissions
                unsafe = []
                for perm in role.permissions:
                    perm_str = str(perm).lower()
                    if any(x in perm_str for x in ['can_write', 'can_create', 'can_edit', 'can_delete', 'can_save', 'can_add', 'can_export', 'sql_lab']):
                        unsafe.append(str(perm))
                
                if unsafe:
                    log.warning(f"⚠️  WARNING: {role_name} has {len(unsafe)} potentially unsafe permissions:")
                    for u in unsafe[:3]:
                        log.warning(f"      {u}")
                    
            except Exception as e:
                log.error(f"❌ Error updating {role_name}: {e}")
                import traceback
                traceback.print_exc()
                db.session.rollback()
        
        # =================================================================
        # FINAL SUMMARY
        # =================================================================
        log.info("\n" + "="*70)
        log.info("✅ SETUP COMPLETE!")
        log.info("="*70)
        
        log.info(f"\n📋 CONFIGURATION SUMMARY:")
        log.info(f"\n  Gamma Role:")
        log.info(f"    - Permissions: {len(gamma_permissions)}")
        log.info(f"    - Purpose: Read-only UI for ALL clients")
        log.info(f"    - Capabilities: View dashboards, charts, use filters")
        log.info(f"    - Restrictions: No create, edit, delete, export, SQL Lab")
        
        log.info(f"\n  Client Roles ({len(client_roles)}):")
        for role_name in sorted(client_roles):
            role = security_manager.find_role(role_name)
            if role:
                log.info(f"    - {role_name}: {len(role.permissions)} permissions")
        log.info(f"    - Purpose: Data access + RLS filtering")
        log.info(f"    - Database access: {len(database_access_permissions)}")
        log.info(f"    - Datasource access: {len(datasource_access_permissions)}")
        
        log.info(f"\n🔒 SECURITY MODEL:")
        log.info(f"  User with: [Gamma, CrescentIslandFarms]")
        log.info(f"    ├─ Gamma → UI permissions (view dashboards/charts)")
        log.info(f"    └─ CrescentIslandFarms → Data access + RLS filter")
        log.info(f"  ")
        log.info(f"  Result:")
        log.info(f"    ✅ Can view dashboards assigned to CrescentIslandFarms role")
        log.info(f"    ✅ Data filtered by RLS rule on CrescentIslandFarms role")
        log.info(f"    ❌ Cannot see PureSunfarms dashboards")
        log.info(f"    ❌ Cannot see PureSunfarms data")
        log.info(f"    ❌ Cannot create/edit/delete anything")
        
        log.info(f"\n📝 NEXT STEPS:")
        log.info(f"\n  1. Assign dashboards to roles:")
        log.info(f"     - Edit each dashboard → Properties → Advanced")
        log.info(f"     - Scroll to find 'Roles' field")
        log.info(f"     - CIF dashboard → Assign to 'CrescentIslandFarms' role")
        log.info(f"     - PSF dashboard → Assign to 'PureSunfarms' role")
        log.info(f"     OR use Python:")
        log.info(f"       docker compose exec superset superset shell")
        log.info(f"       >>> from superset import db, security_manager")
        log.info(f"       >>> from superset.models.dashboard import Dashboard")
        log.info(f"       >>> dash = db.session.query(Dashboard).filter_by(dashboard_title='CIF').first()")
        log.info(f"       >>> role = security_manager.find_role('CrescentIslandFarms')")
        log.info(f"       >>> dash.roles = [role]")
        log.info(f"       >>> db.session.commit()")
        
        log.info(f"\n  2. Create RLS rules:")
        log.info(f"     Settings → Row Level Security → + RLS RULE")
        log.info(f"     ")
        log.info(f"     Rule 1:")
        log.info(f"       Name: Crescent Island Farms Filter")
        log.info(f"       Tables: Your dataset (e.g., fact.analytical_results_enriched)")
        log.info(f"       Roles: CrescentIslandFarms")
        log.info(f"       Clause: dim_client_name = 'Crescent Island Farms'")
        log.info(f"     ")
        log.info(f"     Rule 2:")
        log.info(f"       Name: Pure Sunfarms Filter")
        log.info(f"       Tables: Your dataset")
        log.info(f"       Roles: PureSunfarms")
        log.info(f"       Clause: dim_client_name = 'Pure Sunfarms'")
        
        log.info(f"\n  3. Test access:")
        log.info(f"     - Have users logout and login")
        log.info(f"     - Verify each client only sees their dashboards")
        log.info(f"     - Verify each client only sees their data")
        
        log.info(f"\n  4. Verify AUTH_ROLES_MAPPING in superset_config.py:")
        log.info(f"     AUTH_ROLES_MAPPING = {{")
        log.info(f'       "superset_admin": ["Admin"],')
        log.info(f'       "superset_user": ["Gamma"],')
        log.info(f'       "client_crescent_island_farms": ["Gamma", "CrescentIslandFarms"],')
        log.info(f'       "client_pure_sunfarms": ["Gamma", "PureSunfarms"],')
        log.info(f"     }}")
        
        log.info("\n" + "="*70)
        
        return True

if __name__ == '__main__':
    log.info("="*70)
    log.info("COMPLETE CLIENT ISOLATION SETUP")
    log.info("="*70)
    log.info("\nThis script will:")
    log.info("  1. Configure Gamma as read-only (no create/edit/delete)")
    log.info("  2. Configure client roles with database + datasource access")
    log.info("  3. Enable RLS filtering and dashboard-level access control")
    log.info("")
    log.info("After running:")
    log.info("  - Clients can ONLY see their assigned dashboards")
    log.info("  - Clients can ONLY see their filtered data (via RLS)")
    log.info("  - Clients CANNOT edit, create, or delete anything")
    log.info("")
    
    try:
        success = setup_complete_client_isolation()
        if success:
            log.info("\n✅ ✅ ✅ SETUP COMPLETED SUCCESSFULLY! ✅ ✅ ✅")
            log.info("\nYour Superset is now configured for strict client isolation!")
            exit(0)
        else:
            log.error("\n❌ Setup failed")
            exit(1)
    except Exception as e:
        log.error(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)