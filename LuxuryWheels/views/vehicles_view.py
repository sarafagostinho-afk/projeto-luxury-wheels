# Módulo: vehicles_view.py
# Descrição: Gestão visual de veículos do Luxury Wheels.
           # Gere listagem, pesquisa, filtros, seleção múltipla, fichas técnicas com imagens e criação de reservas.

import os
import shutil
from datetime import datetime, date
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from PIL import Image

from database.queries import (
    listar_veiculos,
    adicionar_veiculo,
    atualizar_veiculo,
    remover_veiculo,
    alterar_estado_veiculo,
    listar_clientes,
    listar_formas_pagamento,
    criar_reserva
)
from services.export_service import exportar_para_csv, exportar_para_excel
from utils.table_sort import configurar_ordenacao_treeview

PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_VEICULOS = os.path.join(PROJ_ROOT, "assets", "vehicles")
os.makedirs(PASTA_VEICULOS, exist_ok=True)


class PainelVeiculos(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10, fg_color="transparent")
        self.parent = parent
        self.veiculo_selecionado = None
        self.lista_veiculos_cache = []
        self.ids_selecionados = set()
        self._cache_imagens = {}
        self.painel_filtros_visivel = False

        self.configurar_estilo_tabela()
        self.criar_barra_superior()
        self.criar_gaveta_filtros()
        self.criar_area_conteudo()
        self.carregar_dados_tabela()

    def configurar_estilo_tabela(self):
        # Configura fontes amplas (11px) e linhas espaçadas (32px) para a tabela de veículos.
        estilo = ttk.Style()
        estilo.theme_use("clam")

        estilo.configure(
            "Vehicles.Treeview.Heading",
            background="#1F2937",
            foreground="#F9FAFB",
            font=("Arial", 11, "bold"),
            relief="flat",
            padding=8
        )
        estilo.map("Vehicles.Treeview.Heading", background=[("active", "#374151")])

        estilo.configure(
            "Vehicles.Treeview",
            background="#111827",
            foreground="#E5E7EB",
            fieldbackground="#111827",
            rowheight=32,
            font=("Arial", 11),
            borderwidth=0
        )
        estilo.map(
            "Vehicles.Treeview",
            background=[("selected", "#1E3A8A")],
            foreground=[("selected", "#FFFFFF")]
        )

    def criar_barra_superior(self):
        # Cria a barra de ferramentas superior com pesquisa rápida, filtros e exportações.
        self.topo_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.topo_frame.pack(fill="x", padx=15, pady=(12, 6))

        ctk.CTkLabel(self.topo_frame, text="🔍 Pesquisa:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0, 6))
        self.ent_pesquisa = ctk.CTkEntry(
            self.topo_frame,
            placeholder_text="Matrícula, Marca ou Modelo...",
            width=260,
            height=34,
            font=ctk.CTkFont(size=12)
        )
        self.ent_pesquisa.pack(side="left", padx=(0, 10))
        self.ent_pesquisa.bind("<KeyRelease>", lambda _: self.carregar_dados_tabela())

        self.btn_toggle_filtros = ctk.CTkButton(
            self.topo_frame,
            text="⚙️ Filtros Avançados (▼)",
            width=175,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1F2937",
            hover_color="#374151",
            border_width=1,
            border_color="#4B5563",
            command=self.alternar_gaveta_filtros
        )
        self.btn_toggle_filtros.pack(side="left", padx=(0, 10))

        btn_limpar = ctk.CTkButton(
            self.topo_frame,
            text="Limpar",
            width=70,
            height=34,
            font=ctk.CTkFont(size=12),
            fg_color="gray40",
            hover_color="gray30",
            command=self.limpar_todos_filtros
        )
        btn_limpar.pack(side="left")

        btn_exp_excel = ctk.CTkButton(
            self.topo_frame,
            text="📥 Exportar Excel",
            fg_color="#27AE60",
            hover_color="#1E8449",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=125,
            height=34,
            command=self.acao_exportar_excel
        )
        btn_exp_excel.pack(side="right", padx=4)

        btn_exp_csv = ctk.CTkButton(
            self.topo_frame,
            text="📥 Exportar CSV",
            fg_color="#2980B9",
            hover_color="#1F618D",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=115,
            height=34,
            command=self.acao_exportar_csv
        )
        btn_exp_csv.pack(side="right", padx=4)

    def criar_gaveta_filtros(self):
        # Cria o painel retrátil de filtros técnicos e comerciais.
        self.frame_gaveta = ctk.CTkFrame(
            self,
            fg_color="#161B26",
            corner_radius=8,
            border_width=1,
            border_color="#283244"
        )

        inner = ctk.CTkFrame(self.frame_gaveta, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        def criar_filtro_combo(rotulo, valores):
            f = ctk.CTkFrame(inner, fg_color="transparent")
            f.pack(side="left", padx=6)
            ctk.CTkLabel(f, text=rotulo, font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(anchor="w", pady=(0, 2))
            cb = ctk.CTkComboBox(
                f, values=valores, width=130, height=32,
                font=ctk.CTkFont(size=12), command=lambda _: self.carregar_dados_tabela()
            )
            cb.set(valores[0])
            cb.pack()
            return cb

        self.cb_tipo = criar_filtro_combo("Tipo de Veículo:", ["Todos", "Carro", "Moto", "Carrinha de Carga", "Camião", "Autocarro"])
        self.cb_categoria = criar_filtro_combo("Categoria:", ["Todas", "Económico", "Médio", "SUV", "Luxo", "Desportivo"])
        self.cb_transmissao = criar_filtro_combo("Transmissão:", ["Todas", "Manual", "Automática"])
        self.cb_combustivel = criar_filtro_combo("Combustível:", ["Todos", "Gasolina", "Gasóleo", "Elétrico", "Híbrido"])
        self.cb_estado = criar_filtro_combo("Estado:", ["Todos", "Disponível", "Alugado", "Manutenção", "Guardado"])

        btn_fechar = ctk.CTkButton(
            inner, text="✕ Fechar", width=80, height=32,
            font=ctk.CTkFont(size=11), fg_color="transparent", border_width=1,
            border_color="#4B5563", hover_color="#1F2937", command=self.alternar_gaveta_filtros
        )
        btn_fechar.pack(side="right", padx=(15, 0), pady=(14, 0))

    def alternar_gaveta_filtros(self):
        if self.painel_filtros_visivel:
            self.frame_gaveta.pack_forget()
            self.btn_toggle_filtros.configure(text="⚙️ Filtros Avançados (▼)", fg_color="#1F2937")
            self.painel_filtros_visivel = False
        else:
            self.frame_gaveta.pack(fill="x", padx=15, pady=(0, 10), before=self.meio_frame)
            self.btn_toggle_filtros.configure(text="⚙️ Filtros Avançados (▲)", fg_color="#2563EB")
            self.painel_filtros_visivel = True

    def limpar_todos_filtros(self):
        self.ent_pesquisa.delete(0, "end")
        for cb in [self.cb_tipo, self.cb_categoria, self.cb_transmissao, self.cb_combustivel, self.cb_estado]:
            cb.set(cb.cget("values")[0])
        self.carregar_dados_tabela()

    def criar_area_conteudo(self):
        # Cria a tabela principal de veículos e o painel inferior de detalhes.
        self.meio_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.meio_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        frame_tabela = ctk.CTkFrame(self.meio_frame, fg_color="#111827", corner_radius=8)
        frame_tabela.pack(fill="both", expand=True, pady=(0, 10))

        barra_sel = ctk.CTkFrame(frame_tabela, fg_color="transparent")
        barra_sel.pack(fill="x", padx=10, pady=(6, 2))

        self.lbl_contador_sel = ctk.CTkLabel(barra_sel, text="Selecionados: 0", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_contador_sel.pack(side="left")

        ctk.CTkButton(
            barra_sel, text="Selecionar Todos", width=115, height=26,
            font=ctk.CTkFont(size=11), fg_color="gray30", hover_color="gray25", command=self.selecionar_todos
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            barra_sel, text="Desmarcar", width=100, height=26,
            font=ctk.CTkFont(size=11), fg_color="gray30", hover_color="gray25", command=self.desmarcar_todos
        ).pack(side="right")

        colunas = (
        "Sel", "ID", "Matrícula", "Marca", "Modelo", "Ano", "Tipo", "Categoria", "Passageiros", "Câmbio", "Combustível", "Preço/Dia", "Km", "Estado")
        self.tabela = ttk.Treeview(
            frame_tabela, columns=colunas, show="headings",
            style="Vehicles.Treeview", selectmode="browse", height=7
        )

        larguras = [35, 40, 95, 110, 125, 55, 95, 90, 85, 100, 95, 85, 85, 95]
        for col, larg in zip(colunas, larguras):
            self.tabela.heading(col, text=col)
            self.tabela.column(col, width=larg, anchor="center")

        configurar_ordenacao_treeview(self.tabela, colunas_ignoradas=["Sel"])

        scrollbar_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scrollbar_y.set)
        self.tabela.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar_y.pack(side="right", fill="y", pady=5)

        self.tabela.bind("<Button-1>", self.ao_clicar_tabela)
        self.tabela.bind("<<TreeviewSelect>>", self.ao_selecionar_veiculo)

        # Painel Inferior de Ficha Técnica e Operações
        self.frame_detalhes = ctk.CTkFrame(self.meio_frame, corner_radius=8, height=225)
        self.frame_detalhes.pack(fill="x", side="bottom")

        topo_det = ctk.CTkFrame(self.frame_detalhes, fg_color="transparent")
        topo_det.pack(fill="x", padx=16, pady=(10, 4))

        self.lbl_det_titulo = ctk.CTkLabel(topo_det, text="Ficha da Viatura", font=ctk.CTkFont(size=15, weight="bold"))
        self.lbl_det_titulo.pack(side="left")

        corpo_det = ctk.CTkFrame(self.frame_detalhes, fg_color="transparent")
        corpo_det.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self.frame_foto = ctk.CTkFrame(corpo_det, width=220, height=140, fg_color="#1F2937", corner_radius=6)
        self.frame_foto.pack(side="left", padx=(0, 16), pady=2)
        self.frame_foto.pack_propagate(False)

        self.lbl_foto = ctk.CTkLabel(self.frame_foto, text="Sem Imagem", font=ctk.CTkFont(size=12), text_color="gray")
        self.lbl_foto.pack(expand=True, fill="both")

        self.lbl_col_dados = ctk.CTkLabel(corpo_det, text="Selecione um veículo na tabela para visualizar a ficha técnica e opções.", justify="left", anchor="nw", font=ctk.CTkFont(size=13))
        self.lbl_col_dados.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.lbl_col_manut = ctk.CTkLabel(corpo_det, text="", justify="left", anchor="nw", font=ctk.CTkFont(size=13))
        self.lbl_col_manut.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.frame_botoes = ctk.CTkFrame(corpo_det, fg_color="transparent", width=195)
        self.frame_botoes.pack(side="right", fill="y")
        self.criar_botoes_operacao()

    def criar_botoes_operacao(self):
        self.btn_reservar = ctk.CTkButton(
            self.frame_botoes, text="🔑 Criar Reserva", fg_color="#10B981", hover_color="#059669",
            text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"), height=30, state="disabled", command=self.abrir_modal_reservar_veiculo
        )
        self.btn_reservar.pack(fill="x", pady=2)

        ctk.CTkButton(self.frame_botoes, text="➕ Novo Veículo", font=ctk.CTkFont(size=12, weight="bold"), height=30, command=self.abrir_modal_adicionar).pack(fill="x", pady=2)

        self.btn_editar = ctk.CTkButton(self.frame_botoes, text="✏️ Editar Veículo", fg_color="#2563EB", hover_color="#1D4ED8", text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"), height=30, state="disabled", command=self.abrir_modal_editar)
        self.btn_editar.pack(fill="x", pady=2)

        self.btn_estado = ctk.CTkButton(self.frame_botoes, text="🔄 Alterar Estado", fg_color="#D97706", hover_color="#B45309", text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"), height=30, state="disabled", command=self.abrir_modal_alterar_estado)
        self.btn_estado.pack(fill="x", pady=2)

        self.btn_remover = ctk.CTkButton(self.frame_botoes, text="🗑️ Remover", fg_color="#C0392B", hover_color="#922B21", text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"), height=30, state="disabled", command=self.acao_remover_veiculo)
        self.btn_remover.pack(fill="x", pady=2)

    def carregar_dados_tabela(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        termo = self.ent_pesquisa.get().strip() if hasattr(self, "ent_pesquisa") else ""
        self.lista_veiculos_cache = listar_veiculos(
            termo_pesquisa=termo,
            filtro_tipo=self.cb_tipo.get(),
            filtro_categoria=self.cb_categoria.get(),
            filtro_transmissao=self.cb_transmissao.get(),
            filtro_combustivel=self.cb_combustivel.get(),
            filtro_estado=self.cb_estado.get()
        )

        for v in self.lista_veiculos_cache:
            v_id = v["id"]
            check = "☑" if v_id in self.ids_selecionados else "☐"
            self.tabela.insert("", "end", iid=str(v_id), values=(
                check, v["id"], v["matricula"], v["marca"], v["modelo"],
                v.get("ano", "—"), v.get("tipo", "—"), v.get("categoria", "—"),
                v.get("num_passageiros", "—"), v.get("transmissao", "—"),
                v.get("combustivel", "—"), f"€ {float(v.get('preco_diario', 0)):.2f}",
                f"{v.get('quilometragem', 0)} km", v.get("estado", "Disponível")
            ))

        self.atualizar_contador_selecao()
        self.desativar_botoes_selecao()

    def ao_clicar_tabela(self, event):
        regiao = self.tabela.identify("region", event.x, event.y)
        coluna = self.tabela.identify_column(event.x)
        item_id = self.tabela.identify_row(event.y)

        if regiao == "cell" and coluna == "#1" and item_id:
            v_id = int(item_id)
            if v_id in self.ids_selecionados:
                self.ids_selecionados.remove(v_id)
            else:
                self.ids_selecionados.add(v_id)

            valores = list(self.tabela.item(item_id, "values"))
            valores[0] = "☑" if v_id in self.ids_selecionados else "☐"
            self.tabela.item(item_id, values=valores)
            self.atualizar_contador_selecao()

    def selecionar_todos(self):
        for v in self.lista_veiculos_cache:
            self.ids_selecionados.add(v["id"])
            if self.tabela.exists(str(v["id"])):
                vals = list(self.tabela.item(str(v["id"]), "values"))
                vals[0] = "☑"
                self.tabela.item(str(v["id"]), values=vals)
        self.atualizar_contador_selecao()

    def desmarcar_todos(self):
        self.ids_selecionados.clear()
        for item_id in self.tabela.get_children():
            vals = list(self.tabela.item(item_id, "values"))
            vals[0] = "☐"
            self.tabela.item(item_id, values=vals)
        self.atualizar_contador_selecao()

    def atualizar_contador_selecao(self):
        self.lbl_contador_sel.configure(text=f"Selecionados: {len(self.ids_selecionados)}")

    def ao_selecionar_veiculo(self, event):
        selecionado = self.tabela.selection()
        if not selecionado: return

        v = next((item for item in self.lista_veiculos_cache if str(item["id"]) == str(selecionado[0])), None)
        if not v: return

        self.veiculo_selecionado = v
        self.btn_editar.configure(state="normal")
        self.btn_estado.configure(state="normal")
        self.btn_remover.configure(state="normal")

        if str(v.get("estado", "")).lower() in ("disponível", "disponivel"):
            self.btn_reservar.configure(state="normal")
        else:
            self.btn_reservar.configure(state="disabled")

        self.lbl_det_titulo.configure(text=f"Ficha Técnica: {v['marca']} {v['modelo']} ({v['matricula']})")
        self.carregar_imagem_veiculo(v)

        self.lbl_col_dados.configure(text=(
            f"🚘 CARACTERÍSTICAS\n\n"
            f"• Ano: {v.get('ano', '—')}   |   Cor: {v.get('cor', '—')}\n"
            f"• Transmissão: {v.get('transmissao', '—')}   |   Lugares: {v.get('num_passageiros', '—')}\n"
            f"• Combustível: {v.get('combustivel', '—')}\n"
            f"• Tarifa: € {float(v.get('preco_diario', 0)):.2f} / dia"
        ))

        self.lbl_col_manut.configure(text=(
            f"⚙️ ESTADO & MANUTENÇÃO\n\n"
            f"• Estado Atual: {v.get('estado', 'Disponível')}\n"
            f"• Quilometragem: {v.get('quilometragem', 0)} km\n"
            f"• Próxima Revisão: {v.get('data_proxima_revisao') or 'Não agendada'}\n"
            f"• Próxima Inspeção: {v.get('data_proxima_inspecao') or 'Não agendada'}"
        ))

    def carregar_imagem_veiculo(self, veiculo: dict):
        for w in self.frame_foto.winfo_children(): w.destroy()
        v_id = veiculo.get("id")

        if v_id in self._cache_imagens and self._cache_imagens[v_id] is not None:
            ctk.CTkLabel(self.frame_foto, text="", image=self._cache_imagens[v_id]).pack(expand=True, fill="both")
            return

        caminho_bd = veiculo.get("imagem_path") or ""
        encontrado = caminho_bd if (caminho_bd and os.path.exists(caminho_bd)) else None

        if not encontrado:
            for ext in [".png", ".jpg", ".jpeg", ".webp", ".jfif"]:
                candidato = os.path.join(PASTA_VEICULOS, f"veiculo_{v_id}{ext}")
                if os.path.exists(candidato):
                    encontrado = candidato
                    break

        if encontrado:
            try:
                pil_img = Image.open(encontrado).copy()
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(210, 135))
                self._cache_imagens[v_id] = ctk_img
                ctk.CTkLabel(self.frame_foto, text="", image=ctk_img).pack(expand=True, fill="both")
            except Exception:
                ctk.CTkLabel(self.frame_foto, text="Erro ao carregar", font=ctk.CTkFont(size=12), text_color="gray").pack(expand=True, fill="both")
        else:
            ctk.CTkLabel(self.frame_foto, text="Sem Imagem", font=ctk.CTkFont(size=12), text_color="gray").pack(expand=True, fill="both")

    def desativar_botoes_selecao(self):
        self.btn_reservar.configure(state="disabled")
        self.btn_editar.configure(state="disabled")
        self.btn_estado.configure(state="disabled")
        self.btn_remover.configure(state="disabled")
        self.lbl_det_titulo.configure(text="Ficha da Viatura")
        self.lbl_col_dados.configure(text="Selecione um veículo na tabela para visualizar a ficha técnica e opções.")
        self.lbl_col_manut.configure(text="")
        for w in self.frame_foto.winfo_children(): w.destroy()
        ctk.CTkLabel(self.frame_foto, text="Sem Imagem", font=ctk.CTkFont(size=12), text_color="gray").pack(expand=True, fill="both")
        self.veiculo_selecionado = None

    def abrir_modal_reservar_veiculo(self):
        # Abre o modal de reserva integrado na vista de veículos com cálculo dinâmico de preço e pagamentos.
        if not self.veiculo_selecionado: return
        v = self.veiculo_selecionado
        clientes_cad = listar_clientes()
        formas_pag = listar_formas_pagamento()

        if not clientes_cad:
            messagebox.showwarning("Aviso", "Não existem clientes registados. Por favor, adicione um cliente primeiro.")
            return

        modal = ctk.CTkToplevel(self)
        modal.title(f"Reservar Viatura: {v['matricula']}")
        modal.geometry("520x620")
        modal.resizable(False, False)
        modal.grab_set()

        ctk.CTkLabel(modal, text=f"Novo Contrato — {v['marca']} {v['modelo']} ({v['matricula']})", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(16, 4))

        scroll = ctk.CTkScrollableFrame(modal, width=460, height=440)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        # Seleção de Cliente
        ctk.CTkLabel(scroll, text="Selecionar Cliente:", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
        dict_clientes = {f"{c['nome_completo']} (Tel: {c.get('telefone', '—')})": c["id"] for c in clientes_cad}
        cb_cli = ctk.CTkComboBox(scroll, values=list(dict_clientes.keys()), height=34, font=ctk.CTkFont(size=12))
        cb_cli.set(list(dict_clientes.keys())[0])
        cb_cli.pack(fill="x", pady=(0, 8))

        # Datas
        hoje_str = date.today().isoformat()
        ctk.CTkLabel(scroll, text="Data Início (AAAA-MM-DD):", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
        ent_ini = ctk.CTkEntry(scroll, height=34, font=ctk.CTkFont(size=12))
        ent_ini.insert(0, hoje_str)
        ent_ini.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(scroll, text="Data Fim Prevista (AAAA-MM-DD):", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
        ent_fim = ctk.CTkEntry(scroll, height=34, font=ctk.CTkFont(size=12))
        ent_fim.insert(0, hoje_str)
        ent_fim.pack(fill="x", pady=(0, 8))

        # Forma e Modalidade de Pagamento
        ctk.CTkLabel(scroll, text="Forma de Pagamento:", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
        dict_pag = {f["nome"]: f["id"] for f in formas_pag}
        cb_pag = ctk.CTkComboBox(scroll, values=list(dict_pag.keys()), height=34, font=ctk.CTkFont(size=12))
        cb_pag.set(list(dict_pag.keys())[0] if dict_pag else "Numerário")
        cb_pag.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(scroll, text="Modalidade (se Dinheiro):", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
        cb_modalidade = ctk.CTkComboBox(scroll, values=["Total", "Sinal (20%)", "Não Pago"], height=34, font=ctk.CTkFont(size=12))
        cb_modalidade.set("Total")
        cb_modalidade.pack(fill="x", pady=(0, 8))

        # Observações
        ctk.CTkLabel(scroll, text="Observações:", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
        ent_obs = ctk.CTkEntry(scroll, height=34, font=ctk.CTkFont(size=12), placeholder_text="Notas adicionais sobre o contrato...")
        ent_obs.pack(fill="x", pady=(0, 6))

        def confirmar_reserva():
            try:
                dt1 = datetime.strptime(ent_ini.get().strip(), "%Y-%m-%d").date()
                dt2 = datetime.strptime(ent_fim.get().strip(), "%Y-%m-%d").date()
                if dt2 < dt1:
                    messagebox.showerror("Erro", "A data de fim não pode ser anterior à data de início.")
                    return
            except ValueError:
                messagebox.showerror("Erro", "Formato de data inválido (use AAAA-MM-DD).")
                return

            mod_escolhida = cb_modalidade.get().split()[0]

            sucesso, msg, _ = criar_reserva(
                veiculo_id=v["id"],
                cliente_id=dict_clientes[cb_cli.get()],
                forma_pag_id=dict_pag[cb_pag.get()],
                data_inicio=ent_ini.get().strip(),
                data_fim=ent_fim.get().strip(),
                km_inicial=v.get("quilometragem", 0),
                valor_dia=v.get("preco_diario", 50.0),
                obs=ent_obs.get().strip(),
                modalidade_pagamento=mod_escolhida
            )

            if sucesso:
                if mod_escolhida == "Não":
                    messagebox.showwarning("Aviso", "⚠️ Viatura colocada no estado 'Guardado' (sem sinal pago).")
                messagebox.showinfo("Sucesso", msg)
                modal.destroy()
                self.carregar_dados_tabela()
            else:
                messagebox.showerror("Erro", msg)

        ctk.CTkButton(
            modal, text="Confirmar e Ativar Aluguer",
            fg_color="#10B981", hover_color="#059669",
            font=ctk.CTkFont(size=13, weight="bold"), height=38,
            command=confirmar_reserva
        ).pack(pady=12)

    def abrir_modal_adicionar(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Adicionar Novo Veículo")
        modal.geometry("560x650")
        modal.grab_set()

        ctk.CTkLabel(modal, text="Registo de Nova Viatura", font=ctk.CTkFont(size=17, weight="bold")).pack(pady=12)
        scroll = ctk.CTkScrollableFrame(modal, width=500, height=480)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        def criar_campo(rotulo, val=""):
            ctk.CTkLabel(scroll, text=rotulo, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
            ent = ctk.CTkEntry(scroll, height=34, font=ctk.CTkFont(size=12))
            if val: ent.insert(0, str(val))
            ent.pack(fill="x", pady=(0, 4))
            return ent

        ent_mat = criar_campo("Matrícula (Ex: AA-00-BB):")
        ent_marca = criar_campo("Marca:")
        ent_modelo = criar_campo("Modelo:")
        ent_ano = criar_campo("Ano:", "2024")

        def criar_combo(rotulo, valores, def_val):
            ctk.CTkLabel(scroll, text=rotulo, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
            cb = ctk.CTkComboBox(scroll, values=valores, height=34, font=ctk.CTkFont(size=12))
            cb.set(def_val)
            cb.pack(fill="x", pady=(0, 4))
            return cb

        cb_tipo = criar_combo("Tipo:", ["Carro", "Moto", "Carrinha de Carga", "Camião", "Autocarro"], "Carro")
        cb_cat = criar_combo("Categoria:", ["Económico", "Médio", "SUV", "Luxo", "Desportivo"], "Luxo")
        cb_trans = criar_combo("Transmissão:", ["Manual", "Automática"], "Automática")
        cb_comb = criar_combo("Combustível:", ["Gasolina", "Gasóleo", "Elétrico", "Híbrido"], "Gasolina")

        ent_lug = criar_campo("Nº Passageiros:", "5")
        ent_cor = criar_campo("Cor:", "Preto")
        ent_preco = criar_campo("Preço Diário (€):", "120.00")
        ent_km = criar_campo("Quilometragem:", "0")
        ent_rev = criar_campo("Próxima Revisão (AAAA-MM-DD):", "2026-10-15")
        ent_insp = criar_campo("Próxima Inspeção (AAAA-MM-DD):", "2026-10-30")

        var_foto = ctk.StringVar(value="")
        frame_img = ctk.CTkFrame(scroll, fg_color="transparent")
        frame_img.pack(fill="x", pady=(8, 10))
        lbl_f_nome = ctk.CTkLabel(frame_img, text="Nenhum ficheiro selecionado", font=ctk.CTkFont(size=12), text_color="gray", anchor="w")
        lbl_f_nome.pack(side="left", fill="x", expand=True)

        def escolher_f():
            c = filedialog.askopenfilename(filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.webp;*.jfif")])
            if c:
                var_foto.set(c)
                lbl_f_nome.configure(text=os.path.basename(c), text_color="#10B981")

        ctk.CTkButton(frame_img, text="📂 Escolher...", width=100, height=32, command=escolher_f).pack(side="right")

        def salvar():
            mat, marca, mod = ent_mat.get().strip(), ent_marca.get().strip(), ent_modelo.get().strip()
            if not (mat and marca and mod):
                messagebox.showerror("Erro", "Preencha matrícula, marca e modelo.")
                return
            try:
                ano, lug, preco, km = int(ent_ano.get()), int(ent_lug.get()), float(ent_preco.get()), int(ent_km.get())
            except ValueError:
                messagebox.showerror("Erro", "Campos numéricos inválidos.")
                return

            caminho_final = ""
            origem = var_foto.get()
            if origem and os.path.exists(origem):
                _, ext = os.path.splitext(origem)
                nome_novo = f"{mat.replace('-', '_').lower()}{ext}"
                destino = os.path.join(PASTA_VEICULOS, nome_novo)
                try:
                    shutil.copy2(origem, destino)
                    caminho_final = destino
                except Exception:
                    caminho_final = origem

            sucesso, msg = adicionar_veiculo({
                "matricula": mat, "marca": marca, "modelo": mod, "ano": ano,
                "tipo": cb_tipo.get(), "categoria": cb_cat.get(), "transmissao": cb_trans.get(),
                "combustivel": cb_comb.get(), "num_passageiros": lug, "cor": ent_cor.get().strip(),
                "preco_diario": preco, "quilometragem": km, "data_proxima_revisao": ent_rev.get().strip() or None,
                "data_proxima_inspecao": ent_insp.get().strip() or None, "imagem_path": caminho_final, "estado": "Disponível"
            })
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                modal.destroy()
                self.carregar_dados_tabela()
            else:
                messagebox.showerror("Erro", msg)

        ctk.CTkButton(modal, text="Gravar Veículo", fg_color="#10B981", hover_color="#059669", font=ctk.CTkFont(size=13, weight="bold"), height=38, command=salvar).pack(pady=14)

    def abrir_modal_editar(self):
        if not self.veiculo_selecionado: return
        v = self.veiculo_selecionado
        modal = ctk.CTkToplevel(self)
        modal.title(f"Editar Veículo #{v['id']}")
        modal.geometry("560x650")
        modal.grab_set()

        ctk.CTkLabel(modal, text=f"Editar Veículo #{v['id']}", font=ctk.CTkFont(size=17, weight="bold")).pack(pady=12)
        scroll = ctk.CTkScrollableFrame(modal, width=500, height=480)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        def criar_campo(rotulo, val=""):
            ctk.CTkLabel(scroll, text=rotulo, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
            ent = ctk.CTkEntry(scroll, height=34, font=ctk.CTkFont(size=12))
            if val is not None: ent.insert(0, str(val))
            ent.pack(fill="x", pady=(0, 4))
            return ent

        ent_mat = criar_campo("Matrícula:", v.get("matricula", ""))
        ent_marca = criar_campo("Marca:", v.get("marca", ""))
        ent_modelo = criar_campo("Modelo:", v.get("modelo", ""))
        ent_ano = criar_campo("Ano:", v.get("ano", 2024))

        def criar_combo(rotulo, valores, def_val):
            ctk.CTkLabel(scroll, text=rotulo, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
            cb = ctk.CTkComboBox(scroll, values=valores, height=34, font=ctk.CTkFont(size=12))
            cb.set(def_val if def_val in valores else valores[0])
            cb.pack(fill="x", pady=(0, 4))
            return cb

        cb_tipo = criar_combo("Tipo:", ["Carro", "Moto", "Carrinha de Carga", "Camião", "Autocarro"], v.get("tipo", "Carro"))
        cb_cat = criar_combo("Categoria:", ["Económico", "Médio", "SUV", "Luxo", "Desportivo"], v.get("categoria", "Luxo"))
        cb_trans = criar_combo("Transmissão:", ["Manual", "Automática"], v.get("transmissao", "Automática"))
        cb_comb = criar_combo("Combustível:", ["Gasolina", "Gasóleo", "Elétrico", "Híbrido"], v.get("combustivel", "Gasolina"))

        ent_lug = criar_campo("Nº Passageiros:", v.get("num_passageiros", 5))
        ent_cor = criar_campo("Cor:", v.get("cor", "Preto"))
        ent_preco = criar_campo("Preço Diário (€):", v.get("preco_diario", 50.0))
        ent_km = criar_campo("Quilometragem:", v.get("quilometragem", 0))
        ent_rev = criar_campo("Próxima Revisão:", v.get("data_proxima_revisao", ""))
        ent_insp = criar_campo("Próxima Inspeção:", v.get("data_proxima_inspecao", ""))

        var_foto = ctk.StringVar(value=v.get("imagem_path", ""))
        frame_img = ctk.CTkFrame(scroll, fg_color="transparent")
        frame_img.pack(fill="x", pady=(8, 10))
        lbl_f_nome = ctk.CTkLabel(frame_img, text=os.path.basename(v.get("imagem_path", "")) or "Sem foto", font=ctk.CTkFont(size=12), text_color="gray", anchor="w")
        lbl_f_nome.pack(side="left", fill="x", expand=True)

        def alterar_f():
            c = filedialog.askopenfilename(filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.webp;*.jfif")])
            if c:
                var_foto.set(c)
                lbl_f_nome.configure(text=os.path.basename(c), text_color="#3B82F6")

        ctk.CTkButton(frame_img, text="📂 Alterar...", width=100, height=32, command=alterar_f).pack(side="right")

        def guardar():
            mat, marca, mod = ent_mat.get().strip(), ent_marca.get().strip(), ent_modelo.get().strip()
            if not (mat and marca and mod):
                messagebox.showerror("Erro", "Preencha matrícula, marca e modelo.")
                return
            try:
                ano, lug, preco, km = int(ent_ano.get()), int(ent_lug.get()), float(ent_preco.get()), int(ent_km.get())
            except ValueError:
                messagebox.showerror("Erro", "Campos numéricos inválidos.")
                return

            if v["id"] in self._cache_imagens: del self._cache_imagens[v["id"]]

            sucesso, msg = atualizar_veiculo(v["id"], {
                "matricula": mat, "marca": marca, "modelo": mod, "ano": ano,
                "tipo": cb_tipo.get(), "categoria": cb_cat.get(), "transmissao": cb_trans.get(),
                "combustivel": cb_comb.get(), "num_passageiros": lug, "cor": ent_cor.get().strip(),
                "preco_diario": preco, "quilometragem": km, "data_proxima_revisao": ent_rev.get().strip() or None,
                "data_proxima_inspecao": ent_insp.get().strip() or None, "imagem_path": var_foto.get(), "estado": v.get("estado", "Disponível")
            })
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                modal.destroy()
                self.carregar_dados_tabela()
            else:
                messagebox.showerror("Erro", msg)

        ctk.CTkButton(modal, text="Guardar Alterações", fg_color="#2563EB", hover_color="#1D4ED8", font=ctk.CTkFont(size=13, weight="bold"), height=38, command=guardar).pack(pady=14)

    def abrir_modal_alterar_estado(self):
        if not self.veiculo_selecionado: return
        v = self.veiculo_selecionado
        modal = ctk.CTkToplevel(self)
        modal.title("Alterar Estado da Viatura")
        modal.geometry("400x280")
        modal.grab_set()

        ctk.CTkLabel(modal, text=f"Estado de {v['matricula']}", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(16, 5))
        cb_novo = ctk.CTkComboBox(modal, values=["Disponível", "Manutenção", "Alugado", "Guardado"], width=260, height=34)
        cb_novo.set(v.get("estado", "Disponível"))
        cb_novo.pack(pady=10)

        def aplicar():
            alterar_estado_veiculo(v["id"], cb_novo.get())
            messagebox.showinfo("Sucesso", "Estado atualizado!")
            modal.destroy()
            self.carregar_dados_tabela()

        ctk.CTkButton(modal, text="Confirmar", fg_color="#D97706", hover_color="#B45309", font=ctk.CTkFont(size=13, weight="bold"), height=36, command=aplicar).pack(pady=14)

    def acao_remover_veiculo(self):
        alvos = list(self.ids_selecionados) if self.ids_selecionados else ([self.veiculo_selecionado["id"]] if self.veiculo_selecionado else [])
        if not alvos: return
        if messagebox.askyesno("Confirmação", f"Remover {len(alvos)} veículo(s)?"):
            for vid in alvos: remover_veiculo(vid)
            self.ids_selecionados.clear()
            messagebox.showinfo("Sucesso", "Operação concluída!")
            self.carregar_dados_tabela()

    def acao_exportar_csv(self):
        dados = list(self.ids_selecionados) and [v for v in self.lista_veiculos_cache if v["id"] in self.ids_selecionados] or self.lista_veiculos_cache
        c = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="veiculos.csv")
        if c:
            sucesso, msg = exportar_para_csv(dados, c)
            messagebox.showinfo("Exportação", msg) if sucesso else messagebox.showerror("Erro", msg)

    def acao_exportar_excel(self):
        dados = list(self.ids_selecionados) and [v for v in self.lista_veiculos_cache if v["id"] in self.ids_selecionados] or self.lista_veiculos_cache
        c = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], initialfile="veiculos.xlsx")
        if c:
            sucesso, msg = exportar_para_excel(dados, c, titulo_folha="Veículos")
            messagebox.showinfo("Exportação", msg) if sucesso else messagebox.showerror("Erro", msg)