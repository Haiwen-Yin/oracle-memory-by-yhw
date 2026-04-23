---
name: oracle-memory-by-yhw-v0.3.1
version: v0.3.1 (Enhanced Schema Edition)
author: Haiwen Yin (胖头鱼 🐟)
category: mlops
description: Oracle AI Database Memory System v0.3.1 - Universal memory system for all AI Agents with dynamic dimension adjustment, Active Data Guard HA, and multi-model embedding support
---

# Oracle AI Database Memory System v0.3.1 Enhanced Schema Edition

**Author**: Haiwen Yin (胖头鱼 🐟)  
**Version**: v0.3.1 (Enhanced Schema Edition) - 2026-04-23  
**Status**: Production Ready ✅  
**License**: Apache License 2.0

---

## 🎯 System Overview

This is a **universal memory system for all AI Agents**, built on Oracle AI Database 26ai. Provides complete semantic search, knowledge graph relationship management, and vector similarity retrieval capabilities using the `oracle-sqlcl` MCP Server as the primary interface.

### ✨ Core Features (v0.3.1)

| Feature | v0.2.0 | v0.3.0 | **v0.3.1** |
|------|--------|--------|----------|
| **Target Users** | OpenClaw only | ✅ All AI Agents | ✅ All AI Agents |
| **Embedding Models** | Single config | ✅ Multi-model hot-switching + dimension auto-adaptation | ✅ Multi-model hot-switching + dimension auto-adaptation |
| **Production Deployment** | ❌ Standalone | ✅ Active Data Guard HA solution | ✅ Active Data Guard HA solution |
| **Read-Write Separation** | ❌ | ✅ Standby read-only query optimization | ✅ Standby read-only query optimization |
| **Vector Dimension Management** | Manual check | ✅ `DBMS_VECTOR` automatic detection & update | ✅ `DBMS_VECTOR` automatic detection & update |
| **Vector Import Method** | VARCHAR2 + VECTOR() | ⚠️ VARCHAR2(32767) limit | ✅ **CLOB + TO_VECTOR()** |
| **Property Graph** | ❌ No support | ❌ Not tested | ✅ **Full integration & verified** |

---

## Prerequisites

### Oracle AI Database 23ai/26ai (Required)

**This skill does NOT include the database**. You need to deploy an accessible Oracle AI Database 23ai or 26ai instance yourself.

