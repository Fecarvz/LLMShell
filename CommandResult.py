import os
import subprocess
import logging
from typing import Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommandResult:
    """Classe para armazenar o resultado de um comando."""
    success: bool
    output: str
    command: str
    error: Optional[str] = None