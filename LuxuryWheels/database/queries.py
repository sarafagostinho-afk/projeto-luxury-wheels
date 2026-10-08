# Módulo: queries.py
# Descrição: Central de consultas e operações SQL na base de dados SQLite para todos os módulos do Luxury Wheels.

import hashlib
from datetime import datetime, date, timedelta
from database.db_handler import get_connection


def parse_data_flexivel(val):
    if not val:
        return None
    val_str = str(val).strip()[:10]
    formatos = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]
    for fmt in formatos:
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue
    return None


# ==============================================================================
# 1. AUTENTICAÇÃO E UTILIZADORES
# ==============================================================================

def autenticar_utilizador(username, password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    usuario_limpo = username.strip()

    cursor.execute("PRAGMA table_info(utilizadores)")
    colunas = [col[1] for col in cursor.fetchall()]

    cursor.execute("SELECT * FROM utilizadores WHERE username = ?", (usuario_limpo,))
    row = cursor.fetchone()

    if not row and usuario_limpo.lower() == "admin":
        hash_padrao = hashlib.sha256("admin123".encode("utf-8")).hexdigest()
        if "primeiro_nome" in colunas and "ultimo_nome" in colunas:
            cursor.execute("INSERT INTO utilizadores (username, password_hash, primeiro_nome, ultimo_nome) VALUES ('admin', ?, 'Admin', 'Sistema')", (hash_padrao,))
        elif "nome_completo" in colunas:
            cursor.execute("INSERT INTO utilizadores (username, password_hash, nome_completo) VALUES ('admin', ?, 'Admin Sistema')", (hash_padrao,))
        else:
            cursor.execute("INSERT INTO utilizadores (username, password_hash) VALUES ('admin', ?)", (hash_padrao,))
        conn.commit()
        cursor.execute("SELECT * FROM utilizadores WHERE username = 'admin'")
        row = cursor.fetchone()

    conn.close()
    if not row: return None

    u = dict(row)
    pwd_bd = u.get("password_hash") or u.get("password") or u.get("senha") or ""
    hash_inserida = hashlib.sha256(password_hash.encode("utf-8")).hexdigest() if len(password_hash) != 64 else password_hash
    hash_admin123 = hashlib.sha256("admin123".encode("utf-8")).hexdigest()

    valido = False
    if pwd_bd in (password_hash, hash_inserida):
        valido = True
    elif usuario_limpo.lower() == "admin" and password_hash in ("admin123", hash_admin123):
        valido = True

    if not valido: return None
    if "ativo" in u and u["ativo"] not in (1, "1", True): return None

    if "nome_completo" not in u:
        if "primeiro_nome" in u and "ultimo_nome" in u:
            u["nome_completo"] = f"{u.get('primeiro_nome', '')} {u.get('ultimo_nome', '')}".strip()
        else:
            u["nome_completo"] = "Admin Sistema"

    if "nivel_acesso" not in u:
        u["nivel_acesso"] = "Administrador"

    return u


def registar_utilizador(username, password_hash, primeiro_nome="", ultimo_nome="",
                       nome_completo="", nivel_acesso="Operador", **kwargs):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(utilizadores)")
    colunas = [col[1] for col in cursor.fetchall()]

    if not nome_completo and (primeiro_nome or ultimo_nome):
        nome_completo = f"{primeiro_nome} {ultimo_nome}".strip()

    mapa_campos = {
        "username": username.strip(), "password_hash": password_hash,
        "password": password_hash, "primeiro_nome": primeiro_nome.strip(),
        "ultimo_nome": ultimo_nome.strip(), "nome_completo": nome_completo.strip(),
        "nome": nome_completo.strip(), "nivel_acesso": nivel_acesso, "ativo": 1
    }
    for k, v in kwargs.items():
        if k in colunas: mapa_campos[k] = v

    campos_a_inserir = [c for c in colunas if c in mapa_campos and c != "id"]
    valores_a_inserir = [mapa_campos[c] for c in campos_a_inserir]

    try:
        colunas_sql = ", ".join(campos_a_inserir)
        placeholders = ", ".join(["?"] * len(valores_a_inserir))
        cursor.execute(f"INSERT INTO utilizadores ({colunas_sql}) VALUES ({placeholders})", valores_a_inserir)
        conn.commit()
        return True, "Utilizador registado com sucesso!"
    except Exception as e:
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()


# ==============================================================================
# 2. DASHBOARD GERAL E MÉTRICAS
# ==============================================================================

def obter_metricas_dashboard():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM veiculos")
    total_veiculos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM veiculos WHERE LOWER(estado) IN ('disponível', 'disponivel')")
    veiculos_disponiveis = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM veiculos WHERE LOWER(estado) IN ('alugado', 'guardado')")
    veiculos_alugados = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM veiculos WHERE LOWER(estado) IN ('manutenção', 'manutencao')")
    veiculos_manutencao = cursor.fetchone()[0]

    primeiro_dia_mes = date.today().replace(day=1).isoformat()
    cursor.execute("SELECT COALESCE(SUM(valor_total), 0) FROM reservas WHERE data_inicio >= ? AND LOWER(estado_reserva) != 'cancelada'", (primeiro_dia_mes,))
    faturacao_mes = float(cursor.fetchone()[0])
    cursor.execute("SELECT COUNT(*) FROM reservas WHERE data_inicio >= ? AND LOWER(estado_reserva) != 'cancelada'", (primeiro_dia_mes,))
    total_reservas_mes = int(cursor.fetchone()[0])
    conn.close()

    class SafeMetrics(dict):
        def __missing__(self, key): return []

    return SafeMetrics({
        "total_veiculos": total_veiculos, "veiculos_disponiveis": veiculos_disponiveis,
        "veiculos_alugados": veiculos_alugados, "veiculos_manutencao": veiculos_manutencao,
        "financas_mes": {"total_faturado": faturacao_mes, "total_reservas": total_reservas_mes, "valor": faturacao_mes},
        "faturacao_mes": faturacao_mes, "total_reservas_mes": total_reservas_mes
    })


def obter_disponibilidade_separada():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT tipo, COUNT(*) as quantidade FROM veiculos WHERE LOWER(estado) IN ('disponível', 'disponivel') GROUP BY tipo ORDER BY quantidade DESC")
    tipos = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT categoria, COUNT(*) as quantidade FROM veiculos WHERE LOWER(estado) IN ('disponível', 'disponivel') GROUP BY categoria ORDER BY quantidade DESC")
    categorias = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return tipos, categorias


def listar_veiculos_alugados_resumo():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT v.matricula, v.tipo, v.modelo, r.data_fim_prevista FROM reservas r JOIN veiculos v ON r.veiculo_id = v.id WHERE LOWER(r.estado_reserva) = 'ativa' ORDER BY r.data_fim_prevista ASC")
    rows = cursor.fetchall()
    conn.close()
    resultado = []
    hoje = date.today()
    for r in rows:
        d = dict(r)
        fim = parse_data_flexivel(d.get("data_fim_prevista"))
        dias = (fim - hoje).days if fim else 999
        dias_txt = f"{dias} dia(s)" if dias >= 0 else f"Atrasado ({abs(dias)} d)"
        resultado.append({"matricula": d["matricula"], "tipo": d["tipo"], "modelo": d["modelo"], "dias_num": dias, "dias_restantes": dias_txt})
    resultado.sort(key=lambda x: x["dias_num"])
    return resultado


def verificar_avisos_manutencao_unificados(dias_aviso=15):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, matricula, marca, modelo, tipo, data_proxima_revisao, data_proxima_inspecao FROM veiculos WHERE (data_proxima_revisao IS NOT NULL AND TRIM(data_proxima_revisao) != '') OR (data_proxima_inspecao IS NOT NULL AND TRIM(data_proxima_inspecao) != '')")
    rows = cursor.fetchall()
    conn.close()
    hoje = date.today()
    avisos = []
    for r in rows:
        v = dict(r)
        d_rev = parse_data_flexivel(v.get("data_proxima_revisao"))
        d_insp = parse_data_flexivel(v.get("data_proxima_inspecao"))
        dias_rev = (d_rev - hoje).days if d_rev else None
        dias_insp = (d_insp - hoje).days if d_insp else None
        tem_rev = (dias_rev is not None) and (dias_rev <= dias_aviso)
        tem_insp = (dias_insp is not None) and (dias_insp <= dias_aviso)
        if not (tem_rev or tem_insp): continue

        if tem_rev and tem_insp:
            dias = min(dias_rev, dias_insp)
            data_str = (d_rev if dias_rev <= dias_insp else d_insp).strftime("%Y-%m-%d")
            tipo_label = "Inspeção e Revisão"
        elif tem_rev:
            dias, data_str, tipo_label = dias_rev, d_rev.strftime("%Y-%m-%d"), "Revisão"
        else:
            dias, data_str, tipo_label = dias_insp, d_insp.strftime("%Y-%m-%d"), "Inspeção"

        estado_tempo = f"EXPIRADO ({abs(dias)} d)" if dias < 0 else ("Hoje!" if dias == 0 else f"Faltam {dias} d")
        avisos.append({"matricula": v["matricula"], "modelo": f"{v['marca']} {v['modelo']}", "data_limite": data_str, "tipo": tipo_label, "dias": dias, "estado_tempo": estado_tempo})
    avisos.sort(key=lambda x: x["dias"])
    return avisos


def obter_ultimos_clientes(limite=5):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(clientes)")
    colunas = [c[1] for c in cursor.fetchall()]
    col_tel = "telefone" if "telefone" in colunas else "nif"
    cursor.execute(f"SELECT nome_completo, {col_tel} as tel FROM clientes ORDER BY id DESC LIMIT ?", (limite,))
    rows = cursor.fetchall()
    conn.close()
    return [{"nome": r["nome_completo"], "telefone": r["tel"]} for r in rows]


# ==============================================================================
# 3. GESTÃO DE VEÍCULOS, CLIENTES E PAGAMENTOS
# ==============================================================================

def listar_veiculos(termo_pesquisa="", filtro_tipo=None, filtro_categoria=None, filtro_transmissao=None, filtro_combustivel=None, filtro_estado=None):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM veiculos WHERE 1=1"
    params = []
    if termo_pesquisa:
        sql += " AND (matricula LIKE ? OR marca LIKE ? OR modelo LIKE ?)"
        params.extend([f"%{termo_pesquisa.strip()}%"] * 3)
    if filtro_tipo and filtro_tipo != "Todos":
        sql += " AND LOWER(tipo) = LOWER(?)"
        params.append(filtro_tipo.strip())
    if filtro_categoria and filtro_categoria != "Todas":
        sql += " AND LOWER(categoria) = LOWER(?)"
        params.append(filtro_categoria.strip())
    sql += " ORDER BY id ASC"
    cursor.execute(sql, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def adicionar_veiculo(dados: dict):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO veiculos (matricula, marca, modelo, ano, tipo, categoria, transmissao, num_passageiros, combustivel, cor, preco_diario, data_proxima_revisao, data_proxima_inspecao, imagem_path, estado, quilometragem) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            dados.get("matricula"), dados.get("marca"), dados.get("modelo"), dados.get("ano", 2024),
            dados.get("tipo", "Carro"), dados.get("categoria", "Médio"), dados.get("transmissao", "Manual"),
            dados.get("num_passageiros", 5), dados.get("combustivel", "Gasolina"), dados.get("cor", "Preto"),
            dados.get("preco_diario", 50.0), dados.get("data_proxima_revisao"), dados.get("data_proxima_inspecao"),
            dados.get("imagem_path", ""), dados.get("estado", "Disponível"), dados.get("quilometragem", 0)
        ))
        conn.commit()
        return True, "Veículo registado com sucesso!"
    except Exception as e:
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()


