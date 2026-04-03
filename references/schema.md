# Oracle Memory Schema & API Reference

## Table Structures

### MEM_VECTORS (Vector Memory)
Created via `DBMS_VECTOR_DATABASE.CREATE_VECTOR_TABLE()`.

| Column | Type | Description |
|--|--|--|
| ID | VARCHAR2(40) | Auto-generated GUID |
| DENSE_VECTOR | VECTOR(*,*,DENSE) | Embedding vector (dimension depends on model) |
| METADATA | JSON | `{"text": "...", "category": "...", "tags": "..."}` |

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

## Embedding Service

### Ollama (Recommended for local use)
```bash
# Install and pull model
ollama pull bge-m3

# API endpoint
POST http://localhost:11434/api/embed
Body: {"model": "bge-m3", "input": "text to embed"}
Response: {"embeddings": [[0.1, 0.2, ...]]}
```

### Compatible Models
- `bge-m3` - Best for Chinese, 1024 dimensions
- `nomic-embed-text` - Lightweight, 768 dimensions
- `mxbai-embed-large` - English focused, 1024 dimensions
- Any model that implements Ollama's `/api/embed` endpoint

## Known Issues

1. **UPSERT_VECTORS bug**: Returns ORA-57707 on Oracle 26ai. Use `EXECUTE IMMEDIATE 'INSERT INTO mem_vectors ... VALUES (VECTOR(:1), JSON(:2))'` instead.
2. **VECTOR constructor**: Only works in `EXECUTE IMMEDIATE`, not static PL/SQL.
3. **JSON escaping**: Heredoc in shell can mangle JSON. Script uses Python to write SQL files with proper encoding.

## Network ACL Setup

For Oracle DB to access external embedding services:

```sql
-- Run as SYSDBA
BEGIN
  DBMS_NETWORK_ACL_ADMIN.CREATE_ACL(
    acl => 'oracle_memory_http.xml',
    description => 'HTTP access for Oracle Memory',
    principal => 'YOUR_USER',
    is_grant => TRUE,
    privilege => 'connect'
  );
  DBMS_NETWORK_ACL_ADMIN.ADD_PRIVILEGE(
    acl => 'oracle_memory_http.xml',
    principal => 'YOUR_USER',
    is_grant => TRUE,
    privilege => 'resolve'
  );
  DBMS_NETWORK_ACL_ADMIN.ASSIGN_ACL(
    acl => 'oracle_memory_http.xml',
    host => 'your-ollama-host',
    lower_port => 11434,
    upper_port => 11434
  );
END;
/
```
