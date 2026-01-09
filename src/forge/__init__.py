"""
Forge: AI-Powered Software Engineering Platform

A multi-agent system for code analysis, debugging, and improvement.
"""

__version__ = "0.1.0"

from forge.orchestrator import Forge
from forge.config.settings import ForgeSettings

__all__ = ["Forge", "ForgeSettings", "__version__"]
