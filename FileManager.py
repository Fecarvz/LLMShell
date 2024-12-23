import os
import logging
from typing import Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path
from CommandResult import CommandResult
from SecurityValidator import SecurityValidator
from PathManager import PathManager

class FileManager:
    """Classe para gerenciar operações com arquivos."""
    
    def __init__(self, path_manager):
        self.path_manager = path_manager
    
    def create_text_file(self, directory: Path, filename: str, content: str, command: str) -> CommandResult:
        """Cria um arquivo de texto com o conteúdo especificado."""
        try:
            if not directory.exists():
                return CommandResult(
                    success=False,
                    output="",
                    command=command,
                    error=f"Diretório não encontrado: {directory}"
                )
            
            if not self.path_manager.has_write_permission(directory):
                return CommandResult(
                    success=False,
                    output="",
                    command=command,
                    error=f"Permissão negada para criar arquivo em: {directory}"
                )
            
            # Sanitiza o nome do arquivo e caminho
            safe_filename = SecurityValidator.sanitize_path(filename)
            if not safe_filename.endswith('.txt'):
                safe_filename += '.txt'
                
            file_path = directory / safe_filename
            
            # Sanitiza o conteúdo
            safe_content = SecurityValidator.sanitize_text_content(content)
            
            # Cria o arquivo e escreve o conteúdo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(safe_content)
            
            return CommandResult(
                success=True,
                output=f"Arquivo criado com sucesso: {file_path}",
                command=command,
                error=None
            )
            
        except Exception as e:
            logging.error(f"Erro ao criar arquivo: {str(e)}")
            return CommandResult(
                success=False,
                output="",
                command=command,
                error=str(e)
            )

    def write_to_file(self, file_path: Path, content: str, command: str) -> CommandResult:
        """Escreve conteúdo em um arquivo existente."""
        try:
            if not file_path.parent.exists():
                return CommandResult(
                    success=False,
                    output="",
                    command=command,
                    error=f"Diretório não encontrado: {file_path.parent}"
                )
            
            if not self.path_manager.has_write_permission(file_path.parent):
                return CommandResult(
                    success=False,
                    output="",
                    command=command,
                    error=f"Permissão negada para escrever no arquivo: {file_path}"
                )
            
            # Sanitiza o conteúdo
            safe_content = SecurityValidator.sanitize_text_content(content)
            
            # Escreve no arquivo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(safe_content)
            
            return CommandResult(
                success=True,
                output=f"Conteúdo escrito com sucesso em: {file_path}",
                command=command,
                error=None
            )
            
        except Exception as e:
            logging.error(f"Erro ao escrever no arquivo: {str(e)}")
            return CommandResult(
                success=False,
                output="",
                command=command,
                error=str(e)
            )