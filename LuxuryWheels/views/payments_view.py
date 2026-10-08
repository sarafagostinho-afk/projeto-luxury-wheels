# Módulo: payments_view.py
# Descrição: Gestão visual de formas de pagamento do Luxury Wheels.
           # Gere listagem, pesquisa, ordenação interativa, etc..

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog

from database.queries import (
    listar_formas_pagamento_detalhado,
    adicionar_forma_pagamento,
    atualizar_forma_pagamento,
    remover_forma_pagamento
)
from services.export_service import exportar_para_csv, exportar_para_excel
from utils.table_sort import configurar_ordenacao_treeview


class PainelPagamentos(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10, fg_color="transparent")
        self.parent = parent
        self.pagamento_selecionado = None
        self.lista_pagamentos_cache = []

        self.configurar_estilo_tabela()
        self.criar_barra_superior()
        self.criar_area_conteudo()
        self.carregar_dados_tabela()

    def configurar_estilo_tabela(self):
        # Configura fontes amplas (11px) e linhas espaçadas (32px) para a tabela de pagamentos.
        estilo = ttk.Style()
        estilo.theme_use("clam")

        estilo.configure(
            "Payments.Treeview.Heading",
            background="#1F2937",
            foreground="#F9FAFB",
            font=("Arial", 11, "bold"),
            relief="flat",
            padding=8
        )
        estilo.map("Payments.Treeview.Heading", background=[("active", "#374151")])

        estilo.configure(
            "Payments.Treeview",
            background="#111827",
            foreground="#E2E8F0",
            fieldbackground="#111827",
            rowheight=32,
            font=("Arial", 11),
            borderwidth=0
        )
        estilo.map(
            "Payments.Treeview",
            background=[("selected", "#1E3A8A")],
            foreground=[("selected", "#FFFFFF")]
        )

    def criar_barra_superior(self):
        # Cria a barra superior com pesquisa rápida e opções de exportação.
        topo_frame = ctk.CTkFrame(self, fg_color="transparent")
        topo_frame.pack(fill="x", padx=15, pady=(12, 8))

        ctk.CTkLabel(topo_frame, text="🔍 Pesquisa:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0, 6))
        self.ent_pesquisa = ctk.CTkEntry(
            topo_frame,
            placeholder_text="Nome do método de pagamento...",
            width=280,
            height=34,
            font=ctk.CTkFont(size=12)
        )
        self.ent_pesquisa.pack(side="left", padx=(0, 10))
        self.ent_pesquisa.bind("<KeyRelease>", lambda _: self.carregar_dados_tabela())

        btn_limpar = ctk.CTkButton(
            topo_frame, text="Limpar", width=75, height=34,
            font=ctk.CTkFont(size=12), fg_color="gray40", hover_color="gray30",
            command=self.limpar_filtros
        )
        btn_limpar.pack(side="left", padx=4)

        btn_exp_excel = ctk.CTkButton(
            topo_frame, text="📥 Exportar Excel", fg_color="#27AE60", hover_color="#1E8449",
            text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"), width=125, height=34,
            command=self.acao_exportar_excel
        )
        btn_exp_excel.pack(side="right", padx=4)

        btn_exp_csv = ctk.CTkButton(
            topo_frame, text="📥 Exportar CSV", fg_color="#2980B9", hover_color="#1F618D",
            text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"), width=115, height=34,
            command=self.acao_exportar_csv
        )
        btn_exp_csv.pack(side="right", padx=4)

    def limpar_filtros(self):
        self.ent_pesquisa.delete(0, "end")
        self.carregar_dados_tabela()

    def criar_area_conteudo(self):
        # Cria a tabela central e o painel inferior de detalhes.
        meio_frame = ctk.CTkFrame(self, fg_color="transparent")
        meio_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        frame_tabela = ctk.CTkFrame(meio_frame, fg_color="#111827", corner_radius=8)
        frame_tabela.pack(fill="both", expand=True, pady=(0, 10))

        colunas = ("ID", "Nome da Forma de Pagamento", "Descrição", "Contratos", "Total Faturado", "Estado")
        self.tabela = ttk.Treeview(
            frame_tabela, columns=colunas, show="headings",
            style="Payments.Treeview", selectmode="browse", height=8
        )

        larguras = [50, 220, 320, 100, 140, 100]
        for col, larg in zip(colunas, larguras):
            self.tabela.heading(col, text=col)
            self.tabela.column(col, width=larg, anchor="center")

        configurar_ordenacao_treeview(self.tabela)

        scrollbar_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scrollbar_y.set)
        self.tabela.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar_y.pack(side="right", fill="y", pady=5)

        self.tabela.bind("<<TreeviewSelect>>", self.ao_selecionar_pagamento)

        # Painel Inferior de Ficha
        self.frame_detalhes = ctk.CTkFrame(meio_frame, corner_radius=8, height=180)
        self.frame_detalhes.pack(fill="x", side="bottom")

        topo_det = ctk.CTkFrame(self.frame_detalhes, fg_color="transparent")
        topo_det.pack(fill="x", padx=16, pady=(10, 4))

        self.lbl_det_titulo = ctk.CTkLabel(topo_det, text="Ficha do Método de Pagamento", font=ctk.CTkFont(size=15, weight="bold"))
        self.lbl_det_titulo.pack(side="left")

        corpo_det = ctk.CTkFrame(self.frame_detalhes, fg_color="transparent")
        corpo_det.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self.lbl_col_dados = ctk.CTkLabel(corpo_det, text="Selecione um método na tabela para visualizar o volume de faturação e detalhes.", justify="left", anchor="nw", font=ctk.CTkFont(size=13))
        self.lbl_col_dados.pack(side="left", fill="both", expand=True, padx=(0, 12))

        self.frame_botoes = ctk.CTkFrame(corpo_det, fg_color="transparent", width=190)
        self.frame_botoes.pack(side="right", fill="y")
        self.criar_botoes_operacao()

    def criar_botoes_operacao(self):
        ctk.CTkButton(self.frame_botoes, text="➕ Novo Método", font=ctk.CTkFont(size=12, weight="bold"), height=32, command=self.abrir_modal_adicionar).pack(fill="x", pady=3)

        self.btn_editar = ctk.CTkButton(self.frame_botoes, text="✏️ Editar Método", fg_color="#2563EB", hover_color="#1D4ED8", text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"), height=32, state="disabled", command=self.abrir_modal_editar)
        self.btn_editar.pack(fill="x", pady=3)

        self.btn_remover = ctk.CTkButton(self.frame_botoes, text="🗑️ Remover", fg_color="#C0392B", hover_color="#922B21", text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"), height=32, state="disabled", command=self.acao_remover_pagamento)
        self.btn_remover.pack(fill="x", pady=3)

    def carregar_dados_tabela(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        termo = self.ent_pesquisa.get().strip() if hasattr(self, "ent_pesquisa") else ""
        self.lista_pagamentos_cache = listar_formas_pagamento_detalhado(termo_pesquisa=termo)

        for p in self.lista_pagamentos_cache:
            tot = float(p.get("total_faturado", 0))
            estado_txt = "Ativo" if p.get("ativo", 1) == 1 else "Inativo"
            self.tabela.insert("", "end", iid=str(p["id"]), values=(
                p["id"], p.get("nome", "—"), p.get("descricao", "—"),
                p.get("total_reservas", 0), f"€ {tot:.2f}", estado_txt
            ))

        self.desativar_botoes_selecao()

    def ao_selecionar_pagamento(self, event):
        selecionado = self.tabela.selection()
        if not selecionado: return

        p = next((item for item in self.lista_pagamentos_cache if str(item["id"]) == str(selecionado[0])), None)
        if not p: return

        self.pagamento_selecionado = p
        self.btn_editar.configure(state="normal")
        self.btn_remover.configure(state="normal")

        self.lbl_det_titulo.configure(text=f"Método de Pagamento: {p.get('nome')}")
        tot = float(p.get("total_faturado", 0))
        estado_txt = "Ativo" if p.get("ativo", 1) == 1 else "Inativo"

        self.lbl_col_dados.configure(text=(
            f"💳 DETALHES & VOLUME DE NEGÓCIO\n\n"
            f"• Nome: {p.get('nome', '—')}   |   Estado: {estado_txt}\n"
            f"• Descrição: {p.get('descricao', '—')}\n"
            f"• Total de Contratos Associados: {p.get('total_reservas', 0)}\n"
            f"• Faturação Acumulada: € {tot:.2f}"
        ))

    def desativar_botoes_selecao(self):
        self.btn_editar.configure(state="disabled")
        self.btn_remover.configure(state="disabled")
        self.lbl_det_titulo.configure(text="Ficha do Método de Pagamento")
        self.lbl_col_dados.configure(text="Selecione um método na tabela para visualizar o volume de faturação e detalhes.")
        self.pagamento_selecionado = None

    def abrir_modal_adicionar(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Adicionar Forma de Pagamento")
        modal.geometry("450x340")
        modal.grab_set()

        ctk.CTkLabel(modal, text="Nova Forma de Pagamento", font=ctk.CTkFont(size=17, weight="bold")).pack(pady=12)
        scroll = ctk.CTkFrame(modal, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        ctk.CTkLabel(scroll, text="Nome do Método:", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
        ent_nome = ctk.CTkEntry(scroll, height=34, font=ctk.CTkFont(size=12))
        ent_nome.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(scroll, text="Descrição / Observações:", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
        ent_desc = ctk.CTkEntry(scroll, height=34, font=ctk.CTkFont(size=12), placeholder_text="Ex: Cartão de crédito VISA/Mastercard")
        ent_desc.pack(fill="x", pady=(0, 10))

        def salvar():
            nome = ent_nome.get().strip()
            if not nome:
                messagebox.showerror("Erro", "O nome do método de pagamento é obrigatório.")
                return

            sucesso, msg = adicionar_forma_pagamento(nome, ent_desc.get().strip())
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                modal.destroy()
                self.carregar_dados_tabela()
            else:
                messagebox.showerror("Erro", msg)

        ctk.CTkButton(modal, text="Adicionar Método", fg_color="#10B981", hover_color="#059669", font=ctk.CTkFont(size=13, weight="bold"), height=38, command=salvar).pack(pady=10)

    def abrir_modal_editar(self):
        if not self.pagamento_selecionado: return
        p = self.pagamento_selecionado

        modal = ctk.CTkToplevel(self)
        modal.title(f"Editar Método #{p['id']}")
        modal.geometry("450x380")
        modal.grab_set()

        ctk.CTkLabel(modal, text=f"Editar Método #{p['id']}", font=ctk.CTkFont(size=17, weight="bold")).pack(pady=12)
        scroll = ctk.CTkFrame(modal, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        ctk.CTkLabel(scroll, text="Nome do Método:", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
        ent_nome = ctk.CTkEntry(scroll, height=34, font=ctk.CTkFont(size=12))
        ent_nome.insert(0, p.get("nome", ""))
        ent_nome.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(scroll, text="Descrição / Observações:", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
        ent_desc = ctk.CTkEntry(scroll, height=34, font=ctk.CTkFont(size=12))
        ent_desc.insert(0, p.get("descricao", ""))
        ent_desc.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(scroll, text="Estado:", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
        cb_ativo = ctk.CTkComboBox(scroll, values=["Ativo", "Inativo"], height=34, font=ctk.CTkFont(size=12))
        cb_ativo.set("Ativo" if p.get("ativo", 1) == 1 else "Inativo")
        cb_ativo.pack(fill="x", pady=(0, 10))

        def guardar():
            nome = ent_nome.get().strip()
            if not nome:
                messagebox.showerror("Erro", "O nome é obrigatório.")
                return

            sucesso, msg = atualizar_forma_pagamento(p["id"], nome, ent_desc.get().strip(), 1 if cb_ativo.get() == "Ativo" else 0)
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                modal.destroy()
                self.carregar_dados_tabela()
            else:
                messagebox.showerror("Erro", msg)

        ctk.CTkButton(modal, text="Guardar Alterações", fg_color="#2563EB", hover_color="#1D4ED8", font=ctk.CTkFont(size=13, weight="bold"), height=38, command=guardar).pack(pady=10)

    def acao_remover_pagamento(self):
        if not self.pagamento_selecionado: return
        p = self.pagamento_selecionado
        if messagebox.askyesno("Confirmação", f"Remover o método '{p.get('nome')}'?"):
            sucesso, msg = remover_forma_pagamento(p["id"])
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                self.carregar_dados_tabela()
            else:
                messagebox.showerror("Erro", msg)

    def acao_exportar_csv(self):
        if not self.lista_pagamentos_cache: return
        c = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="pagamentos.csv")
        if c:
            sucesso, msg = exportar_para_csv(self.lista_pagamentos_cache, c)
            messagebox.showinfo("Exportação", msg) if sucesso else messagebox.showerror("Erro", msg)

    def acao_exportar_excel(self):
        if not self.lista_pagamentos_cache: return
        c = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], initialfile="pagamentos.xlsx")
        if c:
            sucesso, msg = exportar_para_excel(self.lista_pagamentos_cache, c, titulo_folha="Pagamentos")
            messagebox.showinfo("Exportação", msg) if sucesso else messagebox.showerror("Erro", msg)