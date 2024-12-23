import os
import logging
import sys
from pathlib import Path
from CommandExecutor import CommandExecutor
from CommandResult import CommandResult
from FileManager import FileManager
from FileSystemScanner import FileSystemScanner
from LLMInterface import LLMInterface
from PathManager import PathManager
from SecurityValidator import SecurityValidator

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('llm_cli.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


import logging

class CLI:
    """Classe principal da interface de linha de comando."""
    
    def __init__(self):
        self.llm = LLMInterface()
        self.executor = CommandExecutor()
        self.scanner = FileSystemScanner()
        self.path_manager = PathManager()
    
    def _get_user_input(self):
        """Obtém a entrada do usuário e garante que não seja vazia."""
        while True:
            user_input = input("Você: ").strip()
            if user_input.lower() in ['sair', 'exit', 'quit']:
                return 'sair'
            if user_input:
                return user_input

    def _get_confirmation(self):
        """Obtém a confirmação do usuário para executar o comando."""
        while True:
            user_confirm = input("Deseja executar esse comando? (Y/N): ").strip().upper()
            if user_confirm in ["Y", "N"]:
                return user_confirm
            print("Entrada inválida. Responda com 'Y' para sim ou 'N' para não.")

    def _handle_undo(self):
        """Desfaz o último comando executado."""
        result = self.executor.undo_last_command()
        print("Saída:", result.output)
        if not result.success:
            print("Erro:", result.error)

    def _prepare_command_question(self, user_input, home_dir, directories):
        """Prepara a pergunta para a execução do comando com base na entrada do usuário."""
        return (
            f"Você é um assistente responsável por executar comandos Bash no meu sistema Linux. "
            f"Por favor, execute o seguinte comando: {user_input}. "
            f"Responda somente com o comando necessário e forneça sempre o caminho completo do arquivo ou diretório. "
            f"Evite usar '~' ou 'sudo'. "
            f"Se encontrar um comando que não faz sentido, responda que não entendeu e solicite que tente novamente. "
            f"Valide o comando antes de executá-lo e, se ele não for seguro ou válido, retorne uma mensagem de erro. "
            f"Exemplos de comandos válidos: 'mkdir /home/felipe/Documentos/nova_pasta', 'touch /home/felipe/Documentos/arquivo.txt', 'echo'. "
            f"Exemplos de comandos inválidos: 'rm -rf /', 'chmod 777 /home/felipe/Documentos/arquivo.txt'. "
            f"O diretório base é: {home_dir}. "
            f"Os diretórios disponíveis são:\n{chr(10).join(directories)}."
        )
    
    def run(self):
        """Executa o loop principal da CLI."""
        print("Interface de Comando LLM. Digite 'sair' para encerrar.")
        
        while True:
            try:
                user_input = self._get_user_input()
                if user_input == 'sair':
                    break

                # Comando para desfazer
                if user_input.lower() == 'desfazer':
                    self._handle_undo()
                    continue

                # Lista diretórios com profundidade limitada
                home_dir = self.path_manager.get_user_home()
                directories = self.scanner.list_directories(home_dir, max_depth=1)

                # Prepara a pergunta para o LLM
                question = self._prepare_command_question(user_input, home_dir, directories)

                # Obtém a resposta do LLM
                command = self.llm.get_response(question)
                
                if not command:
                    print("Erro: Não foi possível obter resposta do LLM.")
                    continue

                # Exibe o comando que será executado
                print("\nComando a ser executado:", command)

                # Pergunta se o usuário deseja executar o comando
                user_confirm = self._get_confirmation()

                if user_confirm == "Y":
                    result = self.executor.execute_command(command)
                    if result.success:
                        print("Saída:", result.output)
                    else:
                        print("Erro:", result.error or "Comando falhou")
                else:
                    print("\nOperação cancelada pelo usuário.")
                
            except KeyboardInterrupt:
                print("\nOperação cancelada pelo usuário.")
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
