import os
import logging
from pathlib import Path


class PathManager:
    """Classe para gerenciar caminhos e permissões."""
    
    @staticmethod
    def get_user_home() -> Path:
        """Retorna o diretório home do usuário atual."""
        return Path.home()
    
    @staticmethod
    def get_documents_dir() -> Path:
        """Retorna o diretório Documentos do usuário."""
        return Path.home() / "Documentos"
    
    @staticmethod
    def ensure_directory_exists(path: Path) -> bool:
        """Garante que um diretório existe, criando-o se necessário."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except PermissionError:
            logging.error(f"Permissão negada ao criar diretório: {path}")
            return False
        except Exception as e:
            logging.error(f"Erro ao criar diretório {path}: {str(e)}")
            return False

    @staticmethod
    def has_write_permission(path: Path) -> bool:
        """Verifica se o usuário tem permissão de escrita no caminho."""
        return os.access(path.parent, os.W_OK)