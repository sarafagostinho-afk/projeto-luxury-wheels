# Módulo: table_sort.py
# Descrição: ordenação inteligente de colunas em tabelas ttk.Treeview.

def configurar_ordenacao_treeview(treeview, colunas_ignoradas=None):
    # Configura o clique nos cabeçalhos de uma Treeview para ordenar as linhas de forma ascendente e descendente.
    if colunas_ignoradas is None:
        colunas_ignoradas = []

    for col in treeview["columns"]:
        if col in colunas_ignoradas:
            continue
        treeview.heading(col, command=lambda c=col: ordenar_coluna_treeview(treeview, c, False))


def ordenar_coluna_treeview(treeview, coluna, descendente):
    # Ordena os itens de uma coluna da Treeview convertendo inteligentemente os valores.
    dados_linhas = []
    for child in treeview.get_children(""):
        val = treeview.set(child, coluna)
        dados_linhas.append((val, child))

    def converter_valor(valor_str):
        # Tenta converter a string da tabela para número ou data para permitir ordenação numérica correta.
        if valor_str is None:
            return (0, "")

        # Limpar símbolos comuns (como € ou km)
        limpo = str(valor_str).replace("€", "").replace("km", "").replace(",", ".").strip()

        # Tentar converter para inteiro
        try:
            return (1, int(limpo))
        except ValueError:
            pass

        # Tentar converter para float
        try:
            return (1, float(limpo))
        except ValueError:
            pass

        # Se for texto normal, retornar como string em minúsculas
        return (2, str(valor_str).lower())

    # Ordenar com segurança tratando tipos mistos
    try:
        dados_linhas.sort(key=lambda x: converter_valor(x[0]), reverse=descendente)
    except Exception:
        # Fallback de segurança absoluto caso ocorra algum erro inesperado
        dados_linhas.sort(key=lambda x: str(x[0]).lower(), reverse=descendente)

    # Reorganizar as linhas na Treeview
    for index, (val, child) in enumerate(dados_linhas):
        treeview.move(child, "", index)

    # Inverter a direção da ordenação para o próximo clique
    treeview.heading(coluna, command=lambda: ordenar_coluna_treeview(treeview, coluna, not descendente))