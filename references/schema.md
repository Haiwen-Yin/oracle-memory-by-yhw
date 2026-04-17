# Oracle Memory Schema & API Reference

## Table Structures

### MEM_VECTORS (Vector Memory)
Created via `DBMS_VECTOR_DATABASE.CREATE_VECTOR_TABLE()`.

| Column | Type | Description |
|--|--|--|
| ID | VARCHAR2(40) | Auto-generated GUID |
| DENSE_VECTOR | VECTOR(*,*,DENSE) | Embedding vector (dimension depends on model) |
| METADATA | JSON | `{\"text\": \"...\", \"category\": \"...\", \"tags\": \"...\"}` |

### GRAPH_CONCEPTS (Graph Vertices)

| Column | Type | Description |
|--|--|--|
| CONCEPT_ID | VARCHAR2(40) | Primary key |
| NAME | VARCHAR2(500) | Concept name |
| CATEGORY | VARCHAR2(100) | concept/technology/tool/error/person/etc |
| DESCRIPTION | VARCHAR2(4000) | Description text |

### GRAPH_RELATIONS (Graph Edges)

| Column | Type | Description |
|--|--|--|
| RELATION_ID | NUMBER | Auto-increment |
| SRC_CONCEPT_ID | VARCHAR2(40) | FK → GRAPH_CONCEPTS |
| DST_CONCEPT_ID | VARCHAR2(40) | FK → GRAPH_CONCEPTS |
| RELATION_TYPE | VARCHAR2(100) | is_a/part_of/uses/related_to/knows/etc |
| WEIGHT | NUMBER | Edge weight (default 1.0) |

## Property Graph: MEMORY_GRAPH

```sql
CREATE PROPERTY GRAPH memory_graph
  VERTEX TABLES (graph_concepts KEY (concept_id) PROPERTIES (name, category, description))
  EDGE TABLES (graph_relations KEY (relation_id)
    SOURCE KEY (src_concept_id) REFERENCES graph_concepts(concept_id)
    DESTINATION KEY (dst_concept_id) REFERENCES graph_concepts(concept_id)
    PROPERTIES (relation_type, weight) LABEL relation_type);
```

## DBMS_VECTOR_DATABASE API

| API | Description |
|--|--|
| `CREATE_VECTOR_TABLE(table_name, description, auto_generate_id, vector_type)` | Create vector table with auto-index |
| `SEARCH(table_name, query_by, top_k)` | Vector similarity search, returns JSON |
| `LIST_VECTOR_TABLES()` | List all vector tables in schema |
| `LIST_MODELS()` | List loaded models |
| `DROP_VECTOR_TABLE(table_name)` | Drop vector table and associated index |
| `REBUILD_INDEX(table_name)` | Rebuild vector index |
| `RERANK(...)` | Re-rank search results |

## Embedding Service Configuration (Multi-Source Support)

### Supported Sources

This skill supports **multiple embedding service sources** via configuration. No single source is hardcoded!

#### 1️⃣ LM Studio (Recommended for Local Use)

```bash
# Environment variables
export EMBEDDING_SOURCE="lmstudio"
export LMSTUDIO_BASE_URL="http://10.10.10.1:12345/v1"
export LMSTUDIO_MODEL="text-embedding-bge-m3"

# API Call Example
curl -s http://10.10.10.1:12345/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-bge-m3",
    "input": "text to embed"
  }' 
# Response: {"data":[{"embedding":[0.1, 0.2, ...]}],...}
```

**Compatible Models:**
- `text-embedding-bge-m3` - Best for Chinese, 1024 dimensions ✅
- `nomic-embed-text` - Lightweight, 768 dimensions
- `mxbai-embed-large` - English focused, 1024 dimensions

#### 2️⃣ Ollama (Easy Setup)

