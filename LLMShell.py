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
