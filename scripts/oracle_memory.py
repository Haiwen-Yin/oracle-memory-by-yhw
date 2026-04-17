#!/usr/bin/env python3
"""
oracle_memory.py - Multi-source Embedding Service for Oracle Memory System

Supports configurable embedding sources: LM Studio, Ollama, OpenAI, Custom HTTP endpoints.
Auto-detection when EMBEDDING_SOURCE="auto".

Environment Variables:
    EMBEDDING_SOURCE   : "lmstudio" | "ollama" | "openai" | "custom" | "auto" (default: auto)
    
    LM Studio:
        LMSTUDIO_BASE_URL      : Base URL (e.g., http://10.10.10.1:12345/v1)
        LMSTUDIO_MODEL         : Model name (e.g., text-embedding-bge-m3)
    
    Ollama:
        OLLAMA_HOST           : Hostname or IP (default: localhost)
        OLLAMA_PORT           : Port (default: 11434)
        OLLAMA_MODEL          : Model name (default: bge-m3)
    
    OpenAI:
        OPENAI_API_KEY        : API key (sk-...)
        OPENAI_MODEL          : Model name (default: text-embedding-ada-002)
    
    Custom:
        CUSTOM_EMBEDDING_URL  : Full URL to embedding endpoint
        CUSTOM_EMBEDDING_MODEL: Model name for custom API
        CUSTOM_API_KEY        : Optional authentication token

Usage:
    python oracle_memory.py embed "text to embed" --source lmstudio --model bge-m3
    python oracle_memory.py test-connection  # Test all configured sources
"""

import os
import sys
import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple, Any


