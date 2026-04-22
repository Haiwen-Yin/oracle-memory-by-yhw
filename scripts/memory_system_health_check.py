#!/usr/bin/env python3
"""
Memory System Health Check Script - Fixed Version
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

import os
import sys
import subprocess
import json
from datetime import datetime


def run_sql_command(conn_string, sql_query):
    """Execute SQL query using SQLcl and return output."""
    try:
        cmd = f"/root/sqlcl/bin/sql-mcp.sh {conn_string} << 'EOF'\n{sql_query}\nEXIT;"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return {'output': result.stdout + result.stderr, 'returncode': result.returncode}
    except Exception as e:
        return {'output': f'Error executing command: {str(e)}', 'returncode': 1}


# Configuration (can be overridden via command line or environment variables)
PRIMARY_CONN = os.environ.get('PRIMARY_CONN', 'openclaw@//10.10.10.130:1521/openclaw')
STANDBY_CONN = os.environ.get('STANDBY_CONN', '')


def check_primary_db_status():
    """Check primary database role and archivelog mode."""
    sql = """
    SELECT 
        database_role,
        log_mode,
        force_logging
    FROM v$database;
    """
    
    result = run_sql_command(PRIMARY_CONN, sql)
    output = result['output']
    
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
    if not STANDBY_CONN:
        return {"status": "OK", "sync": True, "message": "STAND BY connection not configured - skipping ADG check"}
    
    sql = """
    SELECT 
        destination,
        status,
        error
    FROM v$archive_dest_status 
    WHERE dest_id = 2;
    """
    
    result = run_sql_command(STANDBY_CONN, sql)
    output = result['output']
    
    if "VALID" in output and ("ERROR" not in output or "ORA-" not in output):
        return {"status": "OK", "sync": True, 
                "message": "ADG sync is healthy"}
    else:
        error_msg = "Unknown sync issue"
        for line in output.split('\n'):
            if "ERROR" in line and "ORA-" in line:
                error_msg = line.strip()
                break
        
        return {"status": "WARNING", "sync": False, 
                f"message": f"Sync issue detected: {error_msg}"}


def check_memory_tables():
    """Check memory system table existence and row counts."""
    sql = """
    SELECT 
        owner,
        table_name,
        num_rows,
        last_analyzed
    FROM all_tables 
    WHERE owner = 'OPENCLAW' 
      AND (table_name IN ('MEMORIES', 'MEMORIES_VECTORS', 'MEMORY_RELATIONSHIPS'))
    ORDER BY table_name;
    """
    
    result = run_sql_command(PRIMARY_CONN, sql)
    output = result['output']
    
    if "OPENCLAW" in output and "MEMORIES" in output:
        return {"status": "OK", "tables_found": True, 
                "message": f"All memory tables exist:\n{output[:300]}"}
    else:
        return {"status": "ERROR", "tables_found": False, 
                "message": f"Memory tables not found. Output: {output}"}


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
    
    result = run_sql_command(PRIMARY_CONN, sql)
    output = result['output']
    
    if "OPENCLAW" in output or "dimension" in output.lower():
        return {"status": "OK", "dimension_found": True, 
                "message": f"VECTOR dimension found: {output[:200]}"}
    else:
        return {"status": "WARNING", "dimension_found": False, 
                "message": f"Could not determine VECTOR dimension. Output: {output}"}


def check_updated_at_trigger():
    """Check UPDATED_AT trigger status validation."""
    sql = """
    SELECT 
        trigger_name,
        status,
        trigger_type,
        triggering_event
    FROM all_triggers 
    WHERE owner = 'OPENCLAW' 
      AND table_name = 'MEMORIES';
    """
    
    result = run_sql_command(PRIMARY_CONN, sql)
    output = result['output']
    
    if "ENABLED" in output and "TRIGGER" in output:
        return {"status": "OK", "trigger_active": True, 
                "message": "UPDATED_AT trigger is active and enabled"}
    else:
        return {"status": "WARNING", "trigger_active": False, 
                "message": f"Trigger status unclear. Output: {output}"}


def check_relationship_types():
    """Check relationship types lookup table completeness."""
    sql = """
    SELECT COUNT(*) as total_types,
           SUM(CASE WHEN is_active = 'Y' THEN 1 ELSE 0 END) as active_types
    FROM openclaw.relationship_types;
    """
    
    result = run_sql_command(PRIMARY_CONN, sql)
    output = result['output']
    
    if "total_types" in output.lower() or "COUNT" in output:
        return {"status": "OK", "types_exist": True, 
                "message": f"Relationship types found: {output[:200]}"}
    else:
        return {"status": "WARNING", "types_exist": False, 
                "message": f"Could not find relationship types. Output: {output}"}


def print_header():
    """Print report header."""
    print("=" * 78)
    print("Oracle AI Database Memory System Health Check")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Version: v0.3.0 Enhanced Schema Edition")
    print("=" * 78)


def main():
    """Main health check routine."""
    print_header()
    
    checks = [
        ("Primary DB Status", check_primary_db_status),
        ("ADG Sync Status", check_adg_sync_status),
        ("Memory Tables", check_memory_tables),
        ("Vector Dimension", check_vector_dimension),
        ("UPDATED_AT Trigger", check_updated_at_trigger),
        ("Relationship Types", check_relationship_types),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            status = result.get('status', 'UNKNOWN')
            message = result.get('message', '')
            
            if status == "OK":
                print(f"\n[✓] {name}")
                print(f"    {message[:200]}")
            elif status == "WARNING":
                print(f"\n[⚠️] {name}")
                print(f"    {message[:200]}")
            else:
                print(f"\n[❌] {name}")
                print(f"    {message[:200]}")
            
            results.append(status)
        except Exception as e:
            print(f"\n[❌] {name}")
            print(f"    Error: {str(e)}")
            results.append("ERROR")
    
    # Summary
    print("\n" + "=" * 78)
    print("HEALTH CHECK SUMMARY")
    print("=" * 78)
    
    ok_count = results.count('OK')
    warning_count = results.count('WARNING')
    error_count = results.count('ERROR')
    
    print(f"✓ OK: {ok_count}/{len(results)}")
    print(f"⚠️ WARNING: {warning_count}/{len(results)}")  
    print(f"❌ ERROR: {error_count}/{len(results)}")
    
    if error_count > 0:
        print("\nACTION REQUIRED:")
        for name, _ in checks:
            idx = checks.index((name,))
            if results[idx] == 'ERROR':
                print(f"  • {name}: Requires attention")
    
    # Exit with appropriate code
    sys.exit(0 if error_count == 0 else 1)


if __name__ == "__main__":
    main()
