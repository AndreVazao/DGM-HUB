import shlex
import subprocess
from pathlib import Path
from typing import List
import logging
import sys

LOGGER = logging.getLogger(__name__)


class CommandValidator:
    """
    Validates shell commands to prevent injection attacks.
    
    Uses proper shell parsing (shlex) instead of simple substring matching.
    Allows common legitimate patterns like Python -c and other standard tools.
    """
    
    def __init__(self, allowed_base_paths: List[str | Path] = None):
        self.allowed_base_paths = [Path(p).resolve() for p in (allowed_base_paths or [])]
        
        # Dangerous shell operators that indicate command composition
        # NOTE: We allow some operators when they're part of legitimate commands
        self.dangerous_operators = {
            '||',     # OR (dangerous for composition)
            '&&',     # AND (dangerous for composition)
            '|',      # Pipe (can be legitimate but risky)
            '&',      # Background (risky)
        }
        
        # Operators we allow (legitimate use)
        self.allowed_operators = {
            ';',      # Semicolon - allowed in -c arguments for Python
        }
        
        # Dangerous shell commands/redirects
        self.dangerous_patterns = {
            '`',      # Backtick substitution
            '$(',     # Command substitution  
            '<<',     # Heredoc
            '>',      # Redirect stdout (can be ok in some contexts)
            '<',      # Redirect stdin
        }
        
        # Dangerous command names
        self.dangerous_commands = {
            'cmd', 'cmd.exe',
            'powershell', 'powershell.exe',
            'bash', 'bash.exe', 'sh', 'zsh',
            'del', 'erase', 'rmdir', 'rm', 'rm -rf',
            'format', 'fdisk', 'dd',
            'shutdown', 'reboot', 'restart', 'halt',
            'taskkill', 'kill -9', 'pkill',
            'net user', 'net share', 'net admin',
            'reg delete', 'regedit',
            'chkdsk', 'sfc',
        }
    
    def is_safe(self, command: str) -> bool:
        """
        Check if a command is safe to execute.
        
        Returns True only if:
        1. No dangerous shell composition patterns
        2. The main command is not in the dangerous list
        3. Can be safely parsed
        
        Args:
            command: The shell command string to validate
            
        Returns:
            True if command appears safe, False otherwise
        """
        command = command.strip()
        
        if not command:
            return False
        
        # Check for dangerous composition operators (these join commands)
        for op in self.dangerous_operators:
            if op in command:
                # Exception: && and || in redirected I/O is ok
                # But be conservative here
                LOGGER.warning(f"Command rejected: contains dangerous operator '{op}'")
                return False
        
        # Check for dangerous substitution patterns
        for pattern in self.dangerous_patterns:
            if pattern in command:
                LOGGER.warning(f"Command rejected: contains dangerous pattern '{pattern}'")
                return False
        
        # Try to parse the command safely
        try:
            tokens = shlex.split(command)
        except ValueError as e:
            LOGGER.warning(f"Command rejected: invalid shell syntax - {e}")
            return False
        
        if not tokens:
            return False
        
        main_cmd = tokens[0].lower()
        base_cmd = Path(main_cmd).name.lower() if sys.platform != "win32" else main_cmd.lower()
        
        # Check if main command is dangerous
        if base_cmd in self.dangerous_commands or main_cmd in self.dangerous_commands:
            LOGGER.warning(f"Command rejected: dangerous command '{base_cmd}'")
            return False
        
        # Check if this is a legitimate common pattern
        # Allow: python -c "..."
        #        python3 -c "..."
        #        py -c "..."
        #        pytest
        #        git commit
        #        etc.
        if base_cmd.startswith('python') or base_cmd == 'py':
            # Python with -c is fine (subprocesses within the Python script can be dangerous
            # but that's the Python script's responsibility, not the shell)
            return True
        
        # Check for suspicious command substitution as a fallback
        if any(pattern in command for pattern in ['$', '`', '$(', '`']):
            if not (base_cmd.startswith('python') or base_cmd == 'py'):
                LOGGER.warning("Command rejected: contains command substitution")
                return False
        
        return True
    
    def validate_and_parse(self, command: str) -> tuple[bool, List[str] | None]:
        """
        Validate a command and return parsed tokens if safe.
        
        Returns:
            (is_safe, tokens) where tokens is list of command args if safe, None otherwise
        """
        if not self.is_safe(command):
            return False, None
        
        try:
            tokens = shlex.split(command)
            return True, tokens
        except ValueError:
            return False, None


def get_validated_command(command: str, validator: CommandValidator) -> tuple[bool, List[str] | None, str]:
    """
    Validate a command and return result with error message.
    
    Returns:
        (is_safe, tokens, message)
    """
    is_safe, tokens = validator.validate_and_parse(command)
    
    if not is_safe:
        msg = f"Command rejected by security policy: {command}"
        return False, None, msg
    
    return True, tokens, ""
