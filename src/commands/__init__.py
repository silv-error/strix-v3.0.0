"""
Bot commands (slash and prefix)
"""
from .slash_commands import register_slash_commands
from .prefix_commands import register_prefix_commands

__all__ = ['register_slash_commands', 'register_prefix_commands']
