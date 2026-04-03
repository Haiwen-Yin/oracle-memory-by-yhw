---
name: oracle-memory-by-yhw
description: "Oracle AI Database memory system for OpenClaw v0.1.0. Uses oracle-sqlcl MCP server (RunSqlTool, ConnectTool, SchemaInformationTool) as primary interface; shell script as fallback. Provides semantic search, memory write/list/delete, and property graph relationship queries via native VECTOR type and SQL/PGQ graph. Works with any Oracle 23ai/26ai database. Use when: (1) searching/writing memories on Oracle DB via MCP tools, (2) graph traversal queries, (3) setting up Oracle memory backend for new environments. NOT for OpenClaw native Markdown memory."
---

# Oracle Memory (oracle-memory-by-yhw) v0.1.0

Oracle AI Database memory backend. Uses `oracle-sqlcl` MCP server as primary interface.

## Prerequisites

### Oracle AI Database 23ai/26ai (Required — Self-Provided)
**This skill does NOT include a database.** You must have your own Oracle AI Database 23ai or 26ai instance deployed and accessible.

- Download from [Oracle AI Database](https://www.oracle.com/ai-database/) or use Oracle Cloud
- The database must have `VECTOR` type support (23ai 23.6+ or 26ai)
- Note the connection details: host, port, service name, username, password

### Java Runtime (Required)
SQLcl requires **JDK 17+** (JDK 21+ recommended). Without Java, the `oracle-sqlcl` MCP server will not start.

```bash
# Verify Java installation
java -version

# If not installed, install JDK (examples):
# Ubuntu/Debian: sudo apt install openjdk-21-jdk
# RHEL/Rocky:    sudo dnf install java-21-openjdk-devel
# macOS:         brew install openjdk
```

Set `JAVA_HOME` env var to your JDK path (e.g., `/usr/lib/jvm/java-21-openjdk`).

### Other Requirements
- SQLcl 25.4.2+ (from Oracle, requires Java)
- Oracle AI Database 23ai/26ai
- Ollama with embedding model (bge-m3 recommended)

## MCP Server Integration

When `oracle-sqlcl` MCP server is configured in openclaw.json, use these tools:

| MCP Tool | Purpose |
|--|--|
| `RunSqlTool` | Execute any SQL/PLSQL — all memory operations use this |
| `ConnectTool` | Verify database connection |
| `SchemaInformationTool` | Get table/column metadata |
| `ListConnectionsTool` | List available connections |

### MCP Server Setup (New Environments)

Add to openclaw.json under `mcp.servers`:
```json
{
  "oracle-sqlcl": {
    "command": "/path/to/sqlcl/bin/sql",
    "args": ["--mcp", "-S"],
    "env": {
      "JAVA_HOME": "/path/to/jdk",
      "PATH": "/path/to/jdk/bin:$PATH"
    }
  }
}
```

DB connection via env: `ORACLE_USER`, `ORACLE_PASS`, `ORACLE_HOST`, `ORACLE_PORT`, `ORACLE_SERVICE`.

## Operations via RunSqlTool

### Search Memories
1. Get embedding: `curl localhost:11434/api/embed -d '{"model":"bge-m3","input":"query"}'`
2. Execute via RunSqlTool:
```sql
DECLARE l_result CLOB;
BEGIN
  l_result := DBMS_VECTOR_DATABASE.SEARCH(
    table_name => 'MEM_VECTORS',
    query_by => JSON('{"vector":[...vector array...]}'),
    top_k => 5
  );
  DBMS_OUTPUT.PUT_LINE(l_result);
END;
/
```

### Write Memory
```sql
DECLARE
  l_vec VARCHAR2(32767) := '[...vector...]';
  l_meta VARCHAR2(32767) := '{"text":"content","category":"cat","tags":"t1,t2"}';
BEGIN
  EXECUTE IMMEDIATE
    'INSERT INTO mem_vectors (dense_vector, metadata) VALUES (VECTOR(:1), JSON(:2))'
    USING l_vec, l_meta;
  COMMIT;
END;
/
```

### Graph Query (Multi-hop)
```sql
WITH paths (src, dst, chain, depth) AS (
  SELECT c1.name, c2.name, r.relation_type, 1
  FROM graph_relations r
  JOIN graph_concepts c1 ON r.src_concept_id = c1.concept_id
  JOIN graph_concepts c2 ON r.dst_concept_id = c2.concept_id
  WHERE c1.name LIKE '%concept%'
  UNION ALL
  SELECT p.src, c2.name, p.chain || ' -> ' || r.relation_type, p.depth + 1
  FROM paths p
  JOIN graph_relations r ON r.src_concept_id = (
    SELECT concept_id FROM graph_concepts WHERE name = p.dst
  )
  JOIN graph_concepts c2 ON r.dst_concept_id = c2.concept_id
  WHERE p.depth < 2
)
CYCLE dst SET is_cycle TO 'Y' DEFAULT 'N'
SELECT src, dst, chain, depth FROM paths WHERE is_cycle = 'N';
```

### Initialize Tables
Run via RunSqlTool:
```sql
-- 1. Vector table
DECLARE l_result CLOB;
BEGIN
  l_result := DBMS_VECTOR_DATABASE.CREATE_VECTOR_TABLE(
    table_name => 'MEM_VECTORS', description => 'Agent memory',
    auto_generate_id => TRUE, vector_type => 'dense');
END;
/
-- 2. Graph tables
CREATE TABLE graph_concepts (concept_id VARCHAR2(40) PRIMARY KEY, name VARCHAR2(500), category VARCHAR2(100), description VARCHAR2(4000));
CREATE TABLE graph_relations (relation_id NUMBER GENERATED ALWAYS AS IDENTITY, src_concept_id VARCHAR2(40), dst_concept_id VARCHAR2(40), relation_type VARCHAR2(100), weight NUMBER DEFAULT 1.0);
-- 3. Property graph
CREATE PROPERTY GRAPH memory_graph VERTEX TABLES (graph_concepts KEY (concept_id) PROPERTIES (name, category, description)) EDGE TABLES (graph_relations KEY (relation_id) SOURCE KEY (src_concept_id) REFERENCES graph_concepts(concept_id) DESTINATION KEY (dst_concept_id) REFERENCES graph_concepts(concept_id) PROPERTIES (relation_type, weight) LABEL relation_type);
```

## Shell Fallback

When MCP server is not available:
```bash
bash scripts/oracle-memory.sh setup   # Interactive config
bash scripts/oracle-memory.sh init    # Create tables
bash scripts/oracle-memory.sh search "query" 5
bash scripts/oracle-memory.sh write "text" "cat" "tags"
```

## Key Gotchas

- **Java required**: MCP server will not start without Java (JDK 17+)
- **VECTOR constructor**: Only works in `EXECUTE IMMEDIATE`, not static PL/SQL
- **UPSERT_VECTORS**: ORA-57707 bug — use dynamic INSERT with VECTOR()
- **Embeddings**: Consistent model required (bge-m3, 1024 dims)
- **Chinese text**: MCP handles UTF-8 natively; shell uses Python for encoding
- **Config security**: Shell config `~/.oracle-memory/config.env` has 600 permissions

## Schema Reference

See [references/schema.md](references/schema.md) for full table structures, API reference, and network ACL setup.
