# Módulo: dashboard_view.py
# Descrição: Interface principal do sistema Luxury Wheels.
           # Gere o menu de navegação, layout, gráficos e tabelas.

from datetime import datetime
import customtkinter as ctk
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database.queries import (
    obter_metricas_dashboard,
    obter_disponibilidade_separada,
    listar_veiculos_alugados_resumo,
    verificar_avisos_manutencao_unificados,
    obter_ultimos_clientes
)

from views.vehicles_view import PainelVeiculos
from views.clients_view import PainelClientes
from views.rentals_view import PainelReservas
from views.payments_view import PainelPagamentos


class JanelaPrincipal(ctk.CTk):
    def __init__(self, dados_utilizador):
        super().__init__()

        self.dados_utilizador = dados_utilizador
        self._alerta_manutencao_exibido = False

        self.title("Luxury Wheels - Gestão Integrada de Frota")
        self.geometry("1340x840")
        self.minsize(1180, 720)
        self.after(0, lambda: self.state("zoomed"))

        # Fundo escuro moderno da aplicação
        self.configure(fg_color="#0F131A")

        self.configurar_estilos_tabelas()
        self.criar_cabecalho_expandido()
        self.criar_menu_navegacao_distribuido()

        # Área dinâmica de conteúdo central
        self.area_conteudo = ctk.CTkFrame(self, fg_color="transparent")
        self.area_conteudo.pack(fill="both", expand=True, padx=22, pady=(0, 15))

        # Carregar o Dashboard por defeito ao iniciar
        self.carregar_dashboard()

    def configurar_estilos_tabelas(self):
        # Configura fontes amplas (12px) e linhas espaçadas (32px) para todas as tabelas do dashboard.
        estilo = ttk.Style()
        estilo.theme_use("clam")

        estilo.configure(
            "Dashboard.Treeview.Heading",
            background="#1E2430",
            foreground="#F8FAFC",
            font=("Arial", 12, "bold"),
            relief="flat",
            padding=8
        )
        estilo.map("Dashboard.Treeview.Heading", background=[("active", "#2D3748")])

        estilo.configure(
            "Dashboard.Treeview",
            background="#161B26",
            foreground="#E2E8F0",
            fieldbackground="#161B26",
            rowheight=32,
            font=("Arial", 12),
            borderwidth=0
        )
        estilo.map(
            "Dashboard.Treeview",
            background=[("selected", "#2563EB")],
            foreground=[("selected", "#FFFFFF")]
        )

    def criar_cabecalho_expandido(self):
        # Cria a barra superior com o logótipo da marca e dados da sessão ativa.
        cabecalho = ctk.CTkFrame(self, height=65, fg_color="#181E29", corner_radius=0)
        cabecalho.pack(fill="x", pady=(0, 10))

        conteudo_cab = ctk.CTkFrame(cabecalho, fg_color="transparent")
        conteudo_cab.pack(fill="both", expand=True, padx=24, pady=8)

        ctk.CTkLabel(
            conteudo_cab,
            text="LUXURY WHEELS",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#F8FAFC"
        ).pack(side="left")

        nome_user = self.dados_utilizador.get("nome_completo") or self.dados_utilizador.get("username", "Utilizador")
        cargo_user = self.dados_utilizador.get("nivel_acesso", "Administrador")

        ctk.CTkLabel(
            conteudo_cab,
            text=f"Sessão iniciada como: {nome_user}  |  {cargo_user}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#94A3B8"
        ).pack(side="right")

    def criar_menu_navegacao_distribuido(self):
        # Cria os botões de navegação distribuídos uniformemente em largura total.
        menu_frame = ctk.CTkFrame(self, height=50, fg_color="transparent")
        menu_frame.pack(fill="x", padx=22, pady=(0, 12))

        botoes = [
            ("Dashboard Geral", self.carregar_dashboard),
            ("Veículos", self.abrir_veiculos),
            ("Clientes", self.abrir_clientes),
            ("Reservas", self.abrir_reservas),
            ("Formas de Pagamento", self.abrir_pagamentos)
        ]

        self.btn_menu_dict = {}
        for idx in range(len(botoes)):
            menu_frame.grid_columnconfigure(idx, weight=1, uniform="menu_cols")

        for idx, (texto, comando) in enumerate(botoes):
            btn = ctk.CTkButton(
                menu_frame,
                text=texto,
                height=42,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="#181E29",
                hover_color="#242E3F",
                border_width=1,
                border_color="#2E3A4E",
                text_color="#E2E8F0",
                command=comando
            )
            btn.grid(row=0, column=idx, padx=4, sticky="ew")
            self.btn_menu_dict[texto] = btn

    def destacar_botao_ativo(self, nome_ativo):
        # Atualiza visualmente o botão do menu que se encontra selecionado.
        for nome, btn in self.btn_menu_dict.items():
            if nome == nome_ativo:
                btn.configure(fg_color="#2563EB", hover_color="#1D4ED8", text_color="#FFFFFF", border_width=0)
            else:
                btn.configure(fg_color="#181E29", hover_color="#242E3F", text_color="#E2E8F0", border_width=1)

    def limpar_area_conteudo(self):
        # Remove todos os widgets da área dinâmica central para permitir transições limpas.
        for widget in self.area_conteudo.winfo_children():
            widget.destroy()

    def carregar_dashboard(self):
        # Constrói o layout completo do Dashboard e atualiza os dados em tempo real da base de dados.
        self.destacar_botao_ativo("Dashboard Geral")
        self.limpar_area_conteudo()

        # Obter dados atualizados diretamente da base de dados
        metricas = obter_metricas_dashboard()
        avisos_15_dias = verificar_avisos_manutencao_unificados(15)
        avisos_urgentes_5_dias = verificar_avisos_manutencao_unificados(5)

        # Contentor principal em grelha horizontal
        container_horizontal = ctk.CTkFrame(self.area_conteudo, fg_color="transparent")
        container_horizontal.pack(fill="both", expand=True)

        col_esquerda = ctk.CTkFrame(container_horizontal, fg_color="transparent")
        col_esquerda.place(relx=0.0, rely=0.0, relwidth=0.655, relheight=1.0)

        col_direita = ctk.CTkFrame(container_horizontal, fg_color="transparent")
        col_direita.place(relx=0.665, rely=0.0, relwidth=0.335, relheight=1.0)

        # ======================================================================
        # COLUNA ESQUERDA (2/3) - LINHA 1: CARTÕES KPI
        # ======================================================================
        linha1 = ctk.CTkFrame(col_esquerda, fg_color="transparent")
        linha1.pack(fill="x", pady=(0, 10))

        # KPI: Faturação Mensal
        card_fat = ctk.CTkFrame(linha1, fg_color="#181E29", corner_radius=8, border_width=1, border_color="#283244")
        card_fat.pack(side="left", fill="both", expand=True, padx=(0, 8))

        ctk.CTkLabel(card_fat, text="Faturação deste Mês", font=ctk.CTkFont(size=14, weight="bold"), text_color="#94A3B8").pack(pady=(12, 2))
        fin_bloco = metricas["financas_mes"]
        tot_fat = fin_bloco["total_faturado"] if isinstance(fin_bloco, dict) else float(fin_bloco)
        tot_res = fin_bloco["total_reservas"] if isinstance(fin_bloco, dict) and "total_reservas" in fin_bloco else metricas.get("total_reservas_mes", 0)
        ctk.CTkLabel(card_fat, text=f"€ {tot_fat:.2f}", font=ctk.CTkFont(size=25, weight="bold"), text_color="#10B981").pack(pady=2)
        ctk.CTkLabel(card_fat, text=f"{tot_res} contrato(s) faturado(s) este mês", font=ctk.CTkFont(size=12), text_color="#64748B").pack(pady=(0, 12))

        # KPI: Alertas de Manutenção (15 Dias)
        card_manut = ctk.CTkFrame(linha1, fg_color="#181E29", corner_radius=8, border_width=1, border_color="#283244")
        card_manut.pack(side="right", fill="both", expand=True, padx=(8, 0))

        ctk.CTkLabel(card_manut, text="Manutenções Próximas (15 Dias)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#94A3B8").pack(pady=(12, 2))
        viaturas_afetadas = len(avisos_15_dias)
        ctk.CTkLabel(card_manut, text=f"{viaturas_afetadas} Viatura(s) em Alerta", font=ctk.CTkFont(size=25, weight="bold"), text_color="#F8FAFC").pack(pady=2)
        ctk.CTkLabel(card_manut, text="Próximas duas semanas ou já expiradas", font=ctk.CTkFont(size=12), text_color="#64748B").pack(pady=(0, 12))

        # ======================================================================
        # COLUNA ESQUERDA (2/3) - LINHA 2: GRÁFICOS DONUT (TIPO E CATEGORIA)
        # ======================================================================
        linha2 = ctk.CTkFrame(col_esquerda, fg_color="#181E29", corner_radius=8, border_width=1, border_color="#283244")
        linha2.pack(fill="both", expand=True, pady=(0, 10))

        topo_l2 = ctk.CTkFrame(linha2, fg_color="transparent")
        topo_l2.pack(fill="x", padx=14, pady=(10, 2))
        ctk.CTkLabel(topo_l2, text="📊 Disponibilidade da Frota", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")

        ctk.CTkButton(
            topo_l2, text="Mais info...", width=95, height=28,
            font=ctk.CTkFont(size=12, weight="bold"), fg_color="#2563EB", hover_color="#1D4ED8",
            command=self.abrir_veiculos
        ).pack(side="right")

        corpo_graficos = ctk.CTkFrame(linha2, fg_color="transparent")
        corpo_graficos.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        tipos_disp, categ_disp = obter_disponibilidade_separada()

        box_grafico_tipo = ctk.CTkFrame(corpo_graficos, fg_color="#12161F", corner_radius=6)
        box_grafico_tipo.pack(side="left", fill="both", expand=True, padx=(0, 6), pady=4)

        box_grafico_cat = ctk.CTkFrame(corpo_graficos, fg_color="#12161F", corner_radius=6)
        box_grafico_cat.pack(side="right", fill="both", expand=True, padx=(6, 0), pady=4)

        paleta_elegante = ["#10B981", "#8B5CF6", "#F59E0B", "#06B6D4", "#EC4899", "#3B82F6"]
        self.renderizar_grafico_donut(box_grafico_tipo, tipos_disp, "tipo", "Disponíveis por Tipo", paleta_elegante)
        self.renderizar_grafico_donut(box_grafico_cat, categ_disp, "categoria", "Disponíveis por Categoria", paleta_elegante)

        # ======================================================================
        # COLUNA ESQUERDA (2/3) - LINHA 3: VEÍCULOS ALUGADOS
        # ======================================================================
        linha3 = ctk.CTkFrame(col_esquerda, fg_color="#181E29", corner_radius=8, border_width=1, border_color="#283244")
        linha3.pack(fill="both", expand=True)

        topo_l3 = ctk.CTkFrame(linha3, fg_color="transparent")
        topo_l3.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(topo_l3, text="📋 Veículos Alugados & Prazos Previstos", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")

        ctk.CTkButton(
            topo_l3, text="Mais info...", width=95, height=28,
            font=ctk.CTkFont(size=12, weight="bold"), fg_color="#2563EB", hover_color="#1D4ED8",
            command=self.abrir_reservas
        ).pack(side="right")

        box_alugados = ctk.CTkFrame(linha3, fg_color="#12161F", corner_radius=6)
        box_alugados.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        tab_alug = ttk.Treeview(box_alugados, columns=("Matricula", "Tipo", "Dias"), show="headings", style="Dashboard.Treeview", height=4)
        tab_alug.heading("Matricula", text="Matrícula")
        tab_alug.column("Matricula", width=125, anchor="center")
        tab_alug.heading("Tipo", text="Tipo / Modelo")
        tab_alug.column("Tipo", width=250, anchor="center")
        tab_alug.heading("Dias", text="Dias Restantes")
        tab_alug.column("Dias", width=140, anchor="center")

        scr_alug = ttk.Scrollbar(box_alugados, orient="vertical", command=tab_alug.yview)
        tab_alug.configure(yscrollcommand=scr_alug.set)
        tab_alug.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scr_alug.pack(side="right", fill="y", pady=4)

        for a in listar_veiculos_alugados_resumo():
            tab_alug.insert("", "end", values=(a["matricula"], f"{a['tipo']} - {a['modelo']}", a["dias_restantes"]))

        # ======================================================================
        # COLUNA DIREITA (1/3) - BLOCO 1: AGENDA DE MANUTENÇÕES (15 DIAS)
        # ======================================================================
        painel_manut = ctk.CTkFrame(col_direita, fg_color="#181E29", corner_radius=8, border_width=1, border_color="#283244")
        painel_manut.pack(fill="both", expand=True, pady=(0, 10))

        topo_man = ctk.CTkFrame(painel_manut, fg_color="transparent")
        topo_man.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(topo_man, text="🔧 Manutenções Críticas (15 Dias)", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")

        ctk.CTkButton(
            topo_man, text="Mais info...", width=95, height=28,
            font=ctk.CTkFont(size=12, weight="bold"), fg_color="#2563EB", hover_color="#1D4ED8",
            command=lambda: self.abrir_modal_todas_manutencoes(avisos_15_dias, titulo_alerta=False)
        ).pack(side="right")

        box_man = ctk.CTkFrame(painel_manut, fg_color="#12161F", corner_radius=6)
        box_man.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        tab_man = ttk.Treeview(box_man, columns=("Matricula", "Data", "Tipo"), show="headings", style="Dashboard.Treeview", height=5)
        tab_man.heading("Matricula", text="Matrícula")
        tab_man.column("Matricula", width=110, anchor="center")
        tab_man.heading("Data", text="Data Limite")
        tab_man.column("Data", width=115, anchor="center")
        tab_man.heading("Tipo", text="Intervenção")
        tab_man.column("Tipo", width=170, anchor="center")

        scr_man = ttk.Scrollbar(box_man, orient="vertical", command=tab_man.yview)
        tab_man.configure(yscrollcommand=scr_man.set)
        tab_man.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scr_man.pack(side="right", fill="y", pady=4)

        for av in avisos_15_dias:
            tab_man.insert("", "end", values=(av["matricula"], av["data_limite"], f"{av['tipo']} ({av['estado_tempo']})"))

        # ======================================================================
        # COLUNA DIREITA (1/3) - BLOCO 2: NOVOS CLIENTES
        # ======================================================================
        painel_clientes = ctk.CTkFrame(col_direita, fg_color="#181E29", corner_radius=8, border_width=1, border_color="#283244")
        painel_clientes.pack(fill="both", expand=True)

        topo_cli = ctk.CTkFrame(painel_clientes, fg_color="transparent")
        topo_cli.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(topo_cli, text="👥 Novos Clientes", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")

        ctk.CTkButton(
            topo_cli, text="Mais info...", width=95, height=28,
            font=ctk.CTkFont(size=12, weight="bold"), fg_color="#2563EB", hover_color="#1D4ED8",
            command=self.abrir_clientes
        ).pack(side="right")

        box_cli = ctk.CTkFrame(painel_clientes, fg_color="#12161F", corner_radius=6)
        box_cli.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        tab_cli = ttk.Treeview(box_cli, columns=("Nome", "Telefone"), show="headings", style="Dashboard.Treeview", height=5)
        tab_cli.heading("Nome", text="Nome Completo")
        tab_cli.column("Nome", width=230, anchor="center")
        tab_cli.heading("Telefone", text="Contacto")
        tab_cli.column("Telefone", width=160, anchor="center")

        scr_cli = ttk.Scrollbar(box_cli, orient="vertical", command=tab_cli.yview)
        tab_cli.configure(yscrollcommand=scr_cli.set)
        tab_cli.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scr_cli.pack(side="right", fill="y", pady=4)

        for c in obter_ultimos_clientes(10):
            tab_cli.insert("", "end", values=(c["nome"], c["telefone"]))

        if avisos_urgentes_5_dias and not self._alerta_manutencao_exibido:
            self._alerta_manutencao_exibido = True
            self.after(500, lambda: self.abrir_modal_todas_manutencoes(avisos_urgentes_5_dias, titulo_alerta=True))

    def renderizar_grafico_donut(self, container, dados, chave_nome, titulo, paleta_cores):
        # Renderiza um gráfico Donut limpo com valores absolutos nas fatias e total no canto inferior direito.
        nomes = [d[chave_nome] for d in dados] if dados else ["Sem Dados"]
        quantidades = [d["quantidade"] for d in dados] if dados else [0]
        total_viaturas = sum(quantidades)

        fig = Figure(figsize=(4.0, 2.3), dpi=95, facecolor="#12161F")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#12161F")

        if total_viaturas == 0:
            ax.pie([1], colors=["#1E293B"], wedgeprops=dict(width=0.45, edgecolor="#12161F", linewidth=2))
            ax.set_title(titulo, color="#F8FAFC", fontsize=13, fontweight="bold", pad=8)
            fig.text(0.92, 0.12, "Total: 0", ha="right", va="center", color="#94A3B8", fontsize=11, fontweight="bold")
        else:
            def formato_valor_absoluto(pct):
                val = int(round(pct * total_viaturas / 100.0))
                return f"{val}" if val > 0 else ""

            wedges, texts, autotexts = ax.pie(
                quantidades,
                labels=None,
                autopct=formato_valor_absoluto,
                pctdistance=0.74,
                startangle=140,
                colors=paleta_cores[:len(nomes)],
                wedgeprops=dict(width=0.48, edgecolor="#12161F", linewidth=2.5)
            )

            for at in autotexts:
                at.set_color("#FFFFFF")
                at.set_fontsize(12)
                at.set_fontweight("bold")

            ax.set_title(titulo, color="#F8FAFC", fontsize=13, fontweight="bold", pad=8)

            ax.legend(
                wedges, nomes, loc="upper left", bbox_to_anchor=(0.95, 0.90),
                frameon=False, fontsize=11, labelspacing=0.5, labelcolor="#E2E8F0"
            )

            fig.text(
                0.94, 0.14, f"Total: {total_viaturas} viaturas",
                ha="right", va="center", color="#38BDF8", fontsize=11, fontweight="bold"
            )

        fig.tight_layout(pad=1.0)
        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def abrir_modal_todas_manutencoes(self, avisos, titulo_alerta=False):
        modal = ctk.CTkToplevel(self)
        modal.title("Alerta de Manutenções Urgentes" if titulo_alerta else "Agenda de Manutenções (15 Dias)")
        modal.geometry("740x500")
        modal.grab_set()

        ctk.CTkLabel(
            modal,
            text=f"Atenção: {len(avisos)} Viatura(s) em Alerta" if titulo_alerta else f"Agenda Completa ({len(avisos)} Viaturas)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#F8FAFC"
        ).pack(pady=(16, 6))

        frame_tabela = ctk.CTkFrame(modal, fg_color="#12161F", corner_radius=6)
        frame_tabela.pack(fill="both", expand=True, padx=18, pady=5)

        cols = ("Matricula", "Modelo", "Data", "Tipo", "Urgencia")
        tree = ttk.Treeview(frame_tabela, columns=cols, show="headings", style="Dashboard.Treeview", height=10)

        larguras = [110, 160, 115, 160, 110]
        for col, larg in zip(cols, larguras):
            tree.heading(col, text=col)
            tree.column(col, width=larg, anchor="center")

        scr = ttk.Scrollbar(frame_tabela, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scr.set)
        tree.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scr.pack(side="right", fill="y", pady=4)

        for av in avisos:
            tree.insert("", "end", values=(av["matricula"], av["modelo"], av["data_limite"], av["tipo"], av["estado_tempo"]))

        ctk.CTkButton(
            modal, text="Compreendido" if titulo_alerta else "Fechar Janela",
            width=140, height=36, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563EB", hover_color="#1D4ED8", command=modal.destroy
        ).pack(pady=14)

    def abrir_veiculos(self):
        self.destacar_botao_ativo("Veículos")
        self.limpar_area_conteudo()
        PainelVeiculos(self.area_conteudo).pack(fill="both", expand=True)

    def abrir_clientes(self):
        self.destacar_botao_ativo("Clientes")
        self.limpar_area_conteudo()
        PainelClientes(self.area_conteudo).pack(fill="both", expand=True)

    def abrir_reservas(self):
        self.destacar_botao_ativo("Reservas")
        self.limpar_area_conteudo()
        PainelReservas(self.area_conteudo).pack(fill="both", expand=True)

    def abrir_pagamentos(self):
        self.destacar_botao_ativo("Formas de Pagamento")
        self.limpar_area_conteudo()
        PainelPagamentos(self.area_conteudo).pack(fill="both", expand=True)