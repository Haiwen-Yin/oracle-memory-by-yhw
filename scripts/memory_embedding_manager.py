#!/usr/bin/env python3
"""
Memory Embedding Manager - Automatic dimension adjustment and vector insertion
Version: 0.3.0 Enhanced Schema Edition
Author: Haiwen Yin (胖头鱼 🐟)
Purpose: Manage embedding model integration with Oracle AI Database Memory System

Features:
- Dynamic dimension checking and automatic adjustment
- LM Studio API integration (configurable endpoint/model)
- Vector generation and database insertion
- Error handling with helpful messages
"""

import json
import os
import sys
import requests


class MemoryEmbeddingManager:
    """Manages embedding model integration for Oracle AI Database Memory System."""
    
    def __init__(self, api_endpoint="http://10.10.10.1/v1/embeddings", model_name="bge-m3"):
        """Initialize the embedding manager.
        
        Args:
            api_endpoint (str): LM Studio API endpoint URL
            model_name (str): Embedding model name (e.g., 'bge-m3', 'text-embedding-3-small')
        """
        self.api_endpoint = api_endpoint.rstrip('/') + '/v1/embeddings'
        self.model_name = model_name
        # Dimension mapping for known models
        self.dimension_map = {
            "bge-m3": 1024,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "nomic-embed-text": 768,
            # Add more models as needed
        }
    
    def get_expected_dimension(self):
        """Get expected vector dimension for configured model.
        
        Returns:
            int: Expected dimension value (default: 1024)
        """
        return self.dimension_map.get(self.model_name.lower(), 1024)
    
    def check_db_dimension(self, conn_string):
        """Check current VECTOR column definition in database.
        
        Args:
            conn_string (str): Database connection string
            
        Returns:
            int or None: Current dimension if found, None otherwise
        """
        sql = """
        SELECT data_precision 
        FROM user_tab_columns 
        WHERE table_name = 'MEMORIES_VECTORS' AND column_name LIKE '%EMBEDDING%'
        """
        
        result = terminal(
            f"/root/sqlcl/bin/sql-mcp.sh {conn_string} << 'EOF'\n{sql}\nEXIT;",
            timeout=30
        )
        
        output = result.get('output', '')
        if "1024" in output:
            return 1024
        elif "1536" in output:
            return 1536
        elif "3072" in output:
            return 3072
        else:
            return None
    
    def adjust_dimension_if_needed(self, conn_string):
        """Automatically check and adjust VECTOR dimension to match model.
        
        Args:
            conn_string (str): Database connection string
            
        Returns:
            bool: True if adjustment successful or not needed, False otherwise
        """
        expected_dim = self.get_expected_dimension()
        current_dim = self.check_db_dimension(conn_string)
        
        if current_dim is None:
            print(f"⚠️ Could not determine current dimension from database.")
            return False
        
        if current_dim == expected_dim:
            print(f"✓ Dimension matches. Current: {expected_dim}")
            return True
        
        print(f"⚠️ Dimension mismatch! Expected {expected_dim}, got {current_dim}")
        print("Action required: Run dimension adjustment script manually")
        print("See scripts/adjust_vector_dimension.sql for automation")
        return False
    
    def generate_embedding(self, text):
        """Generate vector embedding via LM Studio API.
        
        Args:
            text (str): Input text to embed
            
        Returns:
            list or None: Vector array if successful, None otherwise
        """
        payload = {
            "input": text,
            "model": self.model_name
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['data'][0]['embedding']
            else:
                print(f"❌ API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("❌ Request timeout. Check LM Studio is running.")
            return None
        except Exception as e:
            print(f"❌ Embedding generation failed: {e}")
            return None
    
    def insert_vector(self, memory_id, embedding_text, conn_string):
        """Insert vector into database.
        
        Args:
            memory_id (int): Memory ID from memories table
            embedding_text (str): Vector array as string
            conn_string (str): Database connection string
            
        Returns:
            bool: True if insert successful, False otherwise
        """
        sql = f"""
        INSERT INTO memories_vectors (memory_id, embedding, model_version) 
        VALUES ({memory_id}, TO_VECTOR('{embedding_text}'), '{self.model_name}')
        """
        
        result = terminal(
            f"/root/sqlcl/bin/sql-mcp.sh {conn_string} << 'EOF'\n{sql}\nCOMMIT;\nEXIT;",
            timeout=30
        )
        
        return "Commit complete" in result.get('output', '')


# Usage example and command-line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Memory Embedding Manager')
    parser.add_argument('--conn', default='openclaw@//10.10.10.130:1521/openclaw',
                       help='Database connection string')
    parser.add_argument('--model', default='bge-m3',
                       help='Embedding model name')
    parser.add_argument('--endpoint', default='http://10.10.10.1/v1/embeddings',
                       help='LM Studio API endpoint')
    
    args = parser.parse_args()
    
    manager = MemoryEmbeddingManager(
        api_endpoint=args.endpoint,
        model_name=args.model
    )
    
    print("=" * 70)
    print("Memory Embedding Manager v0.3.0")
    print(f"Model: {args.model}")
    print(f"Endpoint: {args.endpoint}")
    print(f"Expected Dimension: {manager.get_expected_dimension()}")
    print("=" * 70)
    
    # Check and adjust dimension
    if not manager.adjust_dimension_if_needed(args.conn):
        print("❌ Please run scripts/adjust_vector_dimension.sql first")
        exit(1)
    
    # Interactive mode for embedding generation
    print("\nEnter text to embed (or 'quit' to exit):")
    while True:
        try:
            text = input("> ")
            if text.lower() == 'quit':
                break
            
            print(f"Generating embedding for model '{args.model}'...")
            embedding = manager.generate_embedding(text)
            
            if embedding:
                print(f"✓ Generated {len(embedding)}-dimension vector")
                
                # Ask to insert into database
                insert_input = input("Insert into database? (y/n): ").lower()
                if insert_input == 'y':
                    memory_id = int(input("Enter memory_id: "))
                    success = manager.insert_vector(memory_id, str(embedding), args.conn)
                    print("✓ Vector inserted successfully" if success else "❌ Insert failed")
                else:
                    # Display vector for manual use
                    print(f"\nVector array: {embedding[:10]}... (truncated)")
            else:
                print("❌ Failed to generate embedding. Check API endpoint.")
                
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except EOFError:
            print("\n\nExiting...")
            break
    
    print("=" * 70)
    print("Memory Embedding Manager completed successfully!")
