# Oracle AI Database Memory System - Version Changelog

## [0.3.0] Enhanced Schema Edition (2026-04-22) ⭐ NEW

### Major Changes

#### Universal Design (Breaking Change)
- **Changed**: From OpenClaw-specific memory system to universal AI Agent memory backend
- **Impact**: Works with any Oracle 23ai/26ai database, not just OpenClaw environment
- **Action Required**: Update connection strings and remove OpenClaw-specific references

#### Dynamic Dimension Management (NEW)
- **Added**: Automatic VECTOR column dimension adjustment based on embedding model
- **Files**: 
  - `scripts/adjust_vector_dimension.sql` - SQLcl automation script
  - `scripts/memory_embedding_manager.py` - Python integration manager
- **Supported Models**:
  - BGE-M3: 1024 dimensions (default)
  - text-embedding-3-small: 1536 dimensions
  - text-embedding-3-large: 3072 dimensions
  - Custom models: Any dimension with manual configuration

#### Active Data Guard HA (NEW)
- **Added**: Production-ready high availability with ADG configuration
- **Files**: 
  - `templates/adg_deployment_template.sql` - Complete ADG setup script
  - `scripts/memory_read_splitter.py` - Smart query routing tool
- **Features**:
  - Real-time apply for zero data loss protection
  - Automatic failover capability
  - Read-only standby for load balancing queries

#### Multi-Model Support (Enhanced)
- **Changed**: Not limited to BGE-M3, supports any Oracle Vector compatible model
- **Added**: Configurable embedding endpoint and model selection
- **Files**: `scripts/memory_embedding_manager.py` with dimension mapping table

### New Files Added

| File | Purpose | Category |
|------|---------|----------|
| `scripts/adjust_vector_dimension.sql` | Dimension adjustment automation | Core |
| `scripts/memory_embedding_manager.py` | Python integration manager | Core |
| `scripts/memory_read_splitter.py` | Smart query routing | HA |
| `scripts/memory_system_health_check.py` | Health monitoring tool | Operations |
| `templates/adg_deployment_template.sql` | ADG deployment configuration | HA |

### Schema Enhancements

#### Table Structure Updates
- **MEMORIES**: CLOB type for unlimited content length (unchanged from v0.2.x)
- **MEMORIES_VECTORS**: Added model_version column for tracking embedding source
- **MEMORY_RELATIONSHIPS**: CHECK constraint validation added
- **RELATIONSHIP_TYPES**: New lookup table for normalized relationship types

#### Index Optimization
- IDX_MEMORIES_TYPE (normal query optimization)
- IDX_MEMORIES_CATEGORY (category filtering)
- IDX_MEMORIES_PRIORITY (priority-based sorting DESC)
- IDX_MEMORIES_CREATED (time-based queries DESC)
- IDX_VECTORS_MEMORY_LOOKUP (memory_id join optimization)
- IDX_RELATIONSHIPS_SOURCE/TARGET/TYPE (graph traversal)

#### Trigger Enhancements
- **TRG_MEMORIES_UPDATED_AT**: BEFORE UPDATE trigger with microsecond precision
- Automatic timestamp update on any memory modification
- No manual intervention required

### Performance Improvements

| Optimization | Impact | Description |
|--------------|--------|-------------|
| Dynamic dimension adjustment | N/A | Prevents ORA-02329 errors when models change |
| ADG read splitting | 50% query load reduction | Standby handles read queries during normal operation |
| Smart routing | Zero downtime failover | Automatic primary fallback if standby unavailable |
| Health monitoring | Proactive issue detection | Automated checks prevent production failures |

### Configuration Changes

#### Environment Variables (NEW)
```bash
# Database connections
export PRIMARY_CONN="openclaw@//10.10.10.130:1521/openclaw"
export STANDBY_CONN="openclaw@//10.10.10.131:1521/openclaw_standby"

# Embedding model
export EMBEDDING_MODEL="bge-m3"  # or text-embedding-3-small/large
export LMSTUDIO_ENDPOINT="http://10.10.10.1/v1/embeddings"
```

#### Connection String Format (Changed)
- **v0.2.x**: `openclaw@//host:port/service`
- **v0.3.0**: Same format, but primary/standby distinction for ADG

---

## [0.2.x] Schema Optimization Edition (2026-04-xx)

### Major Improvements

