# Módulo: rentals_view.py
# Descrição: Gestão visual de contratos de aluguer e reservas do Luxury Wheels.
           # Gere listagem cronológica, filtros, criação de contratos, cálculo de acertos financeiros e remoção/cancelamento de registos.

from datetime import datetime, date
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog

from database.queries import (
    listar_reservas,
    criar_reserva,
    concluir_reserva,
    cancelar_reserva,
    remover_reserva,
    listar_veiculos,
    listar_clientes,
    listar_formas_pagamento
)
from services.export_service import exportar_para_csv, exportar_para_excel
from utils.table_sort import configurar_ordenacao_treeview


class PainelReservas(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10, fg_color="transparent")
        self.parent = parent
        self.reserva_selecionada = None
        self.lista_reservas_cache = []
        self.painel_filtros_visivel = False

        self.configurar_estilo_tabela()
        self.criar_barra_superior()
        self.criar_gaveta_filtros()
        self.criar_area_conteudo()
        self.carregar_dados_tabela()

    def configurar_estilo_tabela(self):
        # Configura fontes amplas (11px) e linhas espaçadas (32px) para a tabela de reservas.
        estilo = ttk.Style()
        estilo.theme_use("clam")

        estilo.configure(
            "Rentals.Treeview.Heading",
            background="#1F2937",
            foreground="#F9FAFB",
            font=("Arial", 11, "bold"),
            relief="flat",
            padding=8
        )
        estilo.map("Rentals.Treeview.Heading", background=[("active", "#374151")])

        estilo.configure(
            "Rentals.Treeview",
            background="#111827",
            foreground="#E5E7EB",
            fieldbackground="#111827",
            rowheight=32,
            font=("Arial", 11),
            borderwidth=0
        )
        estilo.map(
            "Rentals.Treeview",
            background=[("selected", "#1E3A8A")],
            foreground=[("selected", "#FFFFFF")]
        )

    def criar_barra_superior(self):
        # Cria a barra superior com pesquisa, botão de novo contrato e exportações.
        self.topo_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.topo_frame.pack(fill="x", padx=15, pady=(12, 6))

        ctk.CTkLabel(self.topo_frame, text="🔍 Pesquisa:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0, 6))
        self.ent_pesquisa = ctk.CTkEntry(
            self.topo_frame,
            placeholder_text="Matrícula ou Nome do Cliente...",
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
            self.topo_frame, text="Limpar", width=70, height=34,
            font=ctk.CTkFont(size=12), fg_color="gray40", hover_color="gray30",
            command=self.limpar_todos_filtros
        )
        btn_limpar.pack(side="left")

        btn_exp_excel = ctk.CTkButton(
            self.topo_frame, text="📥 Exportar Excel", fg_color="#27AE60", hover_color="#1E8449",
            text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"), width=125, height=34,
            command=self.acao_exportar_excel
        )
        btn_exp_excel.pack(side="right", padx=4)

        btn_exp_csv = ctk.CTkButton(
            self.topo_frame, text="📥 Exportar CSV", fg_color="#2980B9", hover_color="#1F618D",
            text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"), width=115, height=34,
            command=self.acao_exportar_csv
        )
        btn_exp_csv.pack(side="right", padx=4)

    def criar_gaveta_filtros(self):
        # Cria o painel retrátil de filtros por estado do contrato.
        self.frame_gaveta = ctk.CTkFrame(self, fg_color="#161B26", corner_radius=8, border_width=1, border_color="#283244")

        inner = ctk.CTkFrame(self.frame_gaveta, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        def criar_filtro_combo(rotulo, valores):
            f = ctk.CTkFrame(inner, fg_color="transparent")
            f.pack(side="left", padx=6)
            ctk.CTkLabel(f, text=rotulo, font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(anchor="w", pady=(0, 2))
            cb = ctk.CTkComboBox(f, values=valores, width=160, height=32, font=ctk.CTkFont(size=12), command=lambda _: self.carregar_dados_tabela())
            cb.set(valores[0])
            cb.pack()
            return cb

        self.cb_estado_filtro = criar_filtro_combo("Estado do Contrato:", ["Todos", "Ativa", "Concluída", "Cancelada"])

        btn_fechar = ctk.CTkButton(
            inner, text="✕ Fechar", width=80, height=32, font=ctk.CTkFont(size=11),
            fg_color="transparent", border_width=1, border_color="#4B5563", hover_color="#1F2937",
            command=self.alternar_gaveta_filtros
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
        self.cb_estado_filtro.set("Todos")
        self.carregar_dados_tabela()

    def criar_area_conteudo(self):
        # Cria a tabela principal de reservas e o painel de operações inferior.
        self.meio_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.meio_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        frame_tabela = ctk.CTkFrame(self.meio_frame, fg_color="#111827", corner_radius=8)
        frame_tabela.pack(fill="both", expand=True, pady=(0, 10))

        colunas = ("ID", "Alerta", "Cliente", "Matrícula", "Viatura", "Início", "Fim Previsto", "Valor Total", "Estado")
        self.tabela = ttk.Treeview(
            frame_tabela, columns=colunas, show="headings",
            style="Rentals.Treeview", selectmode="browse", height=9
        )

        larguras = [40, 65, 180, 100, 160, 100, 100, 105, 100]
        for col, larg in zip(colunas, larguras):
            self.tabela.heading(col, text=col)
            self.tabela.column(col, width=larg, anchor="center")

        configurar_ordenacao_treeview(self.tabela)

        scrollbar_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scrollbar_y.set)
        self.tabela.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar_y.pack(side="right", fill="y", pady=5)

        self.tabela.bind("<<TreeviewSelect>>", self.ao_selecionar_reserva)

        # Painel Inferior de Ações com altura ajustada para albergar confortavelmente os 4 botões
        frame_inf = ctk.CTkFrame(self.meio_frame, fg_color="#111827", corner_radius=8, border_width=1, border_color="#1F2937", height=165)
        frame_inf.pack(fill="x", side="bottom")
        frame_inf.pack_propagate(False)

        corpo_inf = ctk.CTkFrame(frame_inf, fg_color="transparent")
        corpo_inf.pack(fill="both", expand=True, padx=16, pady=12)

        self.lbl_detalhes_reserva = ctk.CTkLabel(
            corpo_inf,
            text="Selecione um contrato na tabela para visualizar detalhes e gerir a conclusão, cancelamento ou remoção.",
            justify="left", anchor="nw", font=ctk.CTkFont(size=12)
        )
        self.lbl_detalhes_reserva.pack(side="left", fill="both", expand=True, padx=(0, 15))

        self.frame_botoes_reserva = ctk.CTkFrame(corpo_inf, fg_color="transparent", width=200)
        self.frame_botoes_reserva.pack(side="right", fill="y")
        self.criar_botoes_operacao()

    def criar_botoes_operacao(self):
        ctk.CTkButton(
            self.frame_botoes_reserva, text="➕ Nova Reserva",
            fg_color="#10B981", hover_color="#059669", text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"), height=30, command=self.abrir_modal_criar_reserva
        ).pack(fill="x", pady=2)

        self.btn_concluir = ctk.CTkButton(
            self.frame_botoes_reserva, text="✅ Concluir Reserva",
            fg_color="#2563EB", hover_color="#1D4ED8", text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"), height=30, state="disabled",
            command=self.acao_concluir_reserva
        )
        self.btn_concluir.pack(fill="x", pady=2)

        self.btn_cancelar = ctk.CTkButton(
            self.frame_botoes_reserva, text="🚫 Cancelar Reserva",
            fg_color="#D97706", hover_color="#B45309", text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"), height=30, state="disabled",
            command=self.acao_cancelar_reserva
        )
        self.btn_cancelar.pack(fill="x", pady=2)

        self.btn_remover = ctk.CTkButton(
            self.frame_botoes_reserva, text="🗑️ Apagar Registo",
            fg_color="#C0392B", hover_color="#922B21", text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"), height=30, state="disabled",
            command=self.acao_remover_reserva
        )
        self.btn_remover.pack(fill="x", pady=2)

    def carregar_dados_tabela(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        termo = self.ent_pesquisa.get().strip() if hasattr(self, "ent_pesquisa") else ""
        estado_sel = self.cb_estado_filtro.get() if hasattr(self, "cb_estado_filtro") else "Todos"

        self.lista_reservas_cache = listar_reservas(
            termo_pesquisa=termo,
            filtro_estado=None if estado_sel == "Todos" else estado_sel
        )

        hoje = date.today()

        for r in self.lista_reservas_cache:
            r_id = r["id"]
            estado = r.get("estado_reserva", "Ativa")
            dt_fim_str = r.get("data_fim_prevista", "")

            alerta = "—"
            if str(estado).lower() == "ativa":
                try:
                    dt_fim = datetime.strptime(dt_fim_str, "%Y-%m-%d").date()
                    if dt_fim < hoje:
                        alerta = "❗ Atrasado"
                    elif dt_fim == hoje:
                        alerta = "⚠️ Termina Hoje"
                    else:
                        alerta = "🟢 No Prazo"
                except Exception:
                    pass

            self.tabela.insert("", "end", iid=str(r_id), values=(
                r["id"], alerta, r.get("nome_cliente", "—"),
                r.get("matricula", "—"), f"{r.get('marca', '')} {r.get('modelo', '')}",
                r.get("data_inicio", ""), dt_fim_str, f"€ {float(r.get('valor_total', 0)):.2f}", estado
            ))

        self.desativar_botoes_selecao()

    def ao_selecionar_reserva(self, event):
        selecionado = self.tabela.selection()
        if not selecionado: return

        r = next((item for item in self.lista_reservas_cache if str(item["id"]) == str(selecionado[0])), None)
        if not r: return

        self.reserva_selecionada = r
        estado = r.get("estado_reserva", "Ativa")

        if str(estado).lower() == "ativa":
            self.btn_concluir.configure(state="normal")
            self.btn_cancelar.configure(state="normal")
        else:
            self.btn_concluir.configure(state="disabled")
            self.btn_cancelar.configure(state="disabled")

        self.btn_remover.configure(state="normal")

        self.lbl_detalhes_reserva.configure(text=(
            f"📋 CONTRATO DE ALUGUER #{r['id']} ({estado})\n\n"
            f"• Cliente: {r.get('nome_cliente', '—')}   |   Contacto: {r.get('telefone_cliente', '—')}\n"
            f"• Viatura: {r.get('marca', '')} {r.get('modelo', '')} [{r.get('matricula', '—')}]\n"
            f"• Período: {r.get('data_inicio', '')} até {r.get('data_fim_prevista', '')}   |   Tarifa: € {float(r.get('valor_diario_aplicado', 0)):.2f}/dia\n"
            f"• Faturação Total: € {float(r.get('valor_total', 0)):.2f}   |   Obs: {r.get('observacoes', 'Nenhuma')}"
        ))

    def desativar_botoes_selecao(self):
        self.btn_concluir.configure(state="disabled")
        self.btn_cancelar.configure(state="disabled")
        self.btn_remover.configure(state="disabled")
        self.reserva_selecionada = None
        self.lbl_detalhes_reserva.configure(text="Selecione um contrato na tabela para visualizar detalhes e gerir a conclusão ou cancelamento.")

    def abrir_modal_criar_reserva(self):
        # Abre o modal avançado para registar um novo contrato de aluguer.
        veiculos_disp = [v for v in listar_veiculos() if str(v.get("estado", "")).lower() in ("disponível", "disponivel")]
        clientes_cad = listar_clientes()
        formas_pag = listar_formas_pagamento()

        if not veiculos_disp:
            messagebox.showwarning("Aviso", "Não existem viaturas disponíveis no momento.")
            return
        if not clientes_cad:
            messagebox.showwarning("Aviso", "Não existem clientes registados. Adicione um cliente primeiro.")
            return

        modal = ctk.CTkToplevel(self)
        modal.title("Novo Contrato de Aluguer")
        modal.geometry("520x640")
        modal.resizable(False, False)
        modal.grab_set()

        ctk.CTkLabel(modal, text="Registar Novo Contrato", font=ctk.CTkFont(size=17, weight="bold")).pack(pady=(16, 4))

        scroll = ctk.CTkScrollableFrame(modal, width=460, height=450)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        # Seleção de Veículo
        ctk.CTkLabel(scroll, text="Selecionar Viatura:", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
        dict_veiculos = {f"{v['marca']} {v['modelo']} ({v['matricula']} — €{v['preco_diario']}/dia)": v for v in veiculos_disp}
        cb_veiculo = ctk.CTkComboBox(scroll, values=list(dict_veiculos.keys()), height=34, font=ctk.CTkFont(size=12))
        cb_veiculo.set(list(dict_veiculos.keys())[0])
        cb_veiculo.pack(fill="x", pady=(0, 8))

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

        # Pagamentos
        ctk.CTkLabel(scroll, text="Forma de Pagamento:", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
        dict_pag = {f["nome"]: f["id"] for f in formas_pag}
        cb_pag = ctk.CTkComboBox(scroll, values=list(dict_pag.keys()), height=34, font=ctk.CTkFont(size=12))
        cb_pag.set(list(dict_pag.keys())[0] if dict_pag else "Numerário")
        cb_pag.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(scroll, text="Modalidade (se Dinheiro):", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
        cb_modalidade = ctk.CTkComboBox(scroll, values=["Total", "Sinal (20%)", "Não Pago"], height=34, font=ctk.CTkFont(size=12))
        cb_modalidade.set("Total")
        cb_modalidade.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(scroll, text="Observações:", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(6, 2))
        ent_obs = ctk.CTkEntry(scroll, height=34, font=ctk.CTkFont(size=12), placeholder_text="Notas adicionais...")
        ent_obs.pack(fill="x", pady=(0, 6))

        def confirmar_criacao():
            try:
                dt1 = datetime.strptime(ent_ini.get().strip(), "%Y-%m-%d").date()
                dt2 = datetime.strptime(ent_fim.get().strip(), "%Y-%m-%d").date()
                if dt2 < dt1:
                    messagebox.showerror("Erro", "A data de fim não pode ser anterior à data de início.")
                    return
            except ValueError:
                messagebox.showerror("Erro", "Formato de data inválido (use AAAA-MM-DD).")
                return

            v_obj = dict_veiculos[cb_veiculo.get()]
            mod_escolhida = cb_modalidade.get().split()[0]

            sucesso, msg, _ = criar_reserva(
                veiculo_id=v_obj["id"],
                cliente_id=dict_clientes[cb_cli.get()],
                forma_pag_id=dict_pag[cb_pag.get()],
                data_inicio=ent_ini.get().strip(),
                data_fim=ent_fim.get().strip(),
                km_inicial=v_obj.get("quilometragem", 0),
                valor_dia=v_obj.get("preco_diario", 50.0),
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
            modal, text="Criar Contrato", fg_color="#10B981", hover_color="#059669",
            font=ctk.CTkFont(size=13, weight="bold"), height=38, command=confirmar_criacao
        ).pack(pady=12)

    def acao_concluir_reserva(self):
        # Abre o modal interativo para devolução da viatura e cálculo de acertos financeiros.
        if not self.reserva_selecionada: return
        r = self.reserva_selecionada

        modal = ctk.CTkToplevel(self)
        modal.title(f"Concluir Contrato #{r['id']}")
        modal.geometry("440x400")
        modal.grab_set()

        ctk.CTkLabel(modal, text=f"Concluir Contrato #{r['id']}", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(16, 10))

        form = ctk.CTkFrame(modal, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24, pady=5)

        ctk.CTkLabel(form, text="Quilometragem Final:", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(4, 2))
        ent_km = ctk.CTkEntry(form, height=34, font=ctk.CTkFont(size=12))
        ent_km.insert(0, str(r.get("km_inicial", 0)))
        ent_km.pack(fill="x", pady=(0, 8))

        def submeter_conclusao():
            try:
                km_f = int(ent_km.get().strip())
            except ValueError:
                messagebox.showerror("Erro", "Quilometragem final inválida.")
                return

            sucesso, msg = concluir_reserva(
                reserva_id=r["id"],
                km_final=km_f
            )

            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                modal.destroy()
                self.carregar_dados_tabela()
            else:
                messagebox.showerror("Erro", msg)

        ctk.CTkButton(
            modal, text="Confirmar Conclusão", fg_color="#2563EB", hover_color="#1D4ED8",
            font=ctk.CTkFont(size=13, weight="bold"), height=38, command=submeter_conclusao
        ).pack(pady=16)

    def acao_cancelar_reserva(self):
        if not self.reserva_selecionada: return
        if messagebox.askyesno("Confirmação", "Tem a certeza que deseja cancelar esta reserva? A viatura voltará a ficar disponível."):
            sucesso, msg = cancelar_reserva(self.reserva_selecionada["id"])
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                self.carregar_dados_tabela()
            else:
                messagebox.showerror("Erro", msg)

    def acao_remover_reserva(self):
        # Elimina definitivamente a reserva selecionada da base de dados.
        if not self.reserva_selecionada: return
        if messagebox.askyesno("Confirmação", "Tem a certeza que deseja apagar este registo por completo da base de dados?"):
            sucesso, msg = remover_reserva(self.reserva_selecionada["id"])
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                self.carregar_dados_tabela()
            else:
                messagebox.showerror("Erro", msg)

    def acao_exportar_csv(self):
        dados = self.lista_reservas_cache
        c = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="reservas.csv")
        if c:
            sucesso, msg = exportar_para_csv(dados, c)
            messagebox.showinfo("Exportação", msg) if sucesso else messagebox.showerror("Erro", msg)

    def acao_exportar_excel(self):
        dados = self.lista_reservas_cache
        c = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], initialfile="reservas.xlsx")
        if c:
            sucesso, msg = exportar_para_excel(dados, c, titulo_folha="Reservas")
            messagebox.showinfo("Exportação", msg) if sucesso else messagebox.showerror("Erro", msg)