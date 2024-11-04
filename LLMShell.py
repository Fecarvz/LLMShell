import os
import subprocess
import shlex
import logging
from typing import Optional, List, Tuple
from dataclasses import dataclass
import sys
from pathlib import Path
import shutil

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('llm_cli.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

@dataclass
class CommandResult:
    """Classe para armazenar o resultado de um comando."""
    success: bool
    output: str
    command: str
    error: Optional[str] = None


class SecurityValidator:
    """Classe para validação de segurança de comandos."""
    BLOCKED_COMMANDS = {'rm', 'mkfs', 'dd', ':(){:|:&};:', 'mv', 'chmod'}
    ALLOWED_COMMANDS = {'touch', 'echo', 'mkdir'}
    ALLOWED_FILE_EXTENSIONS = {'.txt', '.md', '.csv'}
    
    @classmethod
    def is_safe_command(cls, command: str) -> bool:
        """Verifica se o comando é seguro para execução."""
        command_parts = command.lower().split()
        base_command = command_parts[0] if command_parts else ''
        
        # Verifica comandos bloqueados
        if any(blocked in command_parts for blocked in cls.BLOCKED_COMMANDS):
            return False
            
        # Verifica se é um comando permitido
        if base_command in cls.ALLOWED_COMMANDS:
            # Para o comando touch, verifica a extensão do arquivo
            if base_command == 'touch':
                file_path = command_parts[-1] if len(command_parts) > 1 else ''
                return Path(file_path).suffix in cls.ALLOWED_FILE_EXTENSIONS
            return True
            
        # Permite echo e redirecionamento para arquivos .txt
        if command.startswith('echo') and '>' in command:
            file_path = command.split('>')[-1].strip()
            return Path(file_path).suffix in cls.ALLOWED_FILE_EXTENSIONS
            
        return False

    @staticmethod
    def sanitize_text_content(content: str) -> str:
        """Sanitiza o conteúdo do texto removendo caracteres potencialmente perigosos."""
        # Remove caracteres de escape e comandos shell
        sanitized = content.replace(';', '').replace('&', '').replace('|', '')
        # Remove aspas no início e fim
        sanitized = sanitized.strip('"\'')
        # Remove caracteres de controle
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        return sanitized

    @staticmethod
    def sanitize_path(path: str) -> str:
        """Sanitiza o caminho do arquivo."""
        # Remove caracteres potencialmente perigosos do caminho
        sanitized = path.replace(';', '').replace('&', '').replace('|', '')
        # Remove sequências de ../
        while '../' in sanitized:
            sanitized = sanitized.replace('../', '')
        return sanitized.strip()

    @staticmethod
    def sanitize_command(command: str) -> str:
        """Sanitiza o comando removendo caracteres potencialmente perigosos."""
        return SecurityValidator.sanitize_text_content(command)


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

class LLMInterface:
    """Classe para interação com o LLM."""
    
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
    
    def get_response(self, question: str) -> Optional[str]:
        """Obtém a resposta do LLM."""
        try:
            result = subprocess.run(
                ['ollama', 'run', self.model_name, question],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception as e:
            logging.error(f"Erro ao obter resposta do LLM: {str(e)}")
            return None

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

class CLI:
    """Classe principal da interface de linha de comando."""
    
    def __init__(self):
        self.llm = LLMInterface()
        self.executor = CommandExecutor()
        self.scanner = FileSystemScanner()
        self.path_manager = PathManager()
    
    def run(self):
        """Executa o loop principal da CLI."""
        print("Interface de Comando LLM. Digite 'sair' para encerrar.")
        
        while True:
            try:
                user_input = input("Você: ").strip()
                
                if user_input.lower() in ['sair', 'exit', 'quit']:
                    break
                
                if not user_input:
                    continue

                
                if user_input.lower() == 'desfazer':
                    result = self.executor.undo_last_command()
                    print("Saída:", result.output)
                    if not result.success:
                        print("Erro:", result.error)
                    continue               
                # Lista diretórios com profundidade limitada
                home_dir = self.path_manager.get_user_home()
                directories = self.scanner.list_directories(home_dir, max_depth=1)
                
                question = (
                    f"Você é um assistente que executa comandos Bash no meu sistema Linux. "
                    f"Por favor, execute o seguinte comando: {user_input}. "
                    f"Responda apenas com o comando necessário, e sempre forneça o caminho completo do arquivo ou diretório. "
                    f"Nunca utilize ~ ou sudo. "
                    f"Valide o comando antes de executá-lo e retorne uma mensagem de erro se o comando não for seguro ou válido. "
                    f"Exemplos de comandos válidos: 'mkdir /home/felipe/Documentos/nova_pasta', 'touch /home/felipe/Documentos/arquivo.txt'. 'echo'"
                    f"Exemplos de comandos inválidos: 'rm -rf /', 'chmod 777 /home/felipe/Documentos/arquivo.txt'. "
                    f"O diretório base é: {home_dir}\n"
                    f"Os diretórios disponíveis são:\n{chr(10).join(directories)}."
                )
                
                command = self.llm.get_response(question)
                
                if not command:
                    print("Erro: Não foi possível obter resposta do LLM")
                    continue
                
                # Exibe o comando que será executado
                print("\nComando a ser executado:", command)
                

                
                result = self.executor.execute_command(command)
                
                if result.success:
                    print("Saída:", result.output)
                else:
                    print("Erro:", result.error or "Comando falhou")
                
            except KeyboardInterrupt:
                print("\nOperação cancelada pelo usuário")
                break
            except Exception as e:
                logging.error(f"Erro inesperado: {str(e)}")
                print(f"Ocorreu um erro inesperado: {str(e)}")

def main():
    """Função principal."""
    try:
        cli = CLI()
        cli.run()
    except Exception as e:
        logging.critical(f"Erro fatal: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
