# LLMShell
# LLM CLI

Este projeto é uma interface de linha de comando (CLI) que permite a execução de comandos Bash em um sistema Linux, utilizando um modelo de linguagem (LLM) para gerar comandos com base em perguntas do usuário. O sistema inclui validações de segurança para garantir que apenas comandos seguros sejam executados.

## Funcionalidades

- **Execução de Comandos**: Permite a execução de comandos como `mkdir`, `touch`, e `echo`, com validações de segurança.
- **Desfazer Comandos**: Possui a funcionalidade de desfazer o último comando executado.
- **Gerenciamento de Arquivos**: Criação e escrita em arquivos de texto com conteúdo sanitizado.
- **Escaneamento de Sistema de Arquivos**: Lista diretórios até uma profundidade máxima especificada.

## Estrutura do Projeto

- **Classes Principais**:
  - `CLI`: Classe principal que gerencia a interação com o usuário.
  - `CommandExecutor`: Executa comandos e gerencia a lógica de execução.
  - `FileManager`: Gerencia operações de arquivos.
  - `SecurityValidator`: Valida a segurança dos comandos.
  - `PathManager`: Gerencia caminhos e permissões.
  - `LLMInterface`: Interage com o modelo de linguagem para obter respostas.
  - `FileSystemScanner`: Escaneia o sistema de arquivos.

## Como Usar

1. Clone o repositório:
   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd <NOME_DO_REPOSITORIO>
   ```

2. Execute o script:
   ```bash
   python nome_do_script.py
   ```

3. Interaja com a CLI digitando comandos. Para sair, digite `sair`.

## Requisitos

- Python 3.x
- Bibliotecas: `os`, `subprocess`, `shlex`, `logging`, `dataclasses`, `sys`, `pathlib`, `shutil`

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir um issue ou enviar um pull request.

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para mais detalhes.