```bash
# Environment variables
export EMBEDDING_SOURCE="ollama"
export OLLAMA_HOST="localhost"
export OLLAMA_PORT=11434
export OLLAMA_MODEL="bge-m3"

# First, pull the model:
ollama pull bge-m3

# API Call Example
curl -s http://localhost:11434/api/embed \
  -d '{
    "model": "bge-m3",
    "input": "text to embed"
  }' 
# Response: {"embeddings":[[0.1, 0.2, ...]],...}
```

#### 3️⃣ OpenAI (Cloud API)

```bash
# Environment variables
export EMBEDDING_SOURCE="openai"
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="text-embedding-ada-002"

# API Call Example
curl -s https://api.openai.com/v1/embeddings \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-ada-002",
    "input": "text to embed"
  }' 
# Response: {"data":[{"embedding":[0.1, 0.2, ...]}],...}
```

#### 4️⃣ Custom HTTP Endpoint (Advanced)

For any compatible embedding service:

```bash
export EMBEDDING_SOURCE="custom"
export CUSTOM_EMBEDDING_URL="https://your-api.com/v1/embeddings"
export CUSTOM_EMBEDDING_MODEL="your-model-name"
export CUSTOM_API_KEY="your-key"  # Optional

# API Call Example
curl -s $CUSTOM_EMBEDDING_URL \
  -H "Authorization: Bearer $CUSTOM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-model-name",
    "input": "text to embed"
  }' 
```

### Auto-Detection Flow (source: auto)

When configured with `EMBEDDING_SOURCE="auto"`, the system attempts in order:

1. **Try LM Studio** (`LMSTUDIO_BASE_URL` env var set?)
2. **Try Ollama** (`OLLAMA_HOST` and model available?)
3. **Try OpenAI** (`OPENAI_API_KEY` set?)
4. **Fail gracefully** with helpful error message if all sources unavailable

### Model Dimension Compatibility

| Model | Dimensions | Recommended Use Case |
|-------|------------|---------------------|
| `text-embedding-bge-m3` | 1024 | Chinese text, multilingual ✅ |
| `nomic-embed-text` | 768 | Lightweight applications |
| `mxbai-embed-large` | 1024 | English-focused tasks |
| `text-embedding-ada-002` | 1536 | OpenAI users, high accuracy |

**⚠️ Important:** Use the **same embedding model consistently** for all memories and queries! Mixing models will break semantic search.

---

## Known Issues

1. **UPSERT_VECTORS bug**: Returns ORA-57707 on Oracle 26ai. Use `EXECUTE IMMEDIATE 'INSERT INTO mem_vectors ... VALUES (VECTOR(:1), JSON(:2))'` instead.
2. **VECTOR constructor**: Only works in `EXECUTE IMMEDIATE`, not static PL/SQL.
3. **JSON escaping**: Heredoc in shell can mangle JSON. Script uses Python to write SQL files with proper encoding.
4. **Model dimension mismatch**: Different models produce vectors of different lengths. Ensure consistent model usage across all operations.

---

## Network ACL Setup

For Oracle DB to access external embedding services:

### LM Studio (Localhost - No ACL needed)
```sql
-- Local connections don't require ACL setup
-- LM_HOST = localhost or 127.0.0.1
```

### Ollama (Localhost - No ACL needed)
```sql
-- Local connections don't require ACL setup
-- OLLAMA_HOST = localhost or 127.0.0.1
```

### External Services (OpenAI, Custom APIs)

For Oracle DB to access external embedding services:

```sql
-- Run as SYSDBA
BEGIN
  -- Create ACL for HTTP access
  DBMS_NETWORK_ACL_ADMIN.CREATE_ACL(
    acl => 'oracle_memory_http.xml',
    description => 'HTTP access for Oracle Memory embedding services',
    principal => 'YOUR_USER',  -- Replace with actual username
    is_grant => TRUE,
    privilege => 'connect'
  );
  
  -- Add resolve privilege (DNS resolution)
  DBMS_NETWORK_ACL_ADMIN.ADD_PRIVILEGE(
    acl => 'oracle_memory_http.xml',
    principal => 'YOUR_USER',
    is_grant => TRUE,
    privilege => 'resolve'
  );
  
  -- Assign ACL to target hosts
  -- For OpenAI:
  DBMS_NETWORK_ACL_ADMIN.ASSIGN_ACL(
    acl => 'oracle_memory_http.xml',
    host => 'api.openai.com',
    lower_port => 443,
    upper_port => 443
  );
  
  -- For custom APIs (add additional assignments as needed):
  DBMS_NETWORK_ACL_ADMIN.ASSIGN_ACL(
    acl => 'oracle_memory_http.xml',
    host => 'your-api-host.com',
    lower_port => 443,
    upper_port => 443
  );
  
  -- Commit changes
  COMMIT;
END;
/

-- Verify ACL assignment
SELECT * FROM DBA_NETWORK_ACL_PRIVILEGES WHERE principal = 'YOUR_USER';
```

