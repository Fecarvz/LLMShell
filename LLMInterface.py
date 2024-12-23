import subprocess
import logging
import sys
from typing import Optional



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