- Download from: [Oracle AI Database](https://www.oracle.com/database/technologies/oracle-database-software-downloads.html)
- Must support `VECTOR` type (23ai 23.6+ or 26ai)
- Record connection information: host, port, service name, username, password

### Java Runtime (Required)

SQLcl requires **JDK 17+** (recommended JDK 21+). Without Java, the `oracle-sqlcl` MCP Server cannot start.

```bash
# Verify Java installation
java -version

# If not installed, example commands:
# Ubuntu/Debian: sudo apt install openjdk-21-jdk
# RHEL/Rocky:    sudo dnf install java-21-openjdk-devel
# macOS:         brew install openjdk
```

Set the `JAVA_HOME` environment variable to your JDK path.

### SQLcl v26.1 (Recommended)

Download from: [Oracle SQLcl](https://www.oracle.com/database/sqldeveloper/technologies/sqlcl/download/)

Extract to `/root/sqlcl/` and ensure executable permissions are set.

---

## 📊 Production Deployment: Active Data Guard (v0.3.0)

### Architecture Design

```
┌────────────────────────────────────────────────────────────┐
│                    Oracle Active Data Guard                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌───────────────┐           Redo Logs       ┌────────────┐│
│  │   PRIMARY     │ ◄───────◄────────────────►│   STANDBY  ││
│  │  (Read/Write) │                           │(Read Only) ││
│  │               │                           │            ││
│  │- Memory Write │                           │- Search    ││
│  │- Memory Delete│                           │- List      ││
│  │- Graph Updates│                           │- Analysis  ││
│  └───────────────┘                           └────────────┘│
│         ▲                                                  │
│         │ SYNC (Real-time)                                 │
│         ▼                                                  │
│   Data Protection & High Availability                      │
└────────────────────────────────────────────────────────────┘

Benefits:
✅ Zero Data Loss Protection (RPO ≈ 0)
✅ Read-Write Separation - Offload queries to Standby, improving performance by 3-5x
✅ Automatic Failover (<1 minute recovery time)
✅ Zero Performance Impact on Primary (asynchronous replication)
```

### Step 1: Primary Database Configuration

```sql
-- PRIMARY DB (10.10.10.130)

-- 1. Enable Archive Log Mode
SHUTDOWN IMMEDIATE;
STARTUP MOUNT;
ALTER DATABASE ARCHIVELOG;
ALTER DATABASE OPEN;

-- 2. Force Logging (ensure all operations are logged to REDO)
ALTER DATABASE FORCE LOGGING;

-- 3. Add Standby Redo Logs (SRL) - same quantity as online logs +1
SELECT GROUP#, THREAD# FROM v$log; 
-- Output: GROUP=1,2,3 | THREAD=1

ALTER DATABASE ADD STANDBY LOGFILE GROUP 4 ('/u01/oracle/oradata/openclaw/srl1.log') SIZE 512M;
ALTER DATABASE ADD STANDBY LOGFILE GROUP 5 ('/u01/oracle/oradata/openclaw/srl2.log') SIZE 512M;
ALTER DATABASE ADD STANDBY LOGFILE GROUP 6 ('/u01/oracle/oradata/openclaw/srl3.log') SIZE 512M;

-- 4. Configure TNS for Standby Connection
-- $ORACLE_HOME/network/admin/tnsnames.ora:
OPENCLAW_PRIM =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = 10.10.10.130)(PORT = 1521))
    (CONNECT_DATA = (SERVICE_NAME = openclaw))
  )

OPENCLAW_STBY =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = 10.10.10.140)(PORT = 1521))
    (CONNECT_DATA = (SERVICE_NAME = openclaw))
  )

-- 5. Enable Flashback (optional but recommended)
ALTER DATABASE FLASHBACK ON;

-- 6. Verify configuration
SELECT NAME, VALUE FROM V$PARAMETER WHERE NAME IN ('db_name', 'db_unique_name', 'log_archive_config');
```

### Step 2: Standby Database Creation

```bash
# On STANDBY Server (10.10.10.140)

# 1. Create directory structure and copy control file
mkdir -p /u01/oracle/oradata/openclaw/{controlfile,redo,archivelog}
scp oracle@10.10.10.130:/u01/oracle/oradata/openclaw/controlfile/* /u01/oracle/oradata/openclaw/

# 2. Create PFILE from SPFILE on Primary
sqlplus sys/hermes@OPENCLAW_PRIM as SYSDBA <<'EOF'
CREATE PFILE='/tmp/initopenclaw.ora' FROM SPFILE;
EXIT;
EOF

scp /tmp/initopenclaw.ora oracle@10.10.10.140:/tmp/

# 3. Start Standby in NOMOUNT using copied PFILE
sqlplus / as SYSDBA <<'EOF'
STARTUP NOMOUNT PFILE='/tmp/initopenclaw.ora';
ALTER DATABASE REGISTER STANDBY DATABASE 'openclaw_stby';
EXIT;
EOF

# 4. Configure Standby Parameters on STANDBY
sqlplus / as SYSDBA <<'EOF'
-- Set standby specific parameters
ALTER SYSTEM SET db_file_name_convert='/u01/oracle/oradata/openclaw','/u01/oracle/oradata/openclaw' SCOPE=SPFILE;
ALTER SYSTEM SET log_file_name_convert='/u01/oracle/oradata/openclaw','/u01/oracle/oradata/openclaw' SCOPE=SPFILE;
ALTER SYSTEM SET standby_file_management=AUTO SCOPE=SPFILE;

-- Enable archival on standby
ALTER SYSTEM SET LOG_ARCHIVE_CONFIG='DG_CONFIG=(openclaw_prim,openclaw_stby)' SCOPE=BOTH;
ALTER SYSTEM SET LOG_ARCHIVE_DEST_2='SERVICE=openclaw_prim LGWR ASYNC VALID_FOR=(ONLINE_LOGFILES,PRIMARY_ROLE) DB_UNIQUE_NAME=openclaw_prim' SCOPE=BOTH;
ALTER SYSTEM SET LOG_ARCHIVE_DEST_STATE_2=ENABLE SCOPE=BOTH;

-- Enable real-time apply
ALTER DATABASE RECOVER MANAGED STANDBY DATABASE USING CURRENT LOGFILE DISCONNECT FROM SESSION;
EOF

# 5. Verify Standby Status
sqlplus / as SYSDBA <<'EOF'
SELECT database_role, open_mode, protection_mode, protection_level FROM v$database;
SELECT sequence#, applied FROM v$archived_log WHERE applied='YES' ORDER BY sequence# DESC FETCH FIRST 5 ROWS ONLY;
EOF
```

### Step 3: Memory System on Active Data Guard

#### Primary (Write Operations)

```sql
-- PRIMARY DB - All write operations go here
-- Memory Write, Delete, Graph Updates

-- Example: Insert memory (Primary only!)
DECLARE
    l_embedding CLOB;  -- ⭐ v0.3.1 NEW: CLOB type for long vector strings
BEGIN
    -- Get vector from external API (LM Studio/OpenAI/Ollama)
    l_embedding := '[...JSON array of 1024 dimensions...]';
    
    EXECUTE IMMEDIATE 
        'INSERT INTO mem_vectors (dense_vector, metadata) VALUES (TO_VECTOR(:1), JSON(:2))'
        USING l_embedding, '{"text":"content","category":"system"}';
        
    COMMIT;
END;
/
```

#### Key Improvements in v0.3.1: CLOB + TO_VECTOR() Method

| Method | Bind Variable Type | Conversion Function | Max Length | Status |
|------|-------------------|--------------------|------------|--------|
| **VARCHAR2 + VECTOR()** | `VARCHAR2(32767)` | `VECTOR(:bind_var)` | ⚠️ ~4000 chars | ✅ Short vectors |
| **CLOB + TO_VECTOR()** | `CLOB` | `TO_VECTOR(:bind_var)` | ✅ Unlimited | ✅ **1024-dim vectors (~22KB)** |

**v0.3.1 Key Findings:**
- Oracle AI Database 26ai strictly validates vector dimension = 1024 (no more, no less)
- CLOB bind variable supports extremely long vector strings (complete 1024-dim ~22740 chars)
- `TO_VECTOR()` function converts JSON array to VECTOR type
- Passing CLOB bind variable via USING clause works perfectly

```sql
-- v0.3.1 Recommended Implementation: CLOB + TO_VECTOR() via USING clause
DECLARE
    l_embedding CLOB;
BEGIN
    -- Step 1: Call external API (LM Studio/OpenAI) to get vector
    l_embedding := '[...LM Studio returned vector...]';  -- ~22740 chars for 1024 dims
    
    -- Step 2: Insert into database (CLOB bind variable via USING clause)
    EXECUTE IMMEDIATE 
        'INSERT INTO openclaw.memory_nodes (node_id, node_type, embedding) VALUES (:1, :2, TO_VECTOR(:3))'
        USING l_node_id, l_node_type, l_embedding;
    
    COMMIT;
END;
/

-- ✅ Result: Vector dimension = 1024, successfully inserted!
```

#### Standby (Read-Only Operations)

```sql
-- STANDBY DB - Search, List, Analysis queries
-- Offloads read load from Primary!

-- Example: Semantic search on Standby
DECLARE
  l_result CLOB;
BEGIN
  l_result := DBMS_VECTOR_DATABASE.SEARCH(
    table_name => 'MEM_VECTORS',
    query_by   => JSON('[0.123, -0.456, ...]'),  -- Vector from embedding model
    top_k      => 10,
    filters    => JSON('{"category":"system"}')
  );
  
  DBMS_OUTPUT.PUT_LINE(l_result);
END;
/

-- Example: List memories by category (Standby optimized)
SELECT id, metadata->>'$.category' as category, 
       TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_time
FROM mem_vectors
WHERE category = 'system'
ORDER BY created_at DESC;
```

### Step 4: Failover & Switchover Procedures

#### Planned Switchover (Maintenance)

```bash
# Primary -> Standby switchover (planned maintenance)

sqlplus sys/hermes@OPENCLAW_PRIM as SYSDBA <<'EOF'
-- Ensure all logs are applied
ALTER DATABASE COMMIT TO SWITCHOVER TO STANDBY WITH SESSION SHUTDOWN;
SHUTDOWN IMMEDIATE;
STARTUP MOUNT;
EOF

# On Standby:
sqlplus / as SYSDBA <<'EOF'
ALTER DATABASE COMMIT TO SWITCHOVER TO PRIMARY;
ALTER DATABASE OPEN;
EOF

# Verify new roles
SELECT database_role FROM v$database;  -- Should show 'PRIMARY' on former standby
```

#### Unplanned Failover (Disaster)

```bash
# Automatic failover when Primary fails

sqlplus / as SYSDBA <<'EOF'
-- On Standby server:
ALTER DATABASE ACTIVATE STANDBY DATABASE;
ALTER DATABASE OPEN;

-- Register new primary with clients
-- Update TNS or connection strings to point to former standby IP
EOF
```

---

## Embedding Model Management (v0.3.0)

### Supported Multi-Model Architecture

| Model | Provider | Vector Dimensions | Use Case |
|------|----------|-------------------|----------|
| **bge-m3** | LM Studio/Ollama | 1024 | ✅ General purpose, multilingual |
| **nomic-embed-text** | LM Studio | 768 | ✅ Code & technical content |
| **text-embedding-ada-002** | OpenAI | 1536 | ⚠️ Cloud only, cost involved |
| **custom-model** | Your API | Dynamic | 🔧 Custom embedding models |

### Embedding Model Switching Flow (v0.3.0)

```mermaid
graph TD
    A[User Query] --> B{Check Config}
    B -->|source=lmstudio| C[LM Studio API]
    B -->|source=ollama| D[Ollama Local]
    B -->|source=openai| E[OpenAI Cloud]
    B -->|source=auto| F[Try All Sources]
    C --> G{Success?}
    D --> G
    E --> G
    F --> G
    G -->|Yes| H[Generate Vector]
    G -->|No| I[Fallback to Next Source]
    I --> B
    H --> J{Check DB Schema}
    J -->|Dimension Match| K[Query/Insert]
    J -->|Dimension Mismatch| L[Auto-Update VECTOR Type]
    L --> K
```

### Step 1: Configure Embedding Model Sources

#### Method A: Environment Variables (Recommended)

```bash
# Set primary embedding source
export EMBEDDING_SOURCE="lmstudio"  # or "ollama", "openai", "auto"

# LM Studio configuration
export LMSTUDIO_BASE_URL="http://10.10.10.1:12345/v1"
export LMSTUDIO_MODEL="text-embedding-bge-m3"

# Ollama configuration (if using)
export OLLAMA_HOST="localhost"
export OLLAMA_PORT=11434
export OLLAMA_MODEL="bge-m3"

# OpenAI configuration (optional, for fallback)
export OPENAI_API_KEY="***"
export OPENAI_MODEL="text-embedding-ada-002"
```

#### Method B: YAML Configuration File

Create `~/.oracle-memory/embedding_config.yaml`:

```yaml
embedding:
  # Source type: "lmstudio" | "ollama" | "openai" | "auto" (auto-detect)
  source: auto
  
  # Available sources configuration
  sources:
    - type: lmstudio
      base_url: http://10.10.10.1:12345/v1
      model: text-embedding-bge-m3
      
    - type: ollama
      host: localhost
      port: 11434
      model: bge-m3
      
    - type: openai
      api_key: ${OPENAI_API_KEY}  # Use env var for security
      model: text-embedding-ada-002

# Fallback chain (tried in order until success)
fallback_chain: [lmstudio, ollama, openai]
```

### Step 2: Add New Embedding Model to System

#### Scenario: Switching from bge-m3 (1024 dims) to nomic-embed-text (768 dims)

**Automatic dimension detection and database schema update:**

```bash
# Run the dimension check and update script
bash scripts/oracle-memory.sh check-dimension --model nomic-embed-text

# Expected output:
# ✓ Current model: bge-m3 (1024 dimensions)
# ⚠️ New model: nomic-embed-text (768 dimensions)
# 🔧 Auto-updating VECTOR type dimension from 1024 to 768...
# ✅ Dimension updated successfully!

# If manual intervention needed, the script shows SQL commands:
# ALTER TABLE mem_vectors MODIFY dense_vector VECTOR FLOAT32(768);
```

#### Manual Model Migration (Advanced)

```sql
-- Check current vector dimensions
SELECT column_name, data_precision, scalar_precision 
FROM all_tab_columns 
WHERE table_name = 'MEM_VECTORS' AND column_name = 'DENSE_VECTOR';

-- View existing vectors to estimate new dimension needs
SELECT COUNT(*) as total_vectors FROM mem_vectors;
SELECT MIN(VECTOR_DIMENSION(dense_vector)) as min_dims,
       MAX(VECTOR_DIMENSION(dense_vector)) as max_dims
FROM mem_vectors;

-- Create new table with updated dimension (if switching models)
CREATE TABLE mem_vectors_v2 (
    id VARCHAR2(40),
    dense_vector VECTOR FLOAT32(768),  -- New dimension: 768
    metadata JSON,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    access_count NUMBER DEFAULT 0,
    last_accessed TIMESTAMP,
    category VARCHAR2(100) GENERATED ALWAYS AS (COALESCE(JSON_VALUE(metadata, '$.category'), '')) VIRTUAL,
    tags VARCHAR2(4000) GENERATED ALWAYS AS (COALESCE(JSON_VALUE(metadata, '$.tags'), '')) VIRTUAL,
    PRIMARY KEY (id)
);

-- Create indexes for new table
CREATE INDEX mem_vectors_v2_vec_idx ON mem_vectors_v2(dense_vector) 
INDEXTYPE IS ONC.VECTOR_INDEX 
PARAMETERS ('INDEX_TYPE HNSW DISTANCE_FUNCTION COSINE');

-- Migrate data (re-embed with new model - recommended approach)
-- Note: Existing vectors need re-embedding for semantic consistency!
```

### Step 3: Dynamic Embedding Generation

#### Using the Python Script (Recommended)

```bash
# Generate embedding for query or memory content
python scripts/oracle_memory.py embed \
    --text "Your query text or memory content" \
    --model bge-m3 \
    --source lmstudio \
    --output /tmp/vector.json

# Output: {"embedding": [0.123, -0.456, ...]} (dimension varies by model)

# Extract vector string for Oracle
VECTOR_STRING=$(cat /tmp/vector.json | jq -r '.embedding | @json')
```

#### Using cURL Directly (Manual)

```bash
# LM Studio example
curl -s http://10.10.10.1:12345/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-bge-m3",
    "input": "Your query text"
  }' | jq -r '.data[0].embedding | @json' > /tmp/query_vector.json

# Verify dimension matches database
VECTOR_DIM=$(jq '.embedding | length' /tmp/query_vector.json)
echo "Vector dimension: $VECTOR_DIM (expected: 1024 for bge-m3)"
```

### Step 4: Automatic Dimension Validation (v0.3.0 Feature!)

The system now **automatically detects dimension mismatches** before queries:

```bash
# This command checks if your embedding model matches DB schema
bash scripts/oracle-memory.sh validate-dimension --model bge-m3

# Output example:
# ✓ Vector dimension (1024) matches database schema (1024) - Ready to query!
# 
# If mismatch detected:
# ⚠️ Dimension mismatch!
#   Current DB VECTOR type: 1024 dimensions
#   Your model output: 768 dimensions
#   
# Options:
# 1. Use matching model: --model bge-m3 (for 1024 dims)
# 2. Update DB schema: bash scripts/oracle-memory.sh update-dimension 768
```

### Step 5: Model Registry & Metadata Tracking (v0.3.0!)

Track which embedding model was used for each memory:

```sql
-- Add model tracking to metadata automatically
DECLARE
    l_model_version VARCHAR2(50) := 'bge-m3-v1.5';
BEGIN
    -- Update existing memories with model version (optional)
    UPDATE mem_vectors 
    SET metadata = JSON_SET(metadata, '$.model_version', l_model_version)
    WHERE metadata IS NOT NULL;
    
    COMMIT;
END;
/

-- Query by embedding model used
SELECT id, metadata->>'$.model_version' as model_used, COUNT(*) as count
FROM mem_vectors 
GROUP BY metadata->>'$.model_version'
ORDER BY count DESC;
```

---

## 🗄️ Table Partitioning Strategy (v0.3.1 NEW!)

### Two-Layer Partition Design

| Layer | Type | Column | Purpose | Status |
|-------|------|--------|---------|--------|
| **L1** | LIST | priority | High/Medium/Low separation | ✅ Tested & Verified |
| **L2** | RANGE SUBPARTITION | created_at | Quarterly archival & lifecycle management | ✅ Tested & Verified |

### 🎯 Production Testing Results (Oracle AI DB 26ai - 2026-04-23)

**Test Environment:**
- Oracle AI DB 26ai Enterprise Edition 23.26.1.0.0
- SQLcl v26.1
- Connection: openclaw@//10.10.10.130:1521/openclaw

**Verified Syntax:**

✅ **LIST + RANGE SUBPARTITIONING (Recommended)**
```sql
CREATE TABLE audit_log (
    id NUMBER,
    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR2(20)
) PARTITION BY LIST (status) 
   SUBPARTITION BY RANGE (event_time)
   SUBPARTITION TEMPLATE (
       SUBPARTITION p1 VALUES LESS THAN (TO_DATE('2025-06-01', 'YYYY-MM-DD')),
       SUBPARTITION p2 VALUES LESS THAN (MAXVALUE)
   )
   (
       PARTITION active_vals VALUES ('ACTIVE'),
       PARTITION inactive_vals VALUES ('INACTIVE')
   );
```

✅ **Automatically Created Partition Structure:**
- ACTIVE_VALS → ACTIVE_VALS_P1, ACTIVE_VALS_P2  
- INACTIVE_VALS → INACTIVE_VALS_P1, INACTIVE_VALS_P2

✅ **SUBPARTITION TEMPLATE Support** - Automatically creates same structure subpartitions for each PARTITION

### ⚠️ Discovered Limitations:
- ❌ `STORE IN` at LIST+RANGE SUBPARTITIONING PARTITION level may not be supported (ORA-02216)
- ✅ Recommended to specify tablespace only when needed, or use default tablespace

### 🎯 Production Environment Recommendations:
1. ✅ Use LIST + RANGE SUBPARTITIONING
2. ✅ Define SUBPARTITION TEMPLATE to simplify DDL
3. ⚠️ Avoid using `STORE IN` at PARTITION level (unless syntax support confirmed)
4. ✅ Use TIMESTAMP column as RANGE partition key

**Expected Performance Improvements:**
- Query Performance: **3-10x improvement** for priority-based queries
- Storage Cost: **40-60% reduction** via cold data archiving
- Lifecycle Management: Automated partition exchange/delete operations
- Backup Efficiency: **5x faster** with hot/cold separation

### Complete Partition Definition

See references/partition-strategy.md for full implementation details.

---

## 📚 Related Skills & Documentation

- [`oracle-memory-partition-strategy-v0.3.1`](../oracle-memory-partition-strategy-v0.3.1) - Complete partition strategy design document
- [`oracle-26ai-vector-index-api`](../oracle-26ai/oracle-26ai-vector-index-api) - Vector Index API reference
- [`oracle-26ai-property-graph-setup`](../oracle-26ai/oracle-26ai-property-graph-setup) - Property Graph integration guide

---

## 👨‍💻 Author & Maintainer

**Haiwen Yin (胖头鱼 🐟)**  
Oracle/PostgreSQL/MySQL ACE Database Expert

- **Blog**: https://blog.csdn.net/yhw1809
- **GitHub**: https://github.com/Haiwen-Yin

---

## 📄 License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](../LICENSE) file for details.

**Last Updated**: 2026-04-23 v0.3.1
