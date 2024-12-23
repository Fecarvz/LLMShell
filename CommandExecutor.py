import os
import subprocess
import shlex
import logging
from pathlib import Path
import shutil
from PathManager import PathManager
from FileManager import FileManager
from CommandResult import CommandResult
from SecurityValidator import SecurityValidator
class CommandExecutor:
    """Classe responsável pela execução de comandos."""
    
    def __init__(self):
        self.path_manager = PathManager()
        self.file_manager = FileManager(self.path_manager)
        self.previous_commands = []  # Lista para armazenar comandos anteriores
    
    def execute_command(self, command: str) -> CommandResult:
        """Executa um comando no sistema e retorna o resultado."""
        try:
            # Sanitiza o comando antes de executar
            command = SecurityValidator.sanitize_command(command)
            
            # Trata comandos especiais
            if command.startswith('echo') and '>' in command:
                result = self._handle_echo(command)
            elif command.startswith('mkdir'):
                result = self._handle_mkdir(command)
            elif command.startswith('touch'):
                result = self._handle_touch(command)
            else:
                # Verifica se é um comando seguro
                if not SecurityValidator.is_safe_command(command):
                    return CommandResult(
                        success=False,
                        output="",
                        command=command,
                        error="Comando bloqueado por motivos de segurança"
                    )
                
                args = shlex.split(command)
                result = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                result = CommandResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    command=command,
                    error=result.stderr if result.returncode != 0 else None
                )
            
            # Armazena o comando anterior
            self.previous_commands.append(command)
            return result
            
        except Exception as e:
            logging.error(f"Erro ao executar comando: {str(e)}")
            return CommandResult(
                success=False,
                output="",
                command=command,
                error=str(e)
            )

    def undo_last_command(self) -> CommandResult:
        """Desfaz o último comando executado."""
        if not self.previous_commands:
            return CommandResult(
                success=False,
                output="",
                command="",
                error="Nenhum comando anterior para desfazer."
            )
        
        last_command = self.previous_commands.pop()  # Remove o último comando
        command_parts = last_command.split()
        
        if command_parts[0] == 'mkdir':
            # Desfazendo mkdir removendo o diretório
            dir_path = command_parts[-1]
            try:
                shutil.rmtree(dir_path)  # Remove o diretório e todo o seu conteúdo
                return CommandResult(
                    success=True,
                    output=f"Diretório removido com sucesso: {dir_path}",
                    command=last_command,
                    error=None
                )
            except Exception as e:
                return CommandResult(
                    success=False,
                    output="",
                    command=last_command,
                    error=str(e)
                )
        
        elif command_parts[0] == 'touch':
            # Desfazendo touch removendo o arquivo
            file_path = command_parts[-1]
            try:
                os.remove(file_path)  # Remove o arquivo
                return CommandResult(
                    success=True,
                    output=f"Arquivo removido com sucesso: {file_path}",
                    command=last_command,
                    error=None
                )
            except Exception as e:
                return CommandResult(
                    success=False,
                    output="",
                    command=last_command,
                    error=str(e)
                )
        
        # Adicione mais condições conforme necessário para outros comandos
        
        return CommandResult(
            success=False,
            output="",
            command=last_command,
            error="Comando não suportado para desfazer."
        )

    def _handle_touch(self, command: str) -> CommandResult:
        """Trata especialmente comandos touch."""
        try:
            parts = shlex.split(command)
            if len(parts) < 2:
                return CommandResult(
                    success=False,
                    output="",
                    command=command,
                    error="Comando touch inválido"
                )
            
            file_path = Path(parts[-1])
            
            # Verifica se é um caminho absoluto ou relativo
            if file_path.is_absolute():
                full_path = file_path
            else:
                base_path = Path.cwd()
                full_path = base_path / file_path
            
            # Verifica permissões
            if not self.path_manager.has_write_permission(full_path):
                return CommandResult(
                    success=False,
                    output="",
                    command=command,
                    error=f"Permissão negada para criar arquivo em: {full_path}"
                )
            
            # Verifica extensão do arquivo
            if full_path.suffix not in SecurityValidator.ALLOWED_FILE_EXTENSIONS:
                return CommandResult(
                    success=False,
                    output="",
                    command=command,
                    error=f"Extensão de arquivo não permitida. Use: {', '.join(SecurityValidator.ALLOWED_FILE_EXTENSIONS)}"
                )
            
            # Cria o arquivo vazio
            try:
                full_path.touch()
                return CommandResult(
                    success=True,
                    output=f"Arquivo criado com sucesso: {full_path}",
                    command=command,
                    error=None
                )
            except Exception as e:
                return CommandResult(
                    success=False,
                    output="",
                    command=command,
                    error=f"Erro ao criar arquivo: {str(e)}"
                )
                
        except Exception as e:
            logging.error(f"Erro ao processar comando touch: {str(e)}")
            return CommandResult(
                success=False,
                output="",
                command=command,
                error=str(e)
            )

    def _handle_file_creation(self, command: str) -> CommandResult:
        """Trata a criação de arquivos de texto."""
        try:
            parts = command.split('>', 1)
            if len(parts) != 2:
                return CommandResult(
                    success=False,
                    output="",
                    command=command,
                    error="Comando inválido para criação de arquivo"
                )
            
            content = parts[0].replace('echo', '', 1).strip().strip('"\'')
            file_path = parts[1].strip()
            
            # Sanitiza o caminho do arquivo
            file_path = SecurityValidator.sanitize_path(file_path)
            base_dir = Path(file_path).parent
            
            # Cria o arquivo e escreve o conteúdo
            return self.file_manager.create_text_file(base_dir, Path(file_path).name, content, command)
            
        except Exception as e:
            logging.error(f"Erro ao criar arquivo: {str(e)}")
            return CommandResult(
                success=False,
                output="",
                command=command,
                error=str(e)
            )

    def _handle_mkdir(self, command: str) -> CommandResult:
        """Trata especialmente comandos mkdir."""
        try:
            parts = shlex.split(command)
            if len(parts) < 2:
                return CommandResult(
                    success=False,
                    output="",
                    command=command,
                    error="Comando mkdir inválido"
                )
            
            dir_name = parts[-1]
            # Expande o caminho se começar com ~
            if dir_name.startswith('~'):
                path = Path(dir_name).expanduser()
            elif dir_name.startswith('/'):
                path = Path(dir_name)
            else:
                base_path = Path.cwd()  # Mantém o diretório atual como base
                path = base_path / dir_name
            
            if not self.path_manager.has_write_permission(path):
                return CommandResult(
                    success=False,
                    output="",
                    command=command,
                    error=f"Permissão negada para criar diretório em: {path}"
                )
            
            if self.path_manager.ensure_directory_exists(path):
                return CommandResult(
                    success=True,
                    output=f"Diretório criado com sucesso: {path}",
                    command=command,
                    error=None
                )
            else:
                return CommandResult(
                    success=False,
                    output="",
                    command=command,
                    error=f"Não foi possível criar o diretório: {path}"
                )
                
        except Exception as e:
            logging.error(f"Erro ao criar diretório: {str(e)}")
            return CommandResult(
                success=False,
                output="",
                command=command,
                error=str(e)
            )

    def _handle_echo(self, command: str) -> CommandResult:
        """Trata o comando echo com redirecionamento."""
        try:
            parts = command.split('>', 1)
            if len(parts) != 2:
                return CommandResult(
                    success=False,
                    output="",
                    command=command,
                    error="Comando inválido para echo"
                )
            
            content = parts[0].replace('echo', '', 1).strip().strip('"\'')
            file_path = parts[1].strip()
            
            # Sanitiza o caminho do arquivo
            file_path = SecurityValidator.sanitize_path(file_path)
            base_dir = Path(file_path).parent
            
            # Cria o arquivo e escreve o conteúdo
            return self.file_manager.write_to_file(Path(file_path), content, command)
            
        except Exception as e:
            logging.error(f"Erro ao processar comando echo: {str(e)}")
            return CommandResult(
                success=False,
                output="",
                command=command,
                error=str(e)
            )