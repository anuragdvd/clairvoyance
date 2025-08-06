import asyncio
import sys
from . import main

if __name__ == "__main__":
    # This module should no longer be called directly as subprocess
    # Instead, use the session manager through the main FastAPI app
    print("Warning: This module is deprecated for direct execution.", file=sys.stderr)
    print("Use the FastAPI app with session manager instead.", file=sys.stderr)
    print("Direct execution is only supported for testing purposes.", file=sys.stderr)
    
    # Still allow direct execution for testing/debugging
    asyncio.run(main())