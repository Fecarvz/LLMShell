from pathlib import Path


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
