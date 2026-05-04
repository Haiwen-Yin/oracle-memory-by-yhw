# Oracle Memory System v0.4.1 - Release Notes

**Release Date**: May 4, 2026  
**Version**: v0.4.1 (Task Plan Integration Edition)  
**Upgrade Level**: Minor - New Features + Improvements  

---

## 🎯 Executive Summary

v0.4.1 introduces the **Task Plan Persistence System**, a critical enhancement for AI Agents that enables:
- **Breakpoint recovery** after task interruptions with full context restoration
- **Historical pattern learning** from completed tasks and their outcomes  
- **Detailed status auditing** of all agent actions and tool invocations

This is essential for long-running operations in production environments where network issues, timeouts, or system failures can interrupt task execution.

---

## 🆕 New Features

### 1. Task Plan Persistence System (5 Core Tables)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `TASK_PLANS` | Task planning and status tracking | PLAN_ID, STATUS, PRIORITY, METADATA |
| `TASK_STEPS` | Step-by-step execution recording | STEP_ORDER, ACTION, RESULT, ERROR_MSG |
| `TASK_CONTEXT_SNAPSHOTS` | **Breakpoint recovery** (critical!) | CONTEXT_DATA, IS_LATEST, NEXT_ACTION |
| `TASK_TOOL_CALLS` | Complete tool audit trail | TOOL_NAME, DURATION_MS, STATUS |
| `TASK_DEPENDENCIES` | Task relationship management | DEPENDENCY_TYPE, CONDITION |

### 2. Breakpoint Recovery API (Core Feature)

**Function**: `resume_task(plan_id)`  
**Purpose**: Restore agent execution exactly where interrupted  

```python
# Usage example:
recovery_info = resume_task("task-123")
# Returns: {context, next_action, incomplete_steps, snapshot_time}
```

**How it works:**
1. Query `TASK_CONTEXT_SNAPSHOTS` for IS_LATEST='Y' snapshots
2. Restore agent_state and conversation_history from CONTEXT_DATA  
3. Identify incomplete steps by checking STEP status
4. Resume execution with NEXT_ACTION as starting point

### 3. Historical Learning API (Pattern Recognition)

**Function**: `search_completed_tasks(query_params)`  
**Purpose**: Learn from past task patterns to avoid repeating mistakes  

```python
# Usage example:
results = search_completed_tasks({
    "type": "deployment", 
    "status": "SUCCESS",
    "keywords": ["performance"]
})
# Returns list with success rate, execution time stats, metadata
```

### 4. Automatic Snapshot Mechanism

**Trigger points for auto-snapshots:**
- ✅ Every task progress update (via `update_task_progress()`)
- ✅ Initial task creation (`create_task_plan()` saves baseline context)
- ✅ On error/failure scenarios (manual triggers supported)

**Snapshot includes:**
```json
{
  "agent_state": { ... },           // Current agent internal state
  "conversation_history": [...],    // Recent conversation window  
  "memory_ids": [],                 // Related memory node references
  "next_action": "...",             // Determined next step
  "created_at": "..."              // Snapshot timestamp
}
```

### 5. Performance Optimizations (v0.4.1)

**New Indexes**: 9 Task Plan specific indexes for optimal query performance  
**Sequences**: 5 auto-increment sequences for primary key generation  

---

## 🔧 Improvements & Fixes

| Item | Description |
|------|-------------|
| TRIGGER Column | Renamed to `TRIGGER_REASON` in TASK_CONTEXT_SNAPSHOTS (Oracle reserved word) |
| Documentation | SKILL.md fully aligned with database deployment |
| Index Coverage | Complete Task Plan index strategy documented and implemented |

---

## ⚠️ Known Limitations (Same as v0.4.0)

### Vector Search
- **HNSW Vector Index**: Cannot create in Oracle 23.26.1.0.0 (ORA-02327, ORA-02158)
- **Workaround**: Use VECTOR_DISTANCE() function with subquery reference

