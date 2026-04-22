# Oracle AI Database Memory System v0.3.0 Enhanced Schema Edition

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.3.0-green.svg)](CHANGELOG.md)
[![Oracle AI DB](https://img.shields.io/badge/Oracle-26ai-orange.svg)](https://www.oracle.com/database/technologies/appdev/vector-database.html)

**Universal memory system for all AI Agents with dynamic dimension adjustment, Active Data Guard HA, and multi-model embedding support.**

---

## 📋 Quick Start

### Prerequisites

1. **Oracle AI Database 23ai/26ai** (Required)
   - Must have `VECTOR` type support (23ai 23.6+ or 26ai)
   - Download from [Oracle AI Database](https://www.oracle.com/database/technologies/appdev/vector-database.html)

2. **Java Runtime** (Required for SQLcl)
   ```bash
   java -version  # Verify Java installation
   # Install if needed: sudo apt install openjdk-21-jdk
   ```

3. **Embedding Service** (Flexible & Configurable)
   - LM Studio recommended for local development
   - Supports multiple embedding sources via configuration

---

## 🚀 Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/Haiwen-Yin/oracle-memory-by-yhw-0.3.0.git
cd oracle-memory-by-yhw-0.3.0
```

### Step 2: Configure Database Connection

Copy the example configuration file and fill in your values:

```bash
cp config.example.env ~/.oracle-memory/config.env
nano ~/.oracle-memory/config.env
```

Edit the following variables:
- `PRIMARY_CONN`: Primary database connection string (for writes)
- `STANDBY_CONN`: Standby database connection string (for reads, optional)
- `EMBEDDING_MODEL`: Embedding model name
- `LMSTUDIO_ENDPOINT`: LM Studio API endpoint

### Step 3: Initialize Memory Schema

```bash
# Source your configuration
source ~/.oracle-memory/config.env

# Run the schema initialization script
/root/sqlcl/bin/sql-mcp.sh $PRIMARY_CONN @scripts/init_schema.sql
```

---

## 🏗️ System Architecture Overview

The memory system is built on Oracle AI Database 26ai with Active Data Guard high availability:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI Agent Memory System v0.3.0                    │
│                        (Universal Design)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐    ┌──────────────────┐                       │
│  │   AI Agent       │    │   Hermes Agent   │                       │
│  │   (Any Platform) │    │   (Hermes)       │                       │
│  └────────┬─────────┘    └────────┬─────────┘                       │
│           │                       │                                 │
│           ▼                       ▼                                 │
│  ┌──────────────────────────────────────────────┐                   │
│  │        Memory System Interface Layer         │                   │
│  │   • Semantic Search (DBMS_VECTOR)            │                   │
│  │   • Knowledge Graph Traversal                │                   │
│  │   • Vector Similarity Retrieval              │                   │
│  └───────────────────┬──────────────────────────┘                   │
│                      │                                              │
│                      ▼                                              │
│  ┌──────────────────────────────────────────────┐                   │
│  │           Oracle AI Database 26ai            │                   │
│  │   (Active Data Guard High Availability)      │                   │
│  ├──────────────────────────────────────────────┤                   │
│  │                                              │                   │
│  │  ┌─────────────┐    ┌─────────────┐          │                   │
│  │  │   Primary   │◄──►│  Standby    │          │                   │
│  │  │   (R/W)     │ ADG│   (R/O)     │          │                   │
│  │  └─────────────┘    └─────────────┘          │                   │
│  │                                              │                   │
│  │  Core Tables:                                │                   │
│  │  • MEMORIES (CLOB content, CLOB tags)        │                   │
│  │  • MEMORIES_VECTORS (VECTOR dynamic dim)     │                   │
│  │  • MEMORY_RELATIONSHIPS (Graph edges)        │                   │
│  │  • RELATIONSHIP_TYPES (Lookup table)         │                   │
│  └──────────────────────────────────────────────┘                   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                    Key Features                                     │
├─────────────────────────────────────────────────────────────────────┤
│  ✓ Dynamic Dimension Management    • CLOB Type Support              │
│  ✓ Active Data Guard HA            • Trigger Automation             │
│  ✓ Smart Query Routing             • Relationship Validation        │
│  ✓ Multi-Model Embedding           • Health Monitoring              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Core Features

### ✅ Dynamic Dimension Management

Automatic VECTOR column adjustment when embedding model changes:

```bash
# Check current dimension before model change
/root/sqlcl/bin/sql-mcp.sh openclaw@//host:port/service @scripts/adjust_vector_dimension.sql BGE-M3
```

**Supported Models:**
- **BGE-M3**: 1024 dimensions (default)
- **text-embedding-3-small**: 1536 dimensions  
- **text-embedding-3-large**: 3072 dimensions
- **Custom models**: Any dimension with manual configuration

### ✅ Active Data Guard High Availability

Production-ready HA with zero data loss protection:

```bash
# Deploy ADG configuration (on primary server)
/root/sqlcl/bin/sql-mcp.sh openclaw@//primary-host:1521/openclaw @templates/adg_deployment_template.sql

# Verify status
python scripts/memory_system_health_check.py
```

### ✅ Smart Query Routing

Automatic routing based on operation type:

```bash
# Write operations always go to primary (mandatory)
python scripts/memory_read_splitter.py --primary $PRIMARY_CONN

# Read operations prefer standby with automatic fallback  
python scripts/memory_read_splitter.py --standby $STANDBY_CONN
```

---

## 📁 File Structure

```
oracle-memory-by-yhw-0.3.0/
├── LICENSE                       # Apache 2.0 License ✅
├── NOTICE                        # Copyright notice
├── README.md                     # This file
├── CHANGELOG.md                  # Version history and migration guide  
├── SKILL.md                      # Complete technical documentation
├── config.example.env            # Configuration template (copy to config.env)
├── .gitignore                    # Git ignore rules
├── scripts/
│   ├── adjust_vector_dimension.sql    # SQLcl dimension adjustment automation ✅
│   ├── memory_embedding_manager.py    # Python embedding integration manager ✅
│   ├── memory_read_splitter.py        # Smart query routing tool ✅
│   └── memory_system_health_check.py  # Health monitoring script ✅
├── templates/
│   └── adg_deployment_template.sql    # Active Data Guard deployment configuration ✅
```

---

## 🧪 Health Monitoring

### Run Complete Health Check

```bash
python scripts/memory_system_health_check.py --primary $PRIMARY_CONN --standby $STANDBY_CONN
```

**Output Example:**
```
======================================================================
Oracle AI Database Memory System Health Check
Timestamp: 2026-04-22 15:45:00
Version: v0.3.0 Enhanced Schema Edition
======================================================================

[Primary DB Status]
✓ Primary DB is active and ready for writes

[ADG Sync Status]  
✓ ADG sync is healthy, standby lag < 30 seconds

[Memory Tables]
✓ All memory tables exist (3 total)

[Vector Dimension]
✓ VECTOR dimension matches expected value (1024)

[UPDATED_AT Trigger]
✓ UPDATED_AT trigger is active and enabled

[Relationship Types]
✓ Relationship types configured with all standard types

======================================================================
HEALTH CHECK SUMMARY
======================================================================
✓ OK: 6/6
⚠️ WARNING: 0/6
❌ ERROR: 0/6

SYSTEM HEALTH: All components are healthy! ✅
```

---

## 🎯 Common Use Cases

### Use Case 1: Multi-Model Support

Switch from BGE-M3 to text-embedding-3-small:

```bash
# Check current dimension
/root/sqlcl/bin/sql-mcp.sh openclaw@//host:port/service @scripts/adjust_vector_dimension.sql BGE-M3

# If table has no data, safe to proceed. Otherwise:
DROP TABLE memories_vectors CASCADE CONSTRAINTS;
CREATE TABLE memories_vectors (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    memory_id NUMBER NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    embedding VECTOR(1536),  # New dimension for text-embedding-3-small
    created_at TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP,
    model_version VARCHAR2(50) DEFAULT 'text-embedding-3-small'
);

# Update configuration
export EMBEDDING_MODEL="text-embedding-3-small"
```

### Use Case 2: Production Deployment with ADG

1. **Configure Primary Database** (on primary server):
   ```bash
   /root/sqlcl/bin/sql-mcp.sh openclaw@//primary-host:1521/openclaw @templates/adg_deployment_template.sql
   ```

2. **Configure Standby Database** (on standby server):
   ```bash  
   /root/sqlcl/bin/sql-mcp.sh openclaw@//standby-host:1521/openclaw_standby @templates/adg_deployment_template.sql
   ```

3. **Enable Read/Write Splitter**:
   ```bash
   python scripts/memory_read_splitter.py --primary $PRIMARY_CONN --standby $STANDBY_CONN
   ```

### Use Case 3: Daily Health Monitoring

Add to crontab for automated monitoring:

```bash
# Run health check every 6 hours
0 */6 * * * cd /path/to/oracle-memory-by-yhw-0.3.0 && python scripts/memory_system_health_check.py >> ~/memory_health.log 2>&1
```

---

## 🐛 Troubleshooting

### Issue: VECTOR Dimension Mismatch Error

**Error:** `ORA-02329 - Column of data type VECTOR cannot be unique or a primary key`

**Solution:**
```bash
# Check current dimension
/root/sqlcl/bin/sql-mcp.sh openclaw@//host:port/service @scripts/adjust_vector_dimension.sql BGE-M3

# If mismatch detected, follow prompts to adjust
```

### Issue: ADG Sync Lag Too High

**Symptom:** Standby database significantly behind primary

**Solution:**
```sql
-- Check standby lag
SELECT sequence#, applied, 
       ROUND((SYSDATE - TO_DATE(first_time, 'YYYY-MM-DD HH24:MI:SS')) * 24 * 60, 2) AS minutes_lag
FROM v$standby_log;

-- If lag > 5 minutes:
-- • Increase network bandwidth between primary and standby
-- • Optimize storage I/O on standby server  
-- • Adjust LOG_ARCHIVE_DEST_2 parameters (SYNC vs ASYNC)
```

### Issue: Trigger Not Firing

**Symptom:** updated_at timestamp not updating after UPDATE operation

**Solution:**
```bash
# Check trigger status
/root/sqlcl/bin/sql-mcp.sh openclaw@//host:port/service << 'EOF'
SELECT trigger_name, status 
FROM user_triggers 
WHERE table_name = 'MEMORIES' AND trigger_name LIKE '%UPDATED_AT%';
EXIT;
EOF

-- If disabled, re-enable it
ALTER TRIGGER trg_memories_updated_at ENABLE;
```

---

## 📚 Documentation & Resources

- **Complete Technical Reference**: [SKILL.md](SKILL.md) - Full API documentation and usage guide
- **Version History**: [CHANGELOG.md](CHANGELOG.md) - Migration guides and breaking changes  
- **Oracle AI Database Docs**: https://docs.oracle.com/en/database/oracle/26ai/index.html
- **DBMS_VECTOR_DATABASE API**: https://docs.oracle.com/en/database/oracle/23/arpls/DBMS_VECTOR_DATABASE.html
- **Active Data Guard Guide**: https://docs.oracle.com/en/database/data-guard/index.html

---

## 🤝 Contributing

This project is licensed under Apache 2.0 License. For contributions or questions:

**Author**: Haiwen Yin (胖头鱼 🐟)  
**Role**: Oracle ACE Database Expert  
**Blog**: https://blog.csdn.net/yhw1809  
**GitHub**: https://github.com/Haiwen-Yin  

---

## 📄 License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](LICENSE) file for details.

```
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

*Last Updated: 2026-04-22 | Version: 0.3.0 (Enhanced Schema Edition)*
