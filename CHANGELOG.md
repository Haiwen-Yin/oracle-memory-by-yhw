# Oracle Memory System - Change Log (v0.4.0)

## v0.4.0 (2026-04-29) - JRD + Property Graph + Oracle Text Integration

### 🆕 New Features

- **Oracle Text Full-Text Search**
  - ✅ CTX CONTEXT index created on MEMORIES.CONTENT
  - ✅ CTX CONTEXT index created on MEMORY_NODES.LABEL
  - ✅ CONTAINS() keyword search with relevance scoring (SCORE())
  - ✅ Chinese character search works (basic lexer)
  - ✅ Boolean operators: AND, OR, NOT
  - ✅ Wildcard search with prefix matching (%pattern%)
  - ✅ Combined text + vector + graph queries verified

- **Three-Layer Search Architecture**
  - ✅ Text Search (Oracle Text CONTAINS)
  - ✅ Vector Search (VECTOR_DISTANCE)
  - ✅ Graph Search (SQL/PGQ + Relationship Traversal)

### 🔧 Improvements

- Updated SKILL.md with Oracle Text integration section
- Updated README.md with v0.4.1 title and description
- Added search capabilities matrix and architecture diagram

### ⚠️ Known Limitations

- **DBMS_SEARCH.FIND()**: Has DRG-13600 bug in Oracle 23.26.1.0.0
  - Workaround: Use traditional CTX CONTAINS() approach
- **CHINESE_VGRAM_LEXER**: Not available in this Oracle build
  - Basic lexer handles Chinese at character level
  - For better tokenization, wait for Oracle Text patch



### 🆕 New Features

- **JRD Implementation (Completed)**
  - ✅ Created 6 JSON decomposition relationship tables
  - ✅ Implemented 5 JRD views with nested properties
  - ✅ JSON data migrated from CLOB columns to structured tables
  - ✅ Discovered JRD limitation: dual FK nesting not supported (ORA-42607)
  - ✅ Implemented workaround: JSON SQL views (JSON_OBJECT + JSON_ARRAYAGG)

- **Property Graph Implementation (Completed)**
  - ✅ Created Oracle 26ai native Property Graph (MEMORY_PROPERTY_GRAPH)
  - ✅ SQL/PGQ graph queries verified (single-hop + two-hop traversal)
  - ✅ Graph traversal views created (MEMORY_GRAPH_V + MEMORY_GRAPH_JSON_V)
  - ✅ Bidirectional edge traversal (outgoing + incoming)

- **JSON Decomposition Relationship Tables**
  - ✅ MEMORY_NODE_PROPERTIES (decomposed from MEMORY_NODES.PROPERTIES)
  - ✅ MEMORY_EDGE_PROPERTIES (decomposed from MEMORY_EDGES.PROPERTIES)
  - ✅ MEMORY_NODE_TAGS (decomposed from node tags)
  - ✅ MEMORY_CONTENT_FIELDS (decomposed from MEMORIES.CONTENT)
  - ✅ MEMORY_TAG_ITEMS (decomposed from MEMORIES.TAGS)
  - ✅ MEMORY_METADATA_FIELDS (decomposed from MEMORIES.METADATA)

- **Foreign Key Constraints**
  - ✅ MEMORY_RELATIONSHIPS → MEMORY_NODES (FK_MR_SOURCE_NODE)
  - ✅ MEMORY_RELATIONSHIPS → MEMORY_NODES (FK_MR_TARGET_NODE)

- **Auxiliary Indexes (Complete Coverage)**
  - ✅ idx_memory_nodes_type (NODE_TYPE)
  - ✅ idx_node_props_node (NODE_ID)
  - ✅ idx_edge_props_edge (EDGE_ID)
  - ✅ idx_tag_items_mem (MEMORY_ID)
  - ✅ idx_content_fields_mem (MEMORY_ID)
  - ✅ idx_meta_fields_mem (MEMORY_ID)

- **Partition Strategy (Unified Design)**
  - ✅ MEMORIES: LIST(PRIORITY) + RANGE(CREATED_AT) by quarter
  - ✅ MEMORY_NODES: LIST(NODE_TYPE) single layer
  - ✅ MEMORY_EDGES: LIST(EDGE_TYPE) single layer
  - ✅ MEMORY_RELATIONSHIPS: LIST(RELATIONSHIP_TYPE) single layer

