# main.py
from motor import ConexaoEE
from interface import AppInterface

# Configurações de acesso
CONTA_SERVICO = 'digite aqui a conta'
CHAVE_JSON = 'Digite aqui a chave json'

def iniciar():
    # 1. Autentica no Google
    ConexaoEE.autenticar(CONTA_SERVICO, CHAVE_JSON)
    
    # 2. Instancia e executa a interface
    app = AppInterface()
    app.executar()

if __name__ == "__main__":
    iniciar()
