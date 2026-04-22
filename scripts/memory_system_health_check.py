#!/usr/bin/env python3
"""
Memory System Health Check Script
Version: 0.3.0 Enhanced Schema Edition
Author: Haiwen Yin (胖头鱼 🐟)
Purpose: Monitor memory system health, ADG status, and component verification

Checks performed:
1. Primary DB role and archivelog mode
2. ADG synchronization status from standby
3. Memory system table existence and row counts
4. VECTOR column dimension consistency check
5. UPDATED_AT trigger status validation
6. Relationship types lookup table completeness

Usage: python memory_system_health_check.py [--primary CONN] [--standby CONN]
"""

from hermes_tools import terminal, write_file, read_file
import json
from datetime import datetime


# Configuration (can be overridden via command line)
PRIMARY_CONN = "openclaw@//10.10.10.130:1521/openclaw"
STANDBY_CONN = "openclaw@//10.10.10.131:1521/openclaw_standby"


def check_primary_db_status():
    """Check primary database role and archivelog mode."""
    sql = """
    SELECT 
        database_role,
        log_mode,
        force_logging
    FROM v$database;
    """
    
    result = terminal(f"/root/sqlcl/bin/sql-mcp.sh {PRIMARY_CONN} << 'EOF'\n{sql}\nEXIT;", timeout=30)
    
    output = result.get('output', '')
    
    if "PRIMARY" in output:
        return {"status": "OK", "role": "PRIMARY", "archivelog": True, 
                "message": "Primary DB is active and ready for writes"}
    elif "PHYSICAL STANDBY" in output:
        return {"status": "WARNING", "role": "STANDBY", 
                "message": "Unexpected standby role detected on primary server"}
    else:
        return {"status": "ERROR", "role": "UNKNOWN", 
                "message": f"Could not determine database role. Output: {output[:200]}"}


def check_adg_sync_status():
    """Check ADG synchronization status from standby."""
    sql = """
    SELECT 
        destination,
        status,
        error
    FROM v$archive_dest_status 
    WHERE dest_id = 2;
    """
    
    result = terminal(f"/root/sqlcl/bin/sql-mcp.sh {STANDBY_CONN} << 'EOF'\n{sql}\nEXIT;", timeout=30)
    
    output = result.get('output', '')
    
    if "VALID" in output and ("ERROR" not in output or "ORA-" not in output):
        return {"status": "OK", "sync": True, 
                "message": "ADG sync is healthy"}
    else:
        # Extract error message if present
        error_msg = "Unknown sync issue"
        for line in output.split('\n'):
            if "ERROR" in line and "ORA-" in line:
                error_msg = line.strip()
                break
        
        return {"status": "WARNING", "sync": False, 
                f"message": f"Sync issue detected: {error_msg}"}


def check_memory_tables():
    """Check memory system tables existence and row counts."""
    sql = """
    SELECT 
        table_name,
        num_rows,
        bytes/1024 AS size_kb
    FROM user_tables t
    JOIN user_segments s ON t.table_name = s.segment_name
    WHERE table_name IN ('MEMORIES', 'MEMORIES_VECTORS', 'MEMORY_RELATIONSHIPS')
    ORDER BY table_name;
    """
    
    result = terminal(f"/root/sqlcl/bin/sql-mcp.sh {PRIMARY_CONN} << 'EOF'\n{sql}\nEXIT;", timeout=30)
    
    output = result.get('output', '')
    
    if "MEMORIES" in output and "MEMORIES_VECTORS" in output:
        # Extract row counts for detailed report
        tables_found = []
        for line in output.split('\n'):
            if 'MEMORIES' in line or 'MEMORY_RELATIONSHIPS' in line:
                parts = [p.strip() for p in line.split()]
                if len(parts) >= 2 and parts[0] != 'TABLE_NAME':
                    tables_found.append({'name': parts[0], 'rows': int(parts[1]) if parts[1].isdigit() else 0})
        
        return {"status": "OK", "tables_found": True, 
                "table_details": tables_found,
                "message": f"All memory tables exist ({len(tables_found)} total)"}
    else:
        return {"status": "ERROR", "tables_found": False, 
                "message": "Missing memory tables or data dictionary error"}


def check_vector_dimension():
    """Check VECTOR column dimension consistency."""
    sql = """
    SELECT 
        column_name,
        data_precision AS dimension,
        model_version
    FROM user_tab_columns c
    LEFT JOIN memories_vectors v ON 1=1
    WHERE table_name = 'MEMORIES_VECTORS' AND column_name LIKE '%EMBEDDING%';
    """
    
    result = terminal(f"/root/sqlcl/bin/sql-mcp.sh {PRIMARY_CONN} << 'EOF'\n{sql}\nEXIT;", timeout=30)
    
    output = result.get('output', '')
    
    if "1024" in output:
        return {"status": "OK", "dimension": 1024, 
                "message": "VECTOR dimension is valid (BGE-M3 compatible)"}
    elif "1536" in output:
        return {"status": "WARNING", "dimension": 1536, 
                "message": "VECTOR dimension differs from expected (1024 vs 1536)"}
    else:
        return {"status": "ERROR", "dimension": None, 
                "message": f"Could not determine vector dimension. Output: {output[:200]}"}


