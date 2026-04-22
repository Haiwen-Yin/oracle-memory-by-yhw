#!/usr/bin/env python3
"""
Memory Read/Write Splitter - Smart query routing for ADG high availability
Version: 0.3.0 Enhanced Schema Edition
Author: Haiwen Yin (胖头鱼 🐟)
Purpose: Automatically route queries to appropriate database connection

Features:
- Write operations always routed to primary (mandatory)
- Read operations prefer standby (load balancing + failover protection)
- Automatic fallback to primary if standby unavailable
"""


class MemoryReadSplitter:
    """Smart query router for Oracle AI Database Memory System with ADG."""
    
    def __init__(self, primary_conn="openclaw@//10.10.10.130:1521/openclaw", 
                 standby_conn="openclaw@//10.10.10.131:1521/openclaw_standby"):
        """Initialize the read splitter.
        
        Args:
            primary_conn (str): Primary database connection string
            standby_conn (str): Standby database connection string for reads
        """
        self.primary_conn = primary_conn
        self.standby_conn = standby_conn
    
    def execute_write(self, sql):
        """Execute write operation on primary database.
        
        Args:
            sql (str): SQL statement to execute
            
        Returns:
            dict: Terminal execution result
        """
        
        
        # Write operations MUST go to primary for data consistency
        result = terminal(
            f"/root/sqlcl/bin/sql-mcp.sh {self.primary_conn} << 'EOF'\n{sql}\nCOMMIT;\nEXIT;",
            timeout=60
        )
        
        return result
    
    def execute_read(self, sql):
        """Execute read operation on standby database (preferred).
        
        Args:
            sql (str): SQL statement to execute
            
        Returns:
            dict: Terminal execution result
        """
        
        
        try:
            # Try standby first for load balancing
            result = terminal(
                f"/root/sqlcl/bin/sql-mcp.sh {self.standby_conn} << 'EOF'\n{sql}\nEXIT;",
                timeout=60
            )
            
            if "error" in result.get('output', '').lower() or result.get('exit_code') != 0:
                # Standby query failed, will be retried on primary by execute_query
                return None
                
            return result
            
        except Exception as e:
            print(f"⚠️ Standby read failed: {e}")
            return None
    
    def execute_query(self, sql, prefer_standby=True):
        """Smart query routing based on operation type.
        
        Args:
            sql (str): SQL statement to execute
            prefer_standby (bool): Whether to prefer standby for reads
            
        Returns:
            dict: Terminal execution result
        """
        
        
        # Normalize SQL for detection
        sql_upper = sql.upper().strip()
        
        # Write operations MUST go to primary (mandatory)
        write_keywords = ['INSERT', 'UPDATE', 'DELETE', 'MERGE', 'CREATE', 'DROP', 
                          'ALTER', 'TRUNCATE']
        
        if any(kw in sql_upper for kw in write_keywords):
            print(f"📝 Write detected - routing to PRIMARY (mandatory)")
            return self.execute_write(sql)
        
        # Read operations - configurable preference
        elif prefer_standby:
            print(f"📖 Read detected - attempting STANDBY first (load balancing)")
            
            try:
                result = self.execute_read(sql)
                
                if result and "error" not in result.get('output', '').lower():
                    return result
                    
            except Exception as e:
                print(f"⚠️ Standby query failed: {e}")
            
            # Fallback to primary if standby unavailable
            print("🔄 Fallback - routing to PRIMARY")
            return self.execute_write(sql)  # Reuse execute for read fallback
        
        else:
            # Always use primary
            print(f"📖 Read detected - using PRIMARY (no standby preference)")
            return self.execute_write(sql)


# Usage examples and command-line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Memory Read/Write Splitter')
    parser.add_argument('--primary', default='openclaw@//10.10.10.130:1521/openclaw',
                       help='Primary database connection string')
    parser.add_argument('--standby', default='openclaw@//10.10.10.131:1521/openclaw_standby',
                       help='Standby database connection string')
    
    args = parser.parse_args()
    
    splitter = MemoryReadSplitter(
        primary_conn=args.primary,
        standby_conn=args.standby
    )
    
    print("=" * 70)
    print("Memory Read/Write Splitter v0.3.0")
    print(f"Primary: {args.primary}")
    print(f"Standby: {args.standby}")
    print("=" * 70)
    
    # Interactive mode for query execution
    print("\nEnter SQL to execute (or 'quit' to exit):")
    while True:
        try:
            sql = input("> ")
            if sql.lower() == 'quit':
                break
            
            result = splitter.execute_query(sql)
            
            if result.get('output'):
                output = result['output']
                # Show first 10 lines of output (truncated for readability)
                lines = output.split('\n')[:10]
                print('\n'.join(lines))
                
                if len(output.split('\n')) > 10:
                    print(f"... ({len(output.split(chr(10))) - 10} more lines)")
            
            exit_code = result.get('exit_code', -1)
            if exit_code != 0:
                print(f"❌ Query failed with exit code {exit_code}")
                
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except EOFError:
            print("\n\nExiting...")
            break
    
    print("=" * 70)
    print("Memory Read/Write Splitter completed successfully!")
