"""Entry point for email indexing CLI."""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the indexer
from src.index_emails import main

if __name__ == "__main__":
    main()