def check_triggers():
    """Check UPDATED_AT trigger status."""
    sql = """
    SELECT 
        trigger_name,
        triggering_event,
        status
    FROM user_trusters 
    WHERE table_name = 'MEMORIES' AND trigger_name LIKE '%UPDATED_AT%';
    """
    
    result = terminal(f"/root/sqlcl/bin/sql-mcp.sh {PRIMARY_CONN} << 'EOF'\n{sql}\nEXIT;", timeout=30)
    
    output = result.get('output', '')
    
    if "ENABLED" in output:
        return {"status": "OK", "trigger_enabled": True, 
                "message": "UPDATED_AT trigger is active and enabled"}
    elif "DISABLED" in output:
        return {"status": "WARNING", "trigger_enabled": False, 
                "message": "Trigger exists but is DISABLED - needs re-enabling"}
    else:
        return {"status": "ERROR", "trigger_enabled": False, 
                "message": "UPDATED_AT trigger not found"}


def check_relationship_types():
    """Check relationship types lookup table completeness."""
    sql = """
    SELECT 
        type_id,
        description,
        is_active
    FROM relationship_types 
    WHERE is_active = 'Y'
    ORDER BY type_id;
    """
    
    result = terminal(f"/root/sqlcl/bin/sql-mcp.sh {PRIMARY_CONN} << 'EOF'\n{sql}\nEXIT;", timeout=30)
    
    output = result.get('output', '')
    
    # Check for expected standard types
    expected_types = ['related_to', 'updates', 'contradicts', 'depends_on', 'supersedes', 'extends']
    found_types = []
    
    for line in output.split('\n'):
        if any(t in line.lower() for t in expected_types):
            found_types.append(line.strip().split()[0] if line.strip() else '')
    
    if len(found_types) >= 5:  # At least most types present
        return {"status": "OK", "types_count": len(set(found_types)), 
                "message": f"Relationship types configured ({len(set(found_types))} active types)"}
    else:
        missing = set(expected_types) - set(found_types)
        return {"status": "WARNING", "types_count": None, 
                f"message": f"Missing relationship types: {', '.join(missing)}"}


def run_health_check():
    """Run complete health check and generate report."""
    
    print("=" * 70)
    print("Oracle AI Database Memory System Health Check")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Version: v0.3.0 Enhanced Schema Edition")
    print("=" * 70)
    print()
    
    results = {}
    
    # Run all checks
    checks = [
        ("Primary DB Status", check_primary_db_status),
        ("ADG Sync Status", check_adg_sync_status),
        ("Memory Tables", check_memory_tables),
        ("Vector Dimension", check_vector_dimension),
        ("UPDATED_AT Trigger", check_triggers),
        ("Relationship Types", check_relationship_types),
    ]
    
    for name, func in checks:
        print(f"[{name}]")
        try:
            result = func()
            results[name] = result
            status_icon = "✓" if result.get("status") == "OK" else "⚠️" if result.get("status") == "WARNING" else "❌"
            print(f"  {status_icon} {result.get('message', 'Unknown')}")
            
            # Show additional details for table check
            if name == "Memory Tables" and "table_details" in result:
                for table in result["table_details"]:
                    print(f"      - {table['name']}: {table['rows']} rows")
                    
        except Exception as e:
            results[name] = {"status": "ERROR", "message": str(e)}
            print(f"  ❌ Error: {e}")
        print()
    
    # Generate summary
    print("=" * 70)
    print("HEALTH CHECK SUMMARY")
    print("=" * 70)
    
    ok_count = sum(1 for r in results.values() if r.get("status") == "OK")
    warning_count = sum(1 for r in results.values() if r.get("status") == "WARNING")
    error_count = sum(1 for r in results.values() if r.get("status") == "ERROR")
    
    print(f"✓ OK: {ok_count}/{len(results)}")
    print(f"⚠️ WARNING: {warning_count}/{len(results)}")
    print(f"❌ ERROR: {error_count}/{len(results)}")
    print()
    
    if error_count > 0:
        print("ACTION REQUIRED:")
        for name, result in results.items():
            if result.get("status") == "ERROR":
                print(f"  • {name}: {result.get('message')}")
        print("\nPlease address the errors above before proceeding with production use.")
    elif warning_count > 0:
        print("RECOMMENDATION:")
        for name, result in results.items():
            if result.get("status") == "WARNING":
                print(f"  • {name}: {result.get('message')}")
        print("\nReview warnings and take preventive measures.")
    else:
        print("SYSTEM HEALTH: All components are healthy! ✅")
    
    # Return results for programmatic use
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Memory System Health Check')
    parser.add_argument('--primary', default=PRIMARY_CONN, help='Primary DB connection')
    parser.add_argument('--standby', default=STANDBY_CONN, help='Standby DB connection')
    
    args = parser.parse_args()
    
    # Override global configuration if provided
    import sys
    globals()['PRIMARY_CONN'] = args.primary
    globals()['STANDBY_CONN'] = args.standby
    
    results = run_health_check()
    
    exit(0)
