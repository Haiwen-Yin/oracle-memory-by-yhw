# Oracle Memory Schema Optimization Guide

## 📊 **Current Structure Analysis**

### Existing Tables (Production State)

| Table | Rows | Columns | Indexes | Status |
|-------|------|---------|---------|--------|
| `MEM_VECTORS` | 6 | ID, DENSE_VECTOR(VECTOR), METADATA(JSON) | ✓ PK<br/>✓ Vector index | ✅ Good for search |
| `GRAPH_CONCEPTS` | 5 | CONCEPT_ID, NAME, CATEGORY, DESCRIPTION | ✓ PK | ✅ OK |
| `GRAPH_RELATIONS` | 4 | RELATION_ID, SRC/DST_ID, TYPE, WEIGHT | ✓ PK + FK | ✅ OK |

### Identified Optimization Opportunities

1. ❌ **No time-based tracking** - Cannot order by creation date or implement TTL (time-to-live)
2. ❌ **JSON field not queried efficiently** - No indexes on category/tags for filtering
3. ❌ **No access statistics** - Cannot track popular memories or cold data
4. ⚠️ **Vector index parameters not optimized** - Default HNSW settings may not be ideal

---

## 🚀 **Optimization Recommendations**

### **Priority 1: Add Time & Access Tracking (Non-Destructive)** ✅ Recommended

Adds columns without dropping existing tables or data.

#### What it adds:
- `created_at TIMESTAMP` - Auto-set on insert, for time-based queries
- `access_count NUMBER` - Track how many times memory is accessed
- `last_accessed TIMESTAMP` - Last search/write timestamp

#### Benefits:
- Query "recent memories": `WHERE created_at > SYSDATE - 7`
- Find "popular memories": ORDER BY access_count DESC
- Implement TTL cleanup of old data
- Analytics on usage patterns

#### Implementation:
```sql
-- Run this script (non-destructive)
ALTER TABLE mem_vectors ADD (created_at TIMESTAMP DEFAULT SYSTIMESTAMP);
CREATE INDEX mem_vectors_created_idx ON mem_vectors(created_at DESC);
```

---

### **Priority 2: Virtual Columns for Common Filters** ⚡ High Impact

Create virtual columns that extract from JSON metadata.

#### What it adds:
- `category VARCHAR2(50) GENERATED ALWAYS AS (JSON_VALUE(metadata, '$.category')) VIRTUAL`
- `tags VARCHAR2(500) GENERATED ALWAYS AS (JSON_VALUE(metadata, '$.tags')) VIRTUAL`

#### Benefits:
- Index virtual columns for fast filtering by category/tags
- No storage overhead (computed on-the-fly)
- Cleaner SQL queries without JSON_VALUE() function calls

#### Implementation:
```sql
ALTER TABLE mem_vectors ADD (
  category VARCHAR2(50) GENERATED ALWAYS AS (JSON_VALUE(metadata, '$.category')) VIRTUAL,
  tags     VARCHAR2(500) GENERATED ALWAYS AS (JSON_VALUE(metadata, '$.tags')) VIRTUAL
);

CREATE INDEX mem_vectors_cat_idx ON mem_vectors(category);
CREATE INDEX mem_vectors_tags_idx ON mem_vectors(tags);
```

---

### **Priority 3: Optimize Vector Index Parameters** 🔧 Advanced

Tune HNSW index for better search performance.

#### Current settings (default):
- `INDEX_TYPE HNSW` with default parameters

#### Recommended tuning:
- `INDEX_LENGTH 100` - M parameter (connectivity)
- `EFFECTIVE_SIZE 2048` - For larger datasets
- `DISTANCE_FUNCTION COSINE` or `EUCLIDEAN` based on use case

#### Implementation:
```sql
BEGIN
  DBMS_VECTOR_DATABASE.CREATE_INDEX(
    table_name       => 'MEM_VECTORS',
    column_name      => 'DENSE_VECTOR',
    index_type       => 'VECTOR',
    index_parameters => 'INDEX_TYPE HNSW, INDEX_LENGTH 100, DISTANCE_FUNCTION COSINE'
  );
END;
/
```

---

## 📋 **Optimization Scripts**

### Script A: Non-Destructive Add Columns (Safe)

```sql
SET SERVEROUTPUT ON SIZE 1000000

DECLARE
  l_col_count NUMBER;
BEGIN
  -- Check and add created_at column
  SELECT COUNT(*) INTO l_col_count FROM user_tab_cols 
    WHERE table_name = 'MEM_VECTORS' AND column_name = 'CREATED_AT';
  
  IF l_col_count = 0 THEN
    EXECUTE IMMEDIATE 'ALTER TABLE mem_vectors ADD (created_at TIMESTAMP DEFAULT SYSTIMESTAMP)';
    DBMS_OUTPUT.PUT_LINE('✅ Added created_at column');
    
    BEGIN
      EXECUTE IMMEDIATE 'CREATE INDEX mem_vectors_created_idx ON mem_vectors(created_at DESC)';
      DBMS_OUTPUT.PUT_LINE('✅ Created created_at index');
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
  ELSE
    DBMS_OUTPUT.PUT_LINE('ℹ️  created_at column already exists');
  END IF;
END;
/
```

### Script B: Add Virtual Columns (High Impact)

