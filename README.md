# oracle-memory-by-yhw

> Universal Oracle AI Database memory system for OpenClaw — semantic search, vector storage, and knowledge graph queries via MCP.

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)]()
[![Oracle](https://img.shields.io/badge/Oracle-23ai%2F26ai-red.svg)]()
[![MCP](https://img.shields.io/badge/MCP-SQLcl-green.svg)]()
[![License](https://img.shields.io/badge/license-apache2.0-green.svg)]()

---

## Overview

Transform any Oracle AI Database (23ai/26ai) instance into a powerful, AI-native memory backend for OpenClaw agents. Leverages Oracle's native `VECTOR` type for semantic similarity search and SQL/PGQ for knowledge graph relationship traversal — all through the `oracle-sqlcl` MCP server.

**This is NOT a replacement for OpenClaw's native Markdown memory.** It's a complementary layer that adds vector search and graph reasoning capabilities for structured, high-volume memory use cases.

## Features

- **Semantic Search** — Query memories by meaning, not just keywords. Powered by Oracle's native `VECTOR` type and `DBMS_VECTOR_DATABASE` package.
- **Knowledge Graph** — Store and traverse concept relationships using Oracle Property Graph with SQL/PGQ syntax.
- **MCP-First Design** — Primary execution via `oracle-sqlcl` MCP server (`RunSqlTool`). Shell script available as fallback.
- **Universal** — Works with any Oracle 23ai/26ai database. Configurable for any host, user, and embedding model.
- **Chinese-Optimized** — Tested with `bge-m3` embedding model for excellent Chinese language support.
- **Zero Dependencies on OpenClaw Core** — Runs as a standalone skill; no modifications to OpenClaw required.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       OpenClaw Agent                          │
│                                                               │
│  PRIMARY: oracle-sqlcl MCP Server                            │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ Agent → MCP Tools (RunSqlTool, ConnectTool, etc)    │     │
│  │              ↓                                       │     │
│  │         SQLcl (--mcp -S)                            │     │
│  │              ↓                                       │     │
│  │         Oracle AI Database 23ai/26ai                 │     │
│  │         ┌─────────────────────────────────┐         │     │
│  │         │  MEM_VECTORS  (VECTOR type)      │         │     │
│  │         │  GRAPH_CONCEPTS (vertices)       │         │     │
│  │         │  GRAPH_RELATIONS (edges)         │         │     │
│  │         │  MEMORY_GRAPH (Property Graph)   │         │     │
│  │         └─────────────────────────────────┘         │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                               │
│  FALLBACK: Shell Script (oracle-memory.sh)                   │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ Agent → bash → SQLcl CLI → Oracle DB                 │     │
│  │ Ollama curl → embeddings                             │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                               │
│  EMBEDDING: Ollama (or any compatible API)                   │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  POST /api/embed → bge-m3 → 1024-dim vector         │     │
│  └─────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

## Prerequisites

| Requirement | Version | Notes |
|--|--|--|
| **Oracle AI Database** | 23ai (23.6+) or 26ai | ⚠️ **Self-provided — this skill does NOT include a database.** Download from [Oracle](https://www.oracle.com/ai-database/) or use Oracle Cloud. Must have VECTOR type support. |
| **Java JDK** | 17+ (21+ recommended) | Required for SQLcl MCP server |
| **SQLcl** | 25.4.2+ | Download from [Oracle](https://www.oracle.com/database/sqlcl/) |
| **Ollama** | Latest | For embedding generation (or any compatible API) |
| **Embedding Model** | bge-m3 (recommended) | 1024 dimensions, Chinese-optimized |

## Installation

### Step 1: Install the Skill

```bash
# Option A: From ClawHub
openclaw skills install oracle-memory-by-yhw

# Option B: Manual download
cd ~/.openclaw/workspace/skills
unzip /path/to/oracle-memory-by-yhw-0.1.0.zip
```

### Step 2: Configure MCP Server

Add to your `openclaw.json`:

```json
{
  "mcp": {
    "servers": {
      "oracle-sqlcl": {
        "command": "/path/to/sqlcl/bin/sql",
        "args": ["--mcp", "-S"],
        "env": {
          "JAVA_HOME": "/path/to/jdk",
          "PATH": "/path/to/jdk/bin:$PATH"
        }
      }
    }
  }
}
```

### Step 3: Set Database Connection

Via environment variables:
```bash
export ORACLE_USER=openclaw
export ORACLE_PASS=your_password
export ORACLE_HOST=10.10.10.130
export ORACLE_PORT=1521
export ORACLE_SERVICE=openclaw
```

### Step 4: Restart Gateway

```bash
openclaw gateway restart
```

### Step 5: Initialize Tables

Ask the agent to run the initialization SQL via `RunSqlTool`, or use the shell script:

```bash
bash scripts/oracle-memory.sh init
```

## Usage

### Semantic Search

```bash
# Search for "database issues" with top 5 results
bash scripts/oracle-memory.sh search "数据库连接问题" 5
```

Via MCP `RunSqlTool`:
1. Get embedding: `curl localhost:11434/api/embed -d '{"model":"bge-m3","input":"database issue"}'`
2. Execute SQL:
```sql
DECLARE l_result CLOB;
BEGIN
  l_result := DBMS_VECTOR_DATABASE.SEARCH(
    table_name => 'MEM_VECTORS',
    query_by => JSON('{"vector":[...]}'),
    top_k => 5
  );
  DBMS_OUTPUT.PUT_LINE(l_result);
END;
/
```

### Write Memory

```bash
bash scripts/oracle-memory.sh write "SQLcl连接Oracle成功" "success" "SQLcl,Oracle,连接"
```

### Graph Relationship Query

```bash
# Find all relationships from "Oracle" up to 2 hops deep
bash scripts/oracle-memory.sh graph "Oracle" 2
```

Returns paths like:
```
SQLcl → uses → Oracle → is_a → 数据库
```

### List & Delete

```bash
bash scripts/oracle-memory.sh list 10
bash scripts/oracle-memory.sh delete "test data"
```

## Configuration

### Interactive Setup

```bash
bash scripts/oracle-memory.sh setup
```

Guides you through database connection, Ollama URL, and embedding model selection. Config saved to `~/.oracle-memory/config.env` (permissions: 600).

### Environment Variables

| Variable | Default | Description |
|--|--|--|
| `ORACLE_HOST` | `localhost` | Database host |
| `ORACLE_PORT` | `1521` | Database port |
| `ORACLE_SERVICE` | `ORCL` | Database service name |
| `ORACLE_USER` | — | Database username (required) |
| `ORACLE_PASS` | — | Database password (required) |
| `SQLCL_PATH` | `sql` | Path to SQLcl binary |
| `JAVA_HOME` | — | JDK installation path |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API endpoint |
| `EMBED_MODEL` | `bge-m3` | Embedding model name |

## Schema

| Table | Purpose |
|--|--|
| `MEM_VECTORS` | Vector memory (ID, DENSE_VECTOR, METADATA JSON) |
| `GRAPH_CONCEPTS` | Graph vertices (concept_id, name, category, description) |
| `GRAPH_RELATIONS` | Graph edges (relation_id, src, dst, relation_type, weight) |

Property Graph: `MEMORY_GRAPH` — created via `CREATE PROPERTY GRAPH` statement.

## Troubleshooting

### MCP server won't start
- **Check Java**: `java -version` — must be JDK 17+
- **Check SQLcl**: `/path/to/sqlcl/bin/sql --mcp -S --version`
- **Check JAVA_HOME**: Must point to a valid JDK installation

### ORA-01017: invalid username/password
- Verify `ORACLE_USER` and `ORACLE_PASS` environment variables
- Test connection: `sql user/pass@//host:port/service`

### ORA-57707 on UPSERT_VECTORS
- Known Oracle 26ai bug. Use dynamic INSERT with `VECTOR()` constructor instead:
```sql
EXECUTE IMMEDIATE
  'INSERT INTO mem_vectors (dense_vector, metadata) VALUES (VECTOR(:1), JSON(:2))'
  USING vec_str, meta_json;
```

### VECTOR constructor fails in static SQL
- VECTOR type only works in `EXECUTE IMMEDIATE`, not static PL/SQL blocks.

### Chinese text encoding issues
- MCP mode handles UTF-8 natively. Shell script uses Python for proper encoding.
- Avoid piping Chinese text directly through shell heredocs.

### Embedding service unreachable
- Verify Ollama is running: `curl localhost:11434/api/tags`
- Check model is pulled: `ollama list | grep bge-m3`
- Pull if missing: `ollama pull bge-m3`

## Roadmap

- [ ] Support for custom embedding providers (OpenAI, Cohere, etc.)
- [ ] Automatic memory sync between Markdown and Oracle
- [ ] RAG pipeline integration
- [ ] Multi-agent memory isolation
- [ ] Memory TTL and auto-cleanup

## Contributing

Contributions welcome! Please open an issue or submit a PR.

## License

Apache 2.0

---

**Built for OpenClaw** — [GitHub](https://github.com/openclaw/openclaw) | [ClawHub](https://clawhub.ai) | [Docs](https://docs.openclaw.ai)