### JRD Views  
- **Dual FK Nesting**: ORA-42607 - JRD doesn't support multiple FK references to same parent
- **@link Annotation**: Not recognized in 26ai (ORA-24558)
- **Workaround**: Use JSON SQL views instead

### Oracle Text
- **DBMS_SEARCH.FIND()**: DRG-13600 bug in Oracle 23.26.1.0.0
- **CHINESE_VGRAM_LEXER**: Not available - basic lexer handles Chinese at character level

---

## 📋 Migration Notes for v0.4.1 Upgraders

### Database Schema Changes Required:

```sql
-- Run these SQL commands to add Task Plan tables:
-- (See SKILL.md for complete DDL)

CREATE TABLE TASK_PLANS (...);
CREATE TABLE TASK_STEPS (...);  
CREATE TABLE TASK_CONTEXT_SNAPSHOTS (...);  -- Note: TRIGGER_REASON, not "TRIGGER"
CREATE TABLE TASK_TOOL_CALLS (...);
CREATE TABLE TASK_DEPENDENCIES (...);

-- Create sequences
CREATE SEQUENCE SEQ_TASK_PLANS START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE SEQ_TASK_STEPS START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE SEQ_CONTEXT_SNAPSHOTS START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE SEQ_TOOL_CALLS START WITH 1 INCREMENT BY 1;  
CREATE SEQUENCE SEQ_TASK_DEPS START WITH 1 INCREMENT BY 1;

-- Create indexes (see SKILL.md for complete list)
```

### Important: TRIGGER Column Rename

⚠️ **Breaking Change**: The TASK_CONTEXT_SNAPSHOTS table uses `TRIGGER_REASON` instead of `"TRIGGER"` due to Oracle reserved word conflict.

**Update any external scripts that reference this column:**
- ❌ Old: `SELECT "TRIGGER" FROM TASK_CONTEXT_SNAPSHOTS`  
- ✅ New: `SELECT TRIGGER_REASON FROM TASK_CONTEXT_SNAPSHOTS`

---

## 📊 Summary Statistics

| Metric | Value |
|--------|-------|
| **New Tables** | 5 (TASK_PLANS, TASK_STEPS, CONTEXT_SNAPSHOTS, TOOL_CALLS, DEPENDENCIES) |
| **New Columns** | ~47 across all Task Plan tables |
| **New Indexes** | 9 Task Plan specific indexes |
| **New Sequences** | 5 auto-increment sequences |
| **New API Functions** | 4 core Python functions (create/update/resume/search) |
| **Documentation Lines Added** | ~300+ lines of SQL, Python, and architectural documentation |

---

## 🚀 Quick Start for Task Plan Features

```python
# 1. Create a new task plan with initial context snapshot
task = create_task_plan(
    plan_name="Production Deployment v2.0",
    plan_type="deployment",
    description="Deploy new features to production environment",
    steps=[{"order": 1, "name": "Backup DB", "action": "..."}]
)

# 2. Agent executes - auto-snapshots created on each step update  
update_task_progress(task["plan_id"], status="RUNNING")

# 3. If interrupted, resume exactly where left off:
recovery = resume_task(task["plan_id"])
print(f"Next action: {recovery['next_action']}")

# 4. After completion, learn from historical patterns:
patterns = search_completed_tasks({"type": "deployment", "status": "SUCCESS"})
```

---

## 📚 Related Documentation

- [SKILL.md](../oracle-memory-by-yhw-v0.4.0/SKILL.md) - Complete system documentation with Task Plan integration  
- [CHANGELOG.md](./CHANGELOG.md) - Full version history and changes
- [README.md](../oracle-memory-by-yhw-v0.4.0/README.md) - System architecture overview

---

**Release Manager**: Haiwen Yin (Pangtouyu / Fat Head Fish)  
**Verification Status**: ✅ All features tested and validated on Oracle AI DB 26ai v23.26.1.0.0