```sql
SET SERVEROUTPUT ON SIZE 1000000

DECLARE
  l_col_count NUMBER;
BEGIN
  -- Check and add virtual columns
  SELECT COUNT(*) INTO l_col_count FROM user_tab_cols 
    WHERE table_name = 'MEM_VECTORS' AND column_name = 'CATEGORY';
  
  IF l_col_count = 0 THEN
    EXECUTE IMMEDIATE 'ALTER TABLE mem_vectors ADD (category VARCHAR2(50) GENERATED ALWAYS AS (JSON_VALUE(metadata, ''$.category'')) VIRTUAL)';
    DBMS_OUTPUT.PUT_LINE('✅ Added category virtual column');
    
    BEGIN
      EXECUTE IMMEDIATE 'CREATE INDEX mem_vectors_cat_idx ON mem_vectors(category)';
      DBMS_OUTPUT.PUT_LINE('✅ Created category index');
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
  ELSE
    DBMS_OUTPUT.PUT_LINE('ℹ️  category virtual column already exists');
  END IF;
END;
/
```

### Script C: Full Optimization (Destructive - Backup First!)

⚠️ **WARNING**: This drops the existing table! Only use if you have backups.

```sql
SET SERVEROUTPUT ON SIZE 1000000

DECLARE
  l_result CLOB;
BEGIN
  -- Backup data first!
  CREATE TABLE mem_vectors_backup AS SELECT * FROM mem_vectors;
  DBMS_OUTPUT.PUT_LINE('✅ Data backed up to mem_vectors_backup');
  
  -- Drop old table
  EXECUTE IMMEDIATE 'DROP TABLE mem_vectors CASCADE CONSTRAINTS';
  
  -- Create optimized table from scratch
  CREATE TABLE mem_vectors (
    id            VARCHAR2(40) PRIMARY KEY,
    dense_vector  VECTOR,
    metadata      JSON CHECK (metadata IS JSON),
    category      VARCHAR2(50) GENERATED ALWAYS AS (JSON_VALUE(metadata, '$.category')) VIRTUAL,
    tags          VARCHAR2(500) GENERATED ALWAYS AS (JSON_VALUE(metadata, '$.tags')) VIRTUAL,
    created_at    TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    access_count  NUMBER DEFAULT 0 NOT NULL,
    last_accessed TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
  );
  
  -- Create indexes
  EXECUTE IMMEDIATE 'CREATE INDEX mem_vectors_cat_idx ON mem_vectors(category)';
  EXECUTE IMMEDIATE 'CREATE INDEX mem_vectors_tags_idx ON mem_vectors(tags)';
  EXECUTE IMMEDIATE 'CREATE INDEX mem_vectors_created_at_idx ON mem_vectors(created_at DESC)';
  
  -- Create vector index with optimized parameters
  l_result := DBMS_VECTOR_DATABASE.CREATE_INDEX(
    table_name       => 'MEM_VECTORS',
    column_name      => 'DENSE_VECTOR',
    index_type       => 'VECTOR',
    index_parameters => 'INDEX_TYPE HNSW, INDEX_LENGTH 100'
  );
  
  COMMIT;
  DBMS_OUTPUT.PUT_LINE('✅ MEM_VECTORS fully optimized!');
END;
/
```

---

## 🎯 **Recommended Implementation Plan**

### Phase 1: Safe Additions (Priority 1) ✅
- Add `created_at` column and index
- No risk to existing data
- Immediate benefits for time-based queries

### Phase 2: Virtual Columns (Priority 2) ⚡
- Add virtual columns for category/tags
- Create indexes on virtual columns
- Enables fast filtering without storage overhead

### Phase 3: Vector Index Tuning (Priority 3) 🔧
- Rebuild vector index with optimized parameters
- Best done during low-traffic periods
- Requires careful testing before production use

---

## 📈 **Performance Comparison**

| Query Type | Before Optimization | After Virtual Columns | Improvement |
|------------|-------------------|----------------------|-------------|
| `WHERE category = 'system'` | Full table scan + JSON extraction | Index seek | ~10-100x faster at scale |
| `ORDER BY created_at DESC` | Sort all rows | Index scan | ~5-20x faster |
| Vector similarity search | Default HNSW params | Tuned HNSW | ~20-50% faster top-K |

---

## ⚠️ **Important Considerations**

1. **Backup First**: Always backup data before destructive changes
2. **Test in Staging**: Run optimization scripts in non-production first
3. **Index Maintenance**: Vector indexes may need rebuilding after bulk loads
4. **Storage Impact**: Virtual columns have zero storage overhead; timestamps add ~20 bytes per row
5. **Query Changes**: Existing queries using JSON_VALUE() will continue to work

---

## 🔄 **Rollback Procedures**

### Remove virtual columns:
```sql
ALTER TABLE mem_vectors DROP COLUMN category;
ALTER TABLE mem_vectors DROP COLUMN tags;
DROP INDEX mem_vectors_cat_idx;
DROP INDEX mem_vectors_tags_idx;
```

### Remove time tracking:
```sql
ALTER TABLE mem_vectors DROP COLUMN created_at;
DROP INDEX mem_vectors_created_idx;
```

---

## 📝 **Next Steps**

1. **Review current data**: `SELECT * FROM mem_vectors;`
2. **Choose optimization level**: Safe (Phases 1-2) vs Full (Phase 3)
3. **Backup existing tables**: `CREATE TABLE mem_vectors_backup AS SELECT * FROM mem_vectors;`
4. **Run optimization scripts** in order of priority
5. **Test queries**: Verify performance improvements

---

*Generated by Oracle Memory Optimization Guide v1.0*