### 🔧 Improvements

- **Vector Search Diagnostics**
  - ✅ Root cause identified: core data embeddings are NULL
  - ✅ VECTOR_DISTANCE function verified working correctly
  - ✅ Correct syntax documented (subquery reference, not CAST)
  - ⚠️ HNSW vector index creation blocked by Oracle 23.26.1.0.0 limitations

- **JRD View Enhancement**
  - ✅ MEMORY_NODES_JDV now includes nested properties
  - ✅ MEMORY_EDGES_JDV now includes nested properties
  - ✅ Properties accessible via JSON_VALUE/JSON_QUERY

- **Graph Traversal Views**
  - ✅ MEMORY_GRAPH_V: Structured view with outgoing/incoming/properties
  - ✅ MEMORY_GRAPH_JSON_V: Pure JSON view for API consumption
  - ✅ Bidirectional edge support (outgoing + incoming)

### ⚠️ Known Limitations

- **HNSW Vector Index**
  - ONC.VECTOR_INDEX → ORA-02327 (VECTOR column is LOB type)
  - CREATE VECTOR INDEX → ORA-02158 (SQLcl doesn't recognize syntax)
  - DBMS_VECTOR.CREATE_INDEX → idx_organization has no valid values
  - Status: Waiting for Oracle patch or upgrade

- **JRD Dual FK Nesting**
  - ORA-42607: JRD doesn't support multiple FK references to same parent
  - @link annotation not recognized in 26ai (ORA-24558)
  - Workaround: Use JSON SQL views instead

- **Core Data Embeddings**
  - Nodes 1-5 and Memories 1-6 have NULL embeddings
  - Need to generate embeddings via LM Studio/external API
  - Status: Pending batch embedding generation

### 📝 Documentation Updates

- SKILL.md: Complete rewrite for v0.4.0 with JRD + Property Graph sections
- README.md: Full system architecture updated with three-layer design
- CHANGELOG.md: Comprehensive v0.4.0 change documentation
- references/partition-strategy.md: Multi-table unified strategy added

---

## v0.3.1 (2026-04-23) - Production Grade Partition Strategy & Testing

### 🆕 New Features

- **Table Partitioning Strategy**
  - ✅ LIST + RANGE SUBPARTITIONING production testing completed
  - ✅ SUBPARTITION TEMPLATE support verified
  - ⚠️ STORE IN at PARTITION level limitation discovered (ORA-02216)
  
- **Production Testing Results**
  - Oracle AI DB 26ai Enterprise Edition 23.26.1.0.0 validated
  - SQLcl v26.1 connection tested successfully
  - Partition structure: ACTIVE_VALS → P1, P2; INACTIVE_VALS → P1, P2

- **Documentation Updates**
  - Full English documentation (README.md & SKILL.md)
  - System Architecture Overview added
  - Apache 2.0 License included

### 🔧 Improvements

- Updated partition strategy documentation with comprehensive test results
- Added production environment recommendations and performance expectations
- Clarified STORE IN limitations and workarounds
- Enhanced Active Data Guard documentation (Redo Logs instead of WAL)

### 📝 Documentation Updates

- SKILL.md: Complete rewrite in English with v0.3.1 testing section
- README.md: Full system architecture overview added
- references/partition-strategy.md: Comprehensive implementation guide updated
- property-graph-integration-test-report.md: PG integration test results included

---

## v0.3.0 (2026-04-22) - Active Data Guard & Embedding Management

### 🆕 New Features

- **Active Data Guard Deployment**
  - Primary/Standby architecture design documented
  - Read-write separation optimization procedures
  - Failover/switchover operational procedures
  
- **Embedding Model Management**
  - Multi-model hot-switching support (bge-m3, nomic-embed-text)
  - Automatic dimension adaptation mechanism
  - Model registry & metadata tracking

### 🔧 Improvements

- CLOB + TO_VECTOR() method for vector import implementation
- Dynamic embedding generation scripts
- Dimension validation before queries execution

---

## v0.2.0 (2026-04-15) - Initial Release

- Basic memory system implementation completed
- Single model support (bge-m3 only)
- Active Data Guard planning phase initiated
