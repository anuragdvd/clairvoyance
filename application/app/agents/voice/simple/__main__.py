#!/usr/bin/env python3
"""
Entry point for running the voice agent as a module.
This allows the voice agent to be executed with: python -m app.agents.voice.simple
"""

from . import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())