# Oracle Memory System - Change Log (v0.4.0)

## v0.4.1 (2026-05-04) - Task Plan Persistence Integration Edition

### 🆕 New Features: Task Plan System

**Task Plan Management**
- ✅ TASK_PLANS table - Core task planning with status tracking (PENDING/RUNNING/SUCCESS/FAILED/CANCELLED/PAUSED)
- ✅ TASK_STEPS table - Step-by-step execution recording with unique constraints
- ✅ TASK_TOOL_CALLS table - Complete audit trail of all agent tool invocations
- ✅ TASK_DEPENDENCIES table - Task relationship graph for complex workflows

**Breakpoint Recovery System (Core Feature)**
- ✅ TASK_CONTEXT_SNAPSHOTS table - Full state preservation during task execution
- ✅ IS_LATEST flag mechanism - Automatic snapshot versioning for resume capability
- ✅ Auto-snapshot on progress updates - Context preserved every status change
- ✅ Resume API function - Complete agent context restoration after failures

**Historical Learning & Pattern Recognition**
- ✅ search_completed_tasks() API - Query historical task patterns and outcomes
- ✅ Success/failure pattern analysis - Learn from past execution results
- ✅ Task dependency tracking - Identify recurring workflow patterns

### 🔧 API Functions (Python Integration)

| Function | Purpose | Key Features |
|----------|---------|--------------|
| `create_task_plan()` | Create new task with initial snapshot | Auto-saves agent state + conversation history |
| `update_task_progress()` | Update status during execution | Creates auto snapshots on every change |
| `resume_task()` | Restore after interruption | Loads latest snapshot, finds incomplete steps |
| `search_completed_tasks()` | Learn from historical patterns | Returns success metrics and task statistics |

### 📊 Indexing & Performance Optimizations (v0.4.1)

- ✅ 5 database sequences for auto-increment primary keys
- ✅ 9 Task Plan specific indexes for optimal query performance:
  - IDX_TASK_PLANS_STATUS, IDX_TASK_PLANS_TYPE, IDX_TASK_PLANS_CREATED
  - IDX_TASK_STEPS_PLAN, IDX_TASK_STEPS_STATUS
  - IDX_CONTEXT_SNAPSHOT_PLAN (IS_LATEST filter optimization)
  - IDX_TOOL_CALLS_PLAN, IDX_TOOL_CALLS_TIME

### 🔧 Improvements

- **TRIGGER column fix**: Renamed to TRIGGER_REASON in TASK_CONTEXT_SNAPSHOTS table
  - Reason: Oracle reserved word conflict resolution
  - Impact: All references updated for consistency
  
- **Documentation completeness**: SKILL.md fully aligned with database deployment

### ⚠️ Known Limitations

- Same as v0.4.0 (JRD, Vector Index, Oracle Text issues documented)
- TRIGGER column renamed to TRIGGER_REASON - update any external scripts accordingly

---

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
- Added search capabilities matrix and architecture diagram

### ⚠️ Known Limitations

- **DBMS_SEARCH.FIND()**: Has DRG-13600 bug in Oracle 23.26.1.0.0
  - Workaround: Use traditional CTX CONTAINS() approach
- **CHINESE_VGRAM_LEXER**: Not available in this Oracle build
  - Basic lexer handles Chinese at character level
  - For better tokenization, wait for Oracle Text patch


