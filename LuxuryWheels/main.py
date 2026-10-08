# Módulo: main.py
# Descrição: Ponto de entrada principal da aplicação Luxury Wheels (Gestão de Frota).
            # Inicializa o ambiente gráfico e abre a janela de autenticação.

import sys
import os

# Adicionar a pasta raiz ao path do sistema para garantir importações corretas de módulos
PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJ_ROOT not in sys.path:
    sys.path.append(PROJ_ROOT)

from database.db_handler import inicializar_base_dados
from views.login_view import JanelaLogin


def main():
    # Função principal que arranca a base de dados e a interface gráfica.
    # Garantir que a base de dados e as tabelas estão criadas e prontas a usar
    inicializar_base_dados()

    # Iniciar a aplicação abrindo a janela de login
    app = JanelaLogin()
    app.mainloop()


if __name__ == "__main__":
    main()