import os
import logging
from typing import Optional, List, Tuple
from pathlib import Path

class FileSystemScanner:
    """Classe para escanear o sistema de arquivos."""
    
    @staticmethod
    def list_directories(base_path: str, max_depth: int = 3) -> List[str]:
        """Lista diretórios até uma profundidade máxima."""
        try:
            directories = []
            base_path = Path(base_path).expanduser()
            
            for dirpath, dirnames, _ in os.walk(base_path):
                current_depth = len(Path(dirpath).relative_to(base_path).parts)
                if current_depth > max_depth:
                    dirnames.clear()
                    continue
                
                directories.append(dirpath)
            
            return directories[:100]  # Limita a quantidade de diretórios
            
        except Exception as e:
            logging.error(f"Erro ao listar diretórios: {str(e)}")
            return []