class EmbeddingService:
    """Unified embedding service supporting multiple backends."""
    
    def __init__(self):
        self.source = os.environ.get("EMBEDDING_SOURCE", "auto").lower()
        self._active_source = None  # Will be set during auto-detection
        
    def detect_active_source(self) -> str:
        """Auto-detect available embedding source based on environment variables."""
        
        # Try LM Studio first (if configured)
        if self.source == "auto" or self.source == "lmstudio":
            base_url = os.environ.get("LMSTUDIO_BASE_URL")
            model = os.environ.get("LMSTUDIO_MODEL", "text-embedding-bge-m3")
            
            if base_url:
                try:
                    # Test connection
                    req = urllib.request.Request(
                        f"{base_url}/models",
                        method="GET"
                    )
                    
                    with urllib.request.urlopen(req, timeout=5) as response:
                        if response.status == 200:
                            self._active_source = "lmstudio"
                            return "lmstudio"
                except (urllib.error.URLError, TimeoutError):
                    pass
        
        # Try Ollama second (if configured)
        if self.source == "auto" or self.source == "ollama":
            host = os.environ.get("OLLAMA_HOST", "localhost")
            port = os.environ.get("OLLAMA_PORT", "11434")
            
            try:
                req = urllib.request.Request(
                    f"http://{host}:{port}/api/tags",
                    method="GET"
                )
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        self._active_source = "ollama"
                        return "ollama"
            except (urllib.error.URLError, TimeoutError):
                pass
        
        # Try OpenAI third (if API key set)
        if self.source == "auto" or self.source == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
            
            if api_key:
                try:
                    req = urllib.request.Request(
                        "https://api.openai.com/v1/models",
                        method="GET",
                        headers={"Authorization": f"Bearer {api_key}"}
                    )
                    
                    with urllib.request.urlopen(req, timeout=5) as response:
                        if response.status == 200:
                            self._active_source = "openai"
                            return "openai"
                except (urllib.error.URLError, TimeoutError):
                    pass
        
        # All sources failed
        raise RuntimeError(
            f"No available embedding source. Tried: LM Studio, Ollama, OpenAI.\n"
            f"Please set one of these environment variables:\n"
            f"  - EMBEDDING_SOURCE=lmstudio + LMSTUDIO_BASE_URL\n"
            f"  - EMBEDDING_SOURCE=ollama + OLLAMA_HOST\n"
            f"  - EMBEDDING_SOURCE=openai + OPENAI_API_KEY\n"
        )
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for input text using configured source."""
        
        # Auto-detect if needed
        if self.source == "auto":
            self.detect_active_source()
        
        active = self._active_source or self.source
        
        try:
            if active == "lmstudio":
                return self._lmstudio_embed(text)
            elif active == "ollama":
                return self._ollama_embed(text)
            elif active == "openai":
                return self._openai_embed(text)
            elif active == "custom":
                return self._custom_embed(text)
            else:
                raise ValueError(f"Unknown embedding source: {active}")
                
        except Exception as e:
            # If auto-detection failed, try next source
            if self.source == "auto":
                print(f"[WARN] {active} failed: {e}", file=sys.stderr)
                return self._try_next_source(text)
            else:
                raise RuntimeError(f"Embedding generation failed for {active}: {e}")
    
    def _lmstudio_embed(self, text: str) -> List[float]:
        """Generate embedding using LM Studio API."""
        base_url = os.environ.get("LMSTUDIO_BASE_URL", "http://localhost:12345/v1")
        model = os.environ.get("LMSTUDIO_MODEL", "text-embedding-bge-m3")
        
        req_data = json.dumps({
            "model": model,
            "input": text
        }).encode('utf-8')
        
        req = urllib.request.Request(
            f"{base_url}/embeddings",
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        if "data" not in result or len(result["data"]) == 0:
            raise RuntimeError(f"Invalid LM Studio response format: {result}")
        
        return result["data"][0]["embedding"]
    
    def _ollama_embed(self, text: str) -> List[float]:
        """Generate embedding using Ollama API."""
        host = os.environ.get("OLLAMA_HOST", "localhost")
        port = os.environ.get("OLLAMA_PORT", "11434")
        model = os.environ.get("OLLAMA_MODEL", "bge-m3")
        
        req_data = json.dumps({
            "model": model,
            "input": text
        }).encode('utf-8')
        
        req = urllib.request.Request(
            f"http://{host}:{port}/api/embed",
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        if "embeddings" not in result or len(result["embeddings"]) == 0:
            raise RuntimeError(f"Invalid Ollama response format: {result}")
        
        return result["embeddings"][0]
    
    def _openai_embed(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        api_key = os.environ.get("OPENAI_API_KEY")
        model = os.environ.get("OPENAI_MODEL", "text-embedding-ada-002")
        
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set for OpenAI embedding service")
        
        req_data = json.dumps({
            "model": model,
            "input": text
        }).encode('utf-8')
        
        req = urllib.request.Request(
            "https://api.openai.com/v1/embeddings",
            data=req_data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        if "data" not in result or len(result["data"]) == 0:
            raise RuntimeError(f"Invalid OpenAI response format: {result}")
        
        return result["data"][0]["embedding"]
    
    def _custom_embed(self, text: str) -> List[float]:
        """Generate embedding using custom HTTP endpoint."""
        url = os.environ.get("CUSTOM_EMBEDDING_URL")
        model = os.environ.get("CUSTOM_EMBEDDING_MODEL", "custom-model")
        api_key = os.environ.get("CUSTOM_API_KEY")
        
        if not url:
            raise RuntimeError("CUSTOM_EMBEDDING_URL not set for custom embedding service")
        
        req_data = json.dumps({
            "model": model,
            "input": text
        }).encode('utf-8')
        
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        req = urllib.request.Request(
            url,
            data=req_data,
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        # Custom endpoints may have different response formats
        if "data" in result and len(result["data"]) > 0:
            return result["data"][0]["embedding"]
        elif "embeddings" in result and len(result["embeddings"]) > 0:
            return result["embeddings"][0]
        else:
            raise RuntimeError(f"Unknown custom embedding response format: {result}")
    
    def _try_next_source(self, text: str) -> List[float]:
        """Try the next available source in fallback chain."""
        
        # Simple fallback logic for auto mode
        if self._active_source == "lmstudio":
            return self._ollama_embed(text)  # Try Ollama next
        elif self._active_source == "ollama":
            return self._openai_embed(text)  # Try OpenAI next
        else:
            raise RuntimeError("All embedding sources exhausted")


def main():
    """CLI interface for testing and generating embeddings."""
    
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    service = EmbeddingService()
    
    cmd = sys.argv[1]
    
    if cmd == "embed":
        # Generate embedding for input text
        if len(sys.argv) < 3:
            print("Usage: python oracle_memory.py embed \"text to embed\"")
            sys.exit(1)
        
        text = sys.argv[2]
        
        try:
            vector = service.get_embedding(text)
            
            # Output format options:
            if len(sys.argv) > 3 and sys.argv[3] == "--json":
                print(json.dumps({
                    "vector_length": len(vector),
                    "dimensions": vector[:10],  # First 10 dims for preview
                    "full_vector": vector
                }))
            else:
                print(f"Generated {len(vector)}-dimensional embedding:")
                print(f"[{', '.join(f'{x:.6f}' for x in vector[:20])}...]")
                
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif cmd == "test-connection":
        """Test connection to configured embedding sources."""
        
        print("Testing available embedding sources...")
        print("=" * 50)
        
        # Test LM Studio
        lmstudio_url = os.environ.get("LMSTUDIO_BASE_URL", "")
        if lmstudio_url:
            try:
                req = urllib.request.Request(
                    f"{lmstudio_url}/models",
                    method="GET"
                )
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        print("✅ LM Studio: Connected")
                        print(f"   URL: {lmstudio_url}")
                    else:
                        print(f"❌ LM Studio: Failed (status {response.status})")
            except Exception as e:
                print(f"❌ LM Studio: Not available ({e})")
        
        # Test Ollama
        ollama_host = os.environ.get("OLLAMA_HOST", "localhost")
        ollama_port = os.environ.get("OLLAMA_PORT", "11434")
        try:
            req = urllib.request.Request(
                f"http://{ollama_host}:{ollama_port}/api/tags",
                method="GET"
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    print("✅ Ollama: Connected")
                    print(f"   URL: http://{ollama_host}:{ollama_port}")
                else:
                    print(f"❌ Ollama: Failed (status {response.status})")
        except Exception as e:
            print(f"❌ Ollama: Not available ({e})")
        
        # Test OpenAI
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        if openai_key:
            try:
                req = urllib.request.Request(
                    "https://api.openai.com/v1/models",
                    method="GET",
                    headers={"Authorization": f"Bearer {openai_key}"}
                )
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        print("✅ OpenAI API: Connected")
                        print(f"   Key set: ✓")
                    else:
                        print(f"❌ OpenAI API: Failed (status {response.status})")
            except Exception as e:
                print(f"❌ OpenAI API: Not available ({e})")
        
        # Try auto-detection
        try:
            active_source = service.detect_active_source()
            print("=" * 50)
            print(f"✅ Auto-detection: Using {active_source}")
        except Exception as e:
            print("=" * 50)
            print(f"❌ No available sources ({e})")


if __name__ == "__main__":
    main()