#### CONTENT Field Extension
- **Changed**: VARCHAR2(4000) → CLOB type
- **Impact**: Unlimited length memory content support
- **Benefit**: Can store complete conversation history, code snippets, large documents

#### VECTOR Dimension Fix
- **Changed**: 1536 dimensions → 1024 dimensions (BGE-M3 compatible)
- **Impact**: No more ORA-02329 dimension mismatch errors
- **Benefit**: Consistent behavior with BGE-M3 embedding model

#### Updated_AT Trigger
- **Added**: BEFORE UPDATE trigger for automatic timestamp update
- **Impact**: No manual maintenance of updated_at field
- **Benefit**: Microsecond precision, audit trail support

#### Relationship Type Validation
- **Added**: CHECK constraint + RELATIONSHIP_TYPES lookup table
- **Impact**: Prevents inconsistent type values (related_to vs RelatedTo)
- **Standard Types**: related_to, updates, contradicts, depends_on, supersedes, extends

---

## [0.1.0] Initial Release (2026-03-xx)

### Core Features

#### Basic Schema Design
- MEMORIES table for memory content storage
- MEM_VECTORS table for vector embeddings (BGE-M3 specific)
- Property Graph support with JRD (JSON Relational Duality)

#### Semantic Search
- DBMS_VECTOR_DATABASE.SEARCH() API integration
- KNN similarity search capability
- Filter by category and type

#### Knowledge Graph
- GRAPH_CONCEPTS table for node storage
- GRAPH_RELATIONS table for edge relationships
- Property graph view creation

---

## Version Comparison Summary

| Feature | v0.1.0 | v0.2.x | v0.3.0 |
|---------|--------|--------|--------|
| Target Environment | OpenClaw only | OpenClaw focused | **Universal** ✅ |
| CONTENT Type | VARCHAR2(4000) | CLOB | CLOB |
| VECTOR Dimension | 1536 (fixed) | 1024 (BGE-M3) | **Dynamic** ✅ |
| Updated_AT | Manual | Trigger | Trigger ✅ |
| Relationship Types | No validation | CHECK constraint | CHECK + lookup table ✅ |
| HA/DR | None | None | **Active Data Guard** ✅ |
| Read/Write Splitting | No | No | **Smart routing** ✅ |
| Health Monitoring | No | Basic | Automated checks ✅ |

---

## Migration Guide: v0.2.x → v0.3.0

### Step 1: Backup Existing Schema
```bash
expdp openclaw@//host:port/service DIRECTORY=DATA_PUMP_DIR DUMPFILE=memory_backup.dmp TABLES=MEMORIES,MEM_VECTORS,GRAPH_CONCEPTS,GRAPH_RELATIONS
```

### Step 2: Update Connection Configuration
- Add standby database connection string
- Configure read/write splitter endpoints

### Step 3: Deploy ADG (if not already)
- Follow `templates/adg_deployment_template.sql` instructions
- Verify real-time apply status before production use

### Step 4: Test New Features
```bash
# Run health check
python scripts/memory_system_health_check.py

# Test dimension adjustment
/root/sqlcl/bin/sql-mcp.sh openclaw@//host:port/service @scripts/adjust_vector_dimension.sql BGE-M3
```

---

## Known Issues & Limitations

### v0.3.0 Limitations

1. **Dimension Adjustment Requires Table Recreation**
   - If table has existing data, must export/import vectors
   - Plan maintenance window for production changes

2. **ADG Standby Query Latency**
   - Standby may be 1-5 seconds behind primary
   - Not suitable for real-time read-after-write scenarios

3. **Model Support Matrix**
   - Only tested with BGE-M3 and text-embedding-3-* models
   - Custom models require manual dimension configuration

### v0.2.x Known Issues (Fixed in 0.3.0)

1. ❌ Fixed: VARCHAR2(4000) length limitation → CLOB type
2. ❌ Fixed: VECTOR dimension mismatch errors → Dynamic adjustment
3. ❌ Fixed: Manual updated_at maintenance → Automatic trigger

---

## Support & Contact

**Author**: Haiwen Yin (胖头鱼 🐟)  
**Role**: Oracle ACE Database Expert  
**Blog**: https://blog.csdn.net/yhw1809  
**GitHub**: https://github.com/Haiwen-Yin  

**License**: Proprietary - Oracle AI Database 26ai

---

*Last Updated: 2026-04-22*