### Testing Network Connectivity

```sql
-- Test connection to embedding service
DECLARE
  l_response CLOB;
BEGIN
  -- For LM Studio/Ollama (HTTP)
  l_response := UTL_HTTP.GET_REQUEST('http://localhost:12345/v1/models');
  
  -- For OpenAI/Custom APIs (HTTPS)
  -- l_response := UTL_HTTP.GET_REQUEST('https://api.openai.com/v1/models');
  
  DBMS_OUTPUT.PUT_LINE(l_response);
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('Connection failed: ' || SQLERRM);
END;
/
```

---

## Configuration Examples

### Example 1: Production Environment (LM Studio Primary)

```bash
export EMBEDDING_SOURCE="lmstudio"
export LMSTUDIO_BASE_URL="http://10.10.10.1:12345/v1"
export LMSTUDIO_MODEL="text-embedding-bge-m3"
export ORACLE_USER="openclaw"
export ORACLE_PASS="hermes"
export ORACLE_HOST="10.10.10.130"
export ORACLE_PORT="1521"
export ORACLE_SERVICE="openclaw"
```

### Example 2: Development Environment (Ollama Primary)

```bash
export EMBEDDING_SOURCE="ollama"
export OLLAMA_HOST="localhost"
export OLLAMA_PORT=11434
export OLLAMA_MODEL="bge-m3"
export ORACLE_USER="system"
export ORACLE_PASS="your_password"
export ORACLE_HOST="localhost"
export ORACLE_PORT="1521"
export ORACLE_SERVICE="ORCLCDB"
```

### Example 3: Multi-Source Fallback (Auto-Detect)

```bash
# Set all possible sources, system will try in order
export EMBEDDING_SOURCE="auto"

# LM Studio (Primary)
export LMSTUDIO_BASE_URL="http://10.10.10.1:12345/v1"
export LMSTUDIO_MODEL="text-embedding-bge-m3"

# Ollama (Secondary fallback)
export OLLAMA_HOST="localhost"
export OLLAMA_PORT=11434
export OLLAMA_MODEL="bge-m3"

# OpenAI (Tertiary fallback, optional)
export OPENAI_API_KEY="sk-..."  # Optional, only used if others fail

# Oracle connection (required)
export ORACLE_USER="openclaw"
export ORACLE_PASS="hermes"
export ORACLE_HOST="10.10.10.130"
export ORACLE_PORT="1521"
export ORACLE_SERVICE="openclaw"
```

### Example 4: YAML Configuration File (Advanced)

Create `~/.oracle-memory/embedding_config.yaml`:

```yaml
embedding:
  source: auto
  
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

fallback_chain: [lmstudio, ollama, openai]

oracle:
  user: openclaw
  host: 10.10.10.130
  port: 1521
  service: openclaw
```

Then run scripts (they will auto-detect and use this config).

---

## Migration from Hardcoded Ollama

If you were using the old hardcoded Ollama setup:

1. **Remove old config**: `rm -f ~/.oracle-memory/config.env`
2. **Set new environment**: Choose one of the examples above
3. **Verify connection**: Test embedding generation with your chosen source
4. **Continue usage**: All existing commands work unchanged!

The schema and API reference remain identical; only the embedding service configuration has changed to support multiple sources! 🎉
