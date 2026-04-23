# Oracle Memory System - Change Log (v0.3.1)

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
