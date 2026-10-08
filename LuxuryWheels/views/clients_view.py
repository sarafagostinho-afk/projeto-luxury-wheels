# Módulo: clients_view.py
# Descrição: Gestão visual de clientes do Luxury Wheels.
           # Gere listagem, pesquisa por nome/NIF/telefone, ordenação interativa por colunas, fichas detalhadas, etc..

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog

from database.queries import (
    listar_clientes,
    adicionar_cliente,
    atualizar_cliente,
    remover_cliente
)
from services.export_service import exportar_para_csv, exportar_para_excel
from utils.table_sort import configurar_ordenacao_treeview


class PainelClientes(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10, fg_color="transparent")
        self.parent = parent
        self.cliente_selecionado = None
        self.lista_clientes_cache = []

        self.configurar_estilo_tabela()
        self.criar_barra_superior()
        self.criar_area_conteudo()
        self.carregar_dados_tabela()

    def configurar_estilo_tabela(self):
        # Configura fontes amplas (11px) e linhas espaçadas (32px) para a tabela de clientes.
        estilo = ttk.Style()
        estilo.theme_use("clam")

        estilo.configure(
            "Clients.Treeview.Heading",
            background="#1F2937",
            foreground="#F9FAFB",
            font=("Arial", 11, "bold"),
            relief="flat",
            padding=8
        )
        estilo.map("Clients.Treeview.Heading", background=[("active", "#374151")])

        estilo.configure(
            "Clients.Treeview",
            background="#111827",
            foreground="#E2E8F0",
            fieldbackground="#111827",
            rowheight=32,
            font=("Arial", 11),
            borderwidth=0
        )
        estilo.map(
            "Clients.Treeview",
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
            placeholder_text="Nome, NIF ou Telefone...",
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

        colunas = ("ID", "Nome Completo", "NIF", "Nº Carta Condução", "Telefone", "Email", "Morada")
        self.tabela = ttk.Treeview(
            frame_tabela, columns=colunas, show="headings",
            style="Clients.Treeview", selectmode="browse", height=8
        )

        larguras = [50, 200, 110, 140, 120, 180, 220]
        for col, larg in zip(colunas, larguras):
            self.tabela.heading(col, text=col)
            self.tabela.column(col, width=larg, anchor="center")

        configurar_ordenacao_treeview(self.tabela)

        scrollbar_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scrollbar_y.set)
        self.tabela.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar_y.pack(side="right", fill="y", pady=5)

        self.tabela.bind("<<TreeviewSelect>>", self.ao_selecionar_cliente)

        # Painel Inferior de Ficha
        self.frame_detalhes = ctk.CTkFrame(meio_frame, corner_radius=8, height=180)
        self.frame_detalhes.pack(fill="x", side="bottom")

        topo_det = ctk.CTkFrame(self.frame_detalhes, fg_color="transparent")
        topo_det.pack(fill="x", padx=16, pady=(10, 4))

        self.lbl_det_titulo = ctk.CTkLabel(topo_det, text="Ficha do Cliente", font=ctk.CTkFont(size=15, weight="bold"))
        self.lbl_det_titulo.pack(side="left")

        corpo_det = ctk.CTkFrame(self.frame_detalhes, fg_color="transparent")
        corpo_det.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self.lbl_col_dados = ctk.CTkLabel(corpo_det, text="Selecione um cliente na tabela para visualizar os detalhes completos.", justify="left", anchor="nw", font=ctk.CTkFont(size=13))
        self.lbl_col_dados.pack(side="left", fill="both", expand=True, padx=(0, 12))

        self.frame_botoes = ctk.CTkFrame(corpo_det, fg_color="transparent", width=190)
        self.frame_botoes.pack(side="right", fill="y")
        self.criar_botoes_operacao()

    def criar_botoes_operacao(self):
        ctk.CTkButton(self.frame_botoes, text="➕ Novo Cliente", font=ctk.CTkFont(size=12, weight="bold"), height=32, command=self.abrir_modal_adicionar).pack(fill="x", pady=3)

        self.btn_editar = ctk.CTkButton(self.frame_botoes, text="✏️ Editar Cliente", fg_color="#2563EB", hover_color="#1D4ED8", text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"), height=32, state="disabled", command=self.abrir_modal_editar)
        self.btn_editar.pack(fill="x", pady=3)

        self.btn_remover = ctk.CTkButton(self.frame_botoes, text="🗑️ Remover", fg_color="#C0392B", hover_color="#922B21", text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"), height=32, state="disabled", command=self.acao_remover_cliente)
        self.btn_remover.pack(fill="x", pady=3)

    def carregar_dados_tabela(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        termo = self.ent_pesquisa.get().strip() if hasattr(self, "ent_pesquisa") else ""
        self.lista_clientes_cache = listar_clientes(termo_pesquisa=termo)

        for c in self.lista_clientes_cache:
            self.tabela.insert("", "end", iid=str(c["id"]), values=(
                c["id"], c.get("nome_completo", "—"), c.get("nif", "—"),
                c.get("numero_carta", "—"), c.get("telefone", "—"),
                c.get("email", "—"), c.get("morada", "—")
            ))

        self.desativar_botoes_selecao()

    def ao_selecionar_cliente(self, event):
        selecionado = self.tabela.selection()
        if not selecionado: return

        c = next((item for item in self.lista_clientes_cache if str(item["id"]) == str(selecionado[0])), None)
        if not c: return

        self.cliente_selecionado = c
        self.btn_editar.configure(state="normal")
        self.btn_remover.configure(state="normal")

        self.lbl_det_titulo.configure(text=f"Ficha de Cliente: {c.get('nome_completo')}")
        self.lbl_col_dados.configure(text=(
            f"👤 DADOS PESSOAIS & CONTACTO\n\n"
            f"• Nome Completo: {c.get('nome_completo', '—')}\n"
            f"• NIF: {c.get('nif', '—')}   |   Carta de Condução: {c.get('numero_carta', '—')}\n"
            f"• Telefone: {c.get('telefone', '—')}   |   Email: {c.get('email', '—')}\n"
            f"• Morada: {c.get('morada', '—')}"
        ))

    def desativar_botoes_selecao(self):
        self.btn_editar.configure(state="disabled")
        self.btn_remover.configure(state="disabled")
        self.lbl_det_titulo.configure(text="Ficha do Cliente")
        self.lbl_col_dados.configure(text="Selecione um cliente na tabela para visualizar os detalhes completos.")
        self.cliente_selecionado = None

    def abrir_modal_adicionar(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Registar Novo Cliente")
        modal.geometry("480x500")
        modal.grab_set()

        ctk.CTkLabel(modal, text="Novo Cliente", font=ctk.CTkFont(size=17, weight="bold")).pack(pady=12)
        scroll = ctk.CTkScrollableFrame(modal, width=420, height=360)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        def criar_campo(rotulo):
            ctk.CTkLabel(scroll, text=rotulo, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
            ent = ctk.CTkEntry(scroll, height=34, font=ctk.CTkFont(size=12))
            ent.pack(fill="x", pady=(0, 4))
            return ent

        ent_nome, ent_nif, ent_carta, ent_tel, ent_email, ent_morada = (
            criar_campo("Nome Completo:"), criar_campo("NIF:"),
            criar_campo("Número da Carta de Condução:"), criar_campo("Telefone:"),
            criar_campo("Email:"), criar_campo("Morada:")
        )

        def salvar():
            nome, nif = ent_nome.get().strip(), ent_nif.get().strip()
            if not (nome and nif):
                messagebox.showerror("Erro", "O Nome e o NIF são obrigatórios.")
                return

            sucesso, msg = adicionar_cliente(nome, nif, ent_carta.get().strip(), ent_tel.get().strip(), ent_email.get().strip(), ent_morada.get().strip())
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                modal.destroy()
                self.carregar_dados_tabela()
            else:
                messagebox.showerror("Erro", msg)

        ctk.CTkButton(modal, text="Registar Cliente", fg_color="#10B981", hover_color="#059669", font=ctk.CTkFont(size=13, weight="bold"), height=38, command=salvar).pack(pady=14)

    def abrir_modal_editar(self):
        if not self.cliente_selecionado: return
        c = self.cliente_selecionado

        modal = ctk.CTkToplevel(self)
        modal.title(f"Editar Cliente #{c['id']}")
        modal.geometry("480x500")
        modal.grab_set()

        ctk.CTkLabel(modal, text=f"Editar Cliente #{c['id']}", font=ctk.CTkFont(size=17, weight="bold")).pack(pady=12)
        scroll = ctk.CTkScrollableFrame(modal, width=420, height=360)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        def criar_campo(rotulo, val=""):
            ctk.CTkLabel(scroll, text=rotulo, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
            ent = ctk.CTkEntry(scroll, height=34, font=ctk.CTkFont(size=12))
            if val: ent.insert(0, str(val))
            ent.pack(fill="x", pady=(0, 4))
            return ent

        ent_nome = criar_campo("Nome Completo:", c.get("nome_completo", ""))
        ent_nif = criar_campo("NIF:", c.get("nif", ""))
        ent_carta = criar_campo("Número da Carta de Condução:", c.get("numero_carta", ""))
        ent_tel = criar_campo("Telefone:", c.get("telefone", ""))
        ent_email = criar_campo("Email:", c.get("email", ""))
        ent_morada = criar_campo("Morada:", c.get("morada", ""))

        def guardar():
            nome, nif = ent_nome.get().strip(), ent_nif.get().strip()
            if not (nome and nif):
                messagebox.showerror("Erro", "O Nome e o NIF são obrigatórios.")
                return

            sucesso, msg = atualizar_cliente(c["id"], nome, nif, ent_carta.get().strip(), ent_tel.get().strip(), ent_email.get().strip(), ent_morada.get().strip())
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                modal.destroy()
                self.carregar_dados_tabela()
            else:
                messagebox.showerror("Erro", msg)

        ctk.CTkButton(modal, text="Guardar Alterações", fg_color="#2563EB", hover_color="#1D4ED8", font=ctk.CTkFont(size=13, weight="bold"), height=38, command=guardar).pack(pady=14)

    def acao_remover_cliente(self):
        if not self.cliente_selecionado: return
        c = self.cliente_selecionado
        if messagebox.askyesno("Confirmação", f"Remover o cliente {c.get('nome_completo')}?"):
            sucesso, msg = remover_cliente(c["id"])
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                self.carregar_dados_tabela()
            else:
                messagebox.showerror("Erro", msg)

    def acao_exportar_csv(self):
        if not self.lista_clientes_cache: return
        c = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="clientes.csv")
        if c:
            sucesso, msg = exportar_para_csv(self.lista_clientes_cache, c)
            messagebox.showinfo("Exportação", msg) if sucesso else messagebox.showerror("Erro", msg)

    def acao_exportar_excel(self):
        if not self.lista_clientes_cache: return
        c = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], initialfile="clientes.xlsx")
        if c:
            sucesso, msg = exportar_para_excel(self.lista_clientes_cache, c, titulo_folha="Clientes")
            messagebox.showinfo("Exportação", msg) if sucesso else messagebox.showerror("Erro", msg)