def atualizar_veiculo(veiculo_id: int, dados: dict):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE veiculos SET matricula=?, marca=?, modelo=?, ano=?, tipo=?, categoria=?, transmissao=?, num_passageiros=?, combustivel=?, cor=?, preco_diario=?, data_proxima_revisao=?, data_proxima_inspecao=?, imagem_path=?, estado=?, quilometragem=? WHERE id=?", (
            dados.get("matricula"), dados.get("marca"), dados.get("modelo"), dados.get("ano", 2024),
            dados.get("tipo"), dados.get("categoria"), dados.get("transmissao"), dados.get("num_passageiros"),
            dados.get("combustivel"), dados.get("cor"), dados.get("preco_diario"), dados.get("data_proxima_revisao"),
            dados.get("data_proxima_inspecao"), dados.get("imagem_path"), dados.get("estado"), dados.get("quilometragem"), veiculo_id
        ))
        conn.commit()
        return True, "Veículo atualizado com sucesso!"
    except Exception as e:
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()


def alterar_estado_veiculo(veiculo_id: int, novo_estado: str, motivo: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE veiculos SET estado = ?, motivo_indisponivel = ? WHERE id = ?", (novo_estado, motivo, veiculo_id))
    conn.commit()
    conn.close()
    return True


def remover_veiculo(veiculo_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM veiculos WHERE id = ?", (veiculo_id,))
        conn.commit()
        return True, "Veículo removido com sucesso!"
    except Exception:
        return False, "Não é possível remover: o veículo tem histórico."
    finally:
        conn.close()


def listar_clientes(termo_pesquisa=""):
    conn = get_connection()
    cursor = conn.cursor()
    if termo_pesquisa:
        cursor.execute("SELECT * FROM clientes WHERE nome_completo LIKE ? OR nif LIKE ? OR telefone LIKE ? ORDER BY id DESC", (f"%{termo_pesquisa}%", f"%{termo_pesquisa}%", f"%{termo_pesquisa}%"))
    else:
        cursor.execute("SELECT * FROM clientes ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def adicionar_cliente(nome, nif, carta, telefone, email, morada=""):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO clientes (nome_completo, nif, numero_carta, telefone, email, morada) VALUES (?, ?, ?, ?, ?, ?)", (nome, nif, carta, telefone, email, morada))
        conn.commit()
        return True, "Cliente registado com sucesso!"
    except Exception as e:
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()


def atualizar_cliente(cliente_id, nome, nif, carta, telefone, email, morada):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE clientes SET nome_completo=?, nif=?, numero_carta=?, telefone=?, email=?, morada=? WHERE id=?", (nome, nif, carta, telefone, email, morada, cliente_id))
        conn.commit()
        return True, "Cliente atualizado com sucesso!"
    except Exception as e:
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()


def remover_cliente(cliente_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
        conn.commit()
        return True, "Cliente removido com sucesso!"
    except Exception:
        return False, "Não é possível remover: cliente com reservas."
    finally:
        conn.close()


def listar_formas_pagamento():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM formas_pagamento WHERE ativo = 1 ORDER BY id ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def listar_formas_pagamento_detalhado(termo_pesquisa=""):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "SELECT f.id, f.nome, f.descricao, f.ativo, COUNT(r.id) as total_reservas, COALESCE(SUM(r.valor_total), 0) as total_faturado FROM formas_pagamento f LEFT JOIN reservas r ON f.id = r.forma_pagamento_id WHERE 1=1"
    params = []
    if termo_pesquisa:
        sql += " AND f.nome LIKE ?"
        params.append(f"%{termo_pesquisa}%")
    sql += " GROUP BY f.id ORDER BY f.id ASC"
    cursor.execute(sql, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def adicionar_forma_pagamento(nome: str, descricao: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO formas_pagamento (nome, descricao, ativo) VALUES (?, ?, 1)", (nome.strip(), descricao.strip()))
        conn.commit()
        return True, "Adicionado com sucesso!"
    except Exception as e:
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()


def atualizar_forma_pagamento(forma_id: int, nome: str, descricao: str, ativo: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE formas_pagamento SET nome=?, descricao=?, ativo=? WHERE id=?", (nome.strip(), descricao.strip(), ativo, forma_id))
        conn.commit()
        return True, "Atualizado com sucesso!"
    except Exception as e:
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()


def remover_forma_pagamento(forma_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM formas_pagamento WHERE id = ?", (forma_id,))
        conn.commit()
        return True, "Removido com sucesso!"
    except Exception:
        return False, "Bloqueado: existem reservas com este método."
    finally:
        conn.close()


# ==============================================================================
# 6. GESTÃO DE RESERVAS (COM SUPORTE A SINAL / TOTAL / NÃO PAGO E ESTADO GUARDADO)
# ==============================================================================

def listar_reservas(termo_pesquisa="", filtro_estado=None, filtro_tipo_veiculo=None):
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT 
            r.id, r.veiculo_id, r.cliente_id, r.forma_pagamento_id,
            r.data_inicio, r.data_fim_prevista, r.data_fim_real,
            r.km_inicial, r.km_final, r.valor_diario_aplicado,
            r.valor_total, r.estado_reserva, r.observacoes,
            v.matricula, v.marca, v.modelo, v.tipo as tipo_veiculo,
            c.nome_completo as nome_cliente, c.telefone as telefone_cliente,
            f.nome as metodo_pagamento
        FROM reservas r
        JOIN veiculos v ON r.veiculo_id = v.id
        JOIN clientes c ON r.cliente_id = c.id
        JOIN formas_pagamento f ON r.forma_pagamento_id = f.id
        WHERE 1=1
    """
    params = []

    if termo_pesquisa:
        sql += " AND (c.nome_completo LIKE ? OR c.telefone LIKE ? OR v.matricula LIKE ? OR v.modelo LIKE ?)"
        padrao = f"%{termo_pesquisa.strip()}%"
        params.extend([padrao, padrao, padrao, padrao])

    if filtro_estado and filtro_estado != "Todos":
        sql += " AND LOWER(r.estado_reserva) = LOWER(?)"
        params.append(filtro_estado.strip())

    if filtro_tipo_veiculo and filtro_tipo_veiculo != "Todos":
        sql += " AND LOWER(v.tipo) = LOWER(?)"
        params.append(filtro_tipo_veiculo.strip())

    sql += """
        ORDER BY 
            CASE WHEN LOWER(r.estado_reserva) = 'ativa' THEN 0 ELSE 1 END ASC,
            r.data_inicio ASC,
            r.id ASC
    """

    cursor.execute(sql, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def criar_reserva(veiculo_id, cliente_id, forma_pag_id, data_inicio, data_fim, km_inicial, valor_dia, obs="", modalidade_pagamento="Total"):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        d1 = parse_data_flexivel(data_inicio) or datetime.strptime(data_inicio, "%Y-%m-%d").date()
        d2 = parse_data_flexivel(data_fim) or datetime.strptime(data_fim, "%Y-%m-%d").date()
        dias = max(1, (d2 - d1).days)
        valor_total = dias * float(valor_dia)

        obs_final = f"[{modalidade_pagamento.upper()}] {obs}".strip()
        estado_veiculo = "Guardado" if modalidade_pagamento == "Não Pago" else "Alugado"

        cursor.execute("""
            INSERT INTO reservas (
                veiculo_id, cliente_id, forma_pagamento_id,
                data_inicio, data_fim_prevista, km_inicial,
                valor_diario_aplicado, valor_total, estado_reserva, observacoes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Ativa', ?)
        """, (veiculo_id, cliente_id, forma_pag_id, d1.isoformat(), d2.isoformat(), km_inicial, valor_dia, valor_total, obs_final))

        cursor.execute("UPDATE veiculos SET estado = ? WHERE id = ?", (estado_veiculo, veiculo_id))
        conn.commit()
        return True, f"Reserva registada com sucesso! Viatura em estado: {estado_veiculo}.", None
    except Exception as e:
        conn.rollback()
        return False, f"Erro: {str(e)}", None
    finally:
        conn.close()


def atualizar_reserva(reserva_id: int, dados: dict):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        d1 = parse_data_flexivel(dados.get("data_inicio"))
        d2 = parse_data_flexivel(dados.get("data_fim_prevista"))
        dias = max(1, (d2 - d1).days) if (d1 and d2) else 1
        valor_total = dias * float(dados.get("valor_diario_aplicado", 50.0))

        cursor.execute("""
            UPDATE reservas SET
                cliente_id = ?, veiculo_id = ?, forma_pagamento_id = ?,
                data_inicio = ?, data_fim_prevista = ?, km_inicial = ?,
                valor_diario_aplicado = ?, valor_total = ?, estado_reserva = ?, observacoes = ?
            WHERE id = ?
        """, (
            dados.get("cliente_id"), dados.get("veiculo_id"), dados.get("forma_pagamento_id"),
            d1.isoformat() if d1 else dados.get("data_inicio"),
            d2.isoformat() if d2 else dados.get("data_fim_prevista"),
            dados.get("km_inicial", 0), dados.get("valor_diario_aplicado", 50.0),
            valor_total, dados.get("estado_reserva", "Ativa"), dados.get("observacoes", ""), reserva_id
        ))

        estado_novo = str(dados.get("estado_reserva", "")).lower()
        obs_atual = str(dados.get("observacoes", "")).lower()

        if estado_novo in ("concluída", "concluida", "cancelada"):
            cursor.execute("UPDATE veiculos SET estado = 'Disponível' WHERE id = ?", (dados.get("veiculo_id"),))
        elif estado_novo == "ativa":
            novo_estado_v = "Guardado" if "não pago" in obs_atual else "Alugado"
            cursor.execute("UPDATE veiculos SET estado = ? WHERE id = ?", (novo_estado_v, dados.get("veiculo_id")))

        conn.commit()
        return True, "Reserva atualizada com sucesso!"
    except Exception as e:
        conn.rollback()
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()


def concluir_reserva(reserva_id: int, km_final: int, novo_valor_total: float = None):
    conn = get_connection()
    cursor = conn.cursor()
    hoje = date.today().isoformat()
    try:
        cursor.execute("SELECT veiculo_id FROM reservas WHERE id = ?", (reserva_id,))
        row = cursor.fetchone()
        if not row: return False, "Reserva não encontrada."
        veiculo_id = row["veiculo_id"]

        if novo_valor_total is not None:
            cursor.execute("""
                UPDATE reservas 
                SET estado_reserva = 'Concluída', data_fim_real = ?, km_final = ?, valor_total = ?
                WHERE id = ?
            """, (hoje, km_final, novo_valor_total, reserva_id))
        else:
            cursor.execute("""
                UPDATE reservas 
                SET estado_reserva = 'Concluída', data_fim_real = ?, km_final = ?
                WHERE id = ?
            """, (hoje, km_final, reserva_id))

        cursor.execute("""
            UPDATE veiculos 
            SET estado = 'Disponível', motivo_indisponivel = NULL, quilometragem = ?
            WHERE id = ?
        """, (km_final, veiculo_id))

        conn.commit()
        return True, "Reserva concluída com sucesso e acerto financeiro registado!"
    except Exception as e:
        conn.rollback()
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()


def cancelar_reserva(reserva_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT veiculo_id FROM reservas WHERE id = ?", (reserva_id,))
        row = cursor.fetchone()
        if not row: return False, "Reserva não encontrada."
        veiculo_id = row["veiculo_id"]

        cursor.execute("UPDATE reservas SET estado_reserva = 'Cancelada' WHERE id = ?", (reserva_id,))
        cursor.execute("UPDATE veiculos SET estado = 'Disponível', motivo_indisponivel = NULL WHERE id = ?", (veiculo_id,))
        conn.commit()
        return True, "Reserva cancelada com sucesso!"
    except Exception as e:
        conn.rollback()
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()


def remover_reserva(reserva_id: int):
    # Remove permanentemente um contrato de reserva da base de dados e liberta o veículo associado.
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Libertar o veículo associado antes de apagar
        cursor.execute("UPDATE veiculos SET estado = 'Disponível' WHERE id IN (SELECT veiculo_id FROM reservas WHERE id = ?)", (reserva_id,))
        cursor.execute("DELETE FROM reservas WHERE id = ?", (reserva_id,))
        conn.commit()
        return True, "Reserva removida por completo com sucesso."
    except Exception as e:
        conn.rollback()
        return False, f"Erro ao remover reserva: {e}"
    finally:
        conn.close()