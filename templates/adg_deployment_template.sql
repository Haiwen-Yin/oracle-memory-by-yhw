-- ============================================================================
-- Oracle AI Database Memory System - Production Deployment Template
-- Version: 0.3.0 Enhanced Schema Edition (ADG Configuration)
-- Author: Haiwen Yin (胖头鱼 🐟)
-- Purpose: Active Data Guard high availability setup for memory system
-- Usage: sql-mcp.sh openclaw@//host:port/service @adg_deployment_template.sql
-- ============================================================================

SET PAGESIZE 100 LINESIZE 200 FEEDBACK OFF VERIFY OFF;

-- ============================================
-- PART 1: PRIMARY DATABASE CONFIGURATION
-- ============================================

-- Step 1.1: Verify current database role and archivelog mode
SELECT '=== Primary DB Status ===' AS section FROM DUAL;
SELECT 
    database_role,
    log_mode,
    force_logging
FROM v$database;

-- Expected output: PRIMARY | ARCHIVELOG | YES (or NO - we'll enable it)

-- Step 1.2: Enable forced logging (ensure data consistency for ADG)
ALTER DATABASE FORCE LOGGING;

-- Step 1.3: Verify force logging is enabled
SELECT '=== Force Logging Status ===' AS section FROM DUAL;
SELECT database_role, force_logging FROM v$database;

-- Step 1.4: Create Standby Redo Logs (SRLs)
-- Number should be at least equal to online redo logs + 1 per thread
SELECT '=== Current Online Redo Log Groups ===' AS section FROM DUAL;
SELECT group#, type, bytes/1024/1024 as size_mb, status 
FROM v$logfile 
GROUP BY group#, type, bytes, status;

-- Add SRLs (example: 3 additional groups for single instance)
ALTER DATABASE ADD STANDBY LOGFILE GROUP 10 SIZE 512M;
ALTER DATABASE ADD STANDBY LOGFILE GROUP 11 SIZE 512M;
ALTER DATABASE ADD STANDBY LOGFILE GROUP 12 SIZE 512M;

-- Verify SRLs created
SELECT '=== Standby Redo Logs ===' AS section FROM DUAL;
SELECT group#, type, status FROM v$standby_log WHERE group# >= 10;

-- Step 1.5: Configure archive destination parameters
ALTER SYSTEM SET LOG_ARCHIVE_CONFIG='DG_CONFIG=(openclaw, openclaw_standby)' SCOPE=BOTH;
ALTER SYSTEM SET LOG_ARCHIVE_DEST_1='LOCATION=USE_DB_RECOVERY_FILE_DEST VALID_FOR=(ALL_LOGFILES,ALL_ROLES) SCOPE=BOTH';
ALTER SYSTEM SET LOG_ARCHIVE_DEST_2='SERVICE=openclaw_standby ARCH SYNC AFFIRM MAX_FAIL=3 VALID_FOR=(ONLINE_LOGFILES,PRIMARY_ROLE) SCOPE=BOTH';

-- Step 1.6: Enable flashback database (optional but recommended for quick recovery)
SELECT '=== Flashback Status ===' AS section FROM DUAL;
SELECT flashback_on FROM v$database;

ALTER DATABASE FLASHBACK ON;

-- ============================================
-- PART 2: STANDBY DATABASE CONFIGURATION  
-- ============================================

-- Step 2.1: Verify standby database role (run on standby server)
SELECT '=== Standby DB Status ===' AS section FROM DUAL;
SELECT 
    database_role,
    log_mode,
    force_logging
FROM v$database;

-- Expected output: PHYSICAL STANDBY | ARCHIVELOG | YES

-- Step 2.2: Enable forced logging on standby (if not already)
ALTER DATABASE FORCE LOGGING;

-- Step 2.3: Configure archive destinations on standby
ALTER SYSTEM SET LOG_ARCHIVE_CONFIG='DG_CONFIG=(openclaw, openclaw_standby)' SCOPE=BOTH;
ALTER SYSTEM SET LOG_ARCHIVE_DEST_1='LOCATION=USE_DB_RECOVERY_FILE_DEST VALID_FOR=(ALL_LOGFILES,ALL_ROLES) SCOPE=BOTH';
ALTER SYSTEM SET LOG_ARCHIVE_DEST_2='SERVICE=openclaw ARCH SYNC AFFIRM MAX_FAIL=3 VALID_FOR=(STANDBY_LOGFILE,SUBSTANTIARY_ROLE) SCOPE=BOTH';

-- Step 2.4: Enable Real-Time Apply (MTA - Managed Standby Apply)
-- This allows queries on standby while applying redo from primary
ALTER DATABASE RECOVER MANAGED STANDBY DATABASE USING CURRENT LOGFILE DISCONNECT FROM SESSION;

-- ============================================
-- PART 3: TNSNAMES.ORA CONFIGURATION  
-- ============================================

/* 
Create/edit /opt/oracle/product/26ai/network/admin/tnsnames.ora on BOTH servers:

openclaw = (DESCRIPTION=
  (ADDRESS=(PROTOCOL=tcp)(HOST=db-primary.example.com)(PORT=1521))
  (CONNECT_DATA=(SERVICE_NAME=openclaw))
)

openclaw_standby = (DESCRIPTION=
  (ADDRESS=(PROTOCOL=tcp)(HOST=db-standby.example.com)(PORT=1521))
  (CONNECT_DATA=(SERVICE_NAME=openclaw_standby))
)

-- Optional: Add failover configuration
openclaw_failsafe = (DESCRIPTION=
  (LOAD_BALANCE=yes)
  (FAILOVER=on)
  (ADDRESS=(PROTOCOL=tcp)(HOST=db-primary.example.com)(PORT=1521))
  (ADDRESS=(PROTOCOL=tcp)(HOST=db-standby.example.com)(PORT=1521))
  (CONNECT_DATA=(SERVICE_NAME=openclaw))
)
*/

-- ============================================
-- PART 4: MONITORING & HEALTH CHECK  
-- ============================================

-- Step 4.1: Check ADG sync status from primary
SELECT '=== ADG Sync Status ===' AS section FROM DUAL;
SELECT 
    destination,
    status,
    error,
    applied_time
FROM v$archive_dest_status 
WHERE dest_id = 2;

-- Step 4.2: Check standby lag (minutes behind primary)
SELECT '=== Standby Lag ===' AS section FROM DUAL;
SELECT 
    sequence#,
    applied,
    ROUND((SYSDATE - TO_DATE(first_time, 'YYYY-MM-DD HH24:MI:SS')) * 24 * 60, 2) AS minutes_lag
FROM v$standby_log 
ORDER BY sequence# DESC;

-- Step 4.3: Check real-time apply status from standby
SELECT '=== Real-Time Apply Status ===' AS section FROM DUAL;
SELECT process, status, thread#, sequence#, block#, blocks FROM v$managed_standby WHERE process LIKE 'MRP%';

-- ============================================
-- PART 5: ROLLBACK & FAILOVER PROCEDURES  
-- ============================================

-- Step 5.1: Stop managed standby apply (for maintenance)
ALTER DATABASE RECOVER MANAGED STANDBY DATABASE CANCEL;

-- Step 5.2: Convert physical standby to primary (manual failover)
ALTER DATABASE ACTIVATE PHYSICAL STANDBY DATABASE;

-- Step 5.3: Open database in read/write mode after activation
ALTER DATABASE OPEN;

-- ============================================
END OF DEPLOYMENT TEMPLATE  
============================================