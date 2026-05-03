# main.py
from motor import ConexaoEE  # classe motor
from interface import AppInterface  # classe interface

# Configurações de acesso#mudar isso para um metodo construtor
CONTA_SERVICO = 'coloque aqui a chave de serviço'
CHAVE_JSON = 'coloque aqui a chave json'


def iniciar():
    # 1. Autentica no Google
    ConexaoEE.autenticar(CONTA_SERVICO, CHAVE_JSON)  #

    # 2. Instancia e executa a interface
    app = AppInterface()
    app.executar()


if __name__ == "__main__":
    iniciar()
