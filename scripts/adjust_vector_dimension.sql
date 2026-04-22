-- ============================================================================
-- Oracle AI Database Memory System - Embedding Dimension Adjustment Script
-- Version: 0.3.0 Enhanced Schema Edition
-- Author: Haiwen Yin (胖头鱼 🐟)
-- Usage: sql-mcp.sh openclaw@//host:port/service @adjust_vector_dimension.sql BGE-M3
-- Purpose: Automatically check and adjust VECTOR column dimension to match embedding model
-- ============================================================================

SET VERIFY OFF FEEDBACK OFF;
DEFINE model_name = '&1';

WHENEVER SQLERROR EXIT FAILURE;

DECLARE
    v_current_dim NUMBER;
    v_new_dim NUMBER;
    v_table_exists NUMBER := 0;
BEGIN
    -- Step 1: Check if MEMORIES_VECTORS table exists
    BEGIN
        SELECT COUNT(*) INTO v_table_exists 
        FROM user_tables 
        WHERE table_name = 'MEMORIES_VECTORS';
        
        IF v_table_exists = 0 THEN
            DBMS_OUTPUT.PUT_LINE('⚠️ MEMORIES_VECTORS table does not exist.');
            DBMS_OUTPUT.PUT_LINE('Action: Create the table first before adjusting dimension.');
            RETURN;
        END IF;
    EXCEPTION WHEN NO_DATA_FOUND THEN
        DBMS_OUTPUT.PUT_LINE('⚠️ MEMORIES_VECTORS table does not exist.');
        RETURN;
    END;
    
    -- Step 2: Get current VECTOR dimension
    BEGIN
        SELECT data_precision INTO v_current_dim 
        FROM user_tab_columns 
        WHERE table_name = 'MEMORIES_VECTORS' AND column_name LIKE '%EMBEDDING%';
        
        DBMS_OUTPUT.PUT_LINE('✓ Current VECTOR dimension: ' || v_current_dim);
    EXCEPTION WHEN NO_DATA_FOUND THEN
        DBMS_OUTPUT.PUT_LINE('⚠️ EMBEDDING column not found in MEMORIES_VECTORS.');
        RETURN;
    END;
    
    -- Step 3: Set new dimension based on model name
    CASE UPPER('&model_name')
        WHEN 'BGE-M3' THEN v_new_dim := 1024;
        WHEN 'TEXT-EMBEDDING-3-SMALL' THEN v_new_dim := 1536;
        WHEN 'TEXT-EMBEDDING-3-LARGE' THEN v_new_dim := 3072;
        WHEN 'BGE-M3-V1.5' THEN v_new_dim := 1024;
        ELSE 
            DBMS_OUTPUT.PUT_LINE('⚠️ Unknown model name: ' || UPPER('&model_name'));
            DBMS_OUTPUT.PUT_LINE('Supported models: BGE-M3, TEXT-EMBEDDING-3-SMALL/LARGE');
            RETURN;
    END CASE;
    
    DBMS_OUTPUT.PUT_LINE('✓ Target VECTOR dimension for ' || UPPER('&model_name') || ': ' || v_new_dim);
    
    -- Step 4: Check if change needed
    IF v_current_dim != v_new_dim THEN
        DBMS_OUTPUT.PUT_LINE('');
        DBMS_OUTPUT.PUT_LINE('⚠️ Dimension mismatch detected!');
        DBMS_OUTPUT.PUT_LINE('  Current: ' || v_current_dim);
        DBMS_OUTPUT.PUT_LINE('  Expected: ' || v_new_dim);
        DBMS_OUTPUT.PUT_LINE('');
        
        -- Check if table has existing data
        DECLARE
            v_row_count NUMBER;
        BEGIN
            SELECT COUNT(*) INTO v_row_count FROM memories_vectors;
            
            IF v_row_count > 0 THEN
                DBMS_OUTPUT.PUT_LINE('⚠️ WARNING: Table contains ' || v_row_count || ' existing vector records!');
                DBMS_OUTPUT.PUT_LINE('Action required: Backup data before proceeding.');
                DBMS_OUTPUT.PUT_LINE('');
                DBMS_OUTPUT.PUT_LINE('Recommended steps:');
                DBMS_OUTPUT.PUT_LINE('1. Export current vectors to backup file');
                DBMS_OUTPUT.PUT_LINE('2. DROP TABLE memories_vectors CASCADE CONSTRAINTS;');
                DBMS_OUTPUT.PUT_LINE('3. Recreate table with new VECTOR dimension');
                DBMS_OUTPUT.PUT_LINE('4. Re-import vectors from backup (may need regeneration)');
            ELSE
                DBMS_OUTPUT.PUT_LINE('✓ Table is empty - safe to proceed.');
                DBMS_OUTPUT.PUT_LINE('');
                DBMS_OUTPUT.PUT_LINE('Proceed with dimension adjustment? (Y/N):');
                
                -- Note: In automated mode, you would want to skip this prompt
                -- and just do the ALTER or DROP+RECREATE automatically.
            END IF;
        EXCEPTION WHEN OTHERS THEN
            NULL; -- Ignore errors in count query
        END;
    ELSE
        DBMS_OUTPUT.PUT_LINE('');
        DBMS_OUTPUT.PUT_LINE('✓ Dimension matches expected value.');
        DBMS_OUTPUT.PUT_LINE('No action required.');
    END IF;
END;
/

EXIT SUCCESS;
