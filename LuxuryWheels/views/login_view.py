# Módulo: login_view.py
# Descrição: Interface gráfica de autenticação do Luxury Wheels.
           # Gere o início de sessão, criação de contas e transição para o painel principal da aplicação.

import hashlib
import customtkinter as ctk
from tkinter import messagebox

from database.queries import autenticar_utilizador, registar_utilizador
from views.dashboard_view import JanelaPrincipal


class JanelaLogin(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Luxury Wheels - Autenticação")
        self.geometry("450x520")
        self.resizable(False, False)
        self.configure(fg_color="#0F131A")

        # Centralizar a janela no ecrã
        self.center_window(450, 520)

        self.criar_elementos_interface()

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

    def criar_elementos_interface(self):
        # Contentor principal central
        frame_principal = ctk.CTkFrame(self, fg_color="#181E29", corner_radius=12, border_width=1, border_color="#283244")
        frame_principal.pack(fill="both", expand=True, padx=30, pady=30)

        # Cabeçalho / Título da Marca
        ctk.CTkLabel(
            frame_principal,
            text="LUXURY WHEELS",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#F8FAFC"
        ).pack(pady=(35, 5))

        ctk.CTkLabel(
            frame_principal,
            text="Sistema de Gestão de Frota",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        ).pack(pady=(0, 25))

        # Campo de Username
        ctk.CTkLabel(
            frame_principal,
            text="Utilizador:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#E2E8F0",
            anchor="w"
        ).pack(fill="x", padx=35, pady=(0, 4))

        self.ent_username = ctk.CTkEntry(
            frame_principal,
            placeholder_text="Insira o seu utilizador",
            height=38,
            font=ctk.CTkFont(size=12)
        )
        self.ent_username.pack(fill="x", padx=35, pady=(0, 15))
        self.ent_username.insert(0, "admin")  # Preenchimento rápido auxiliar

        # Campo de Password
        ctk.CTkLabel(
            frame_principal,
            text="Palavra-passe:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#E2E8F0",
            anchor="w"
        ).pack(fill="x", padx=35, pady=(0, 4))

        self.ent_password = ctk.CTkEntry(
            frame_principal,
            placeholder_text="Insira a palavra-passe",
            show="*",
            height=38,
            font=ctk.CTkFont(size=12)
        )
        self.ent_password.pack(fill="x", padx=35, pady=(0, 25))
        self.ent_password.insert(0, "admin123")  # Preenchimento rápido auxiliar

        # Submeter formulário ao pressionar 'Enter'
        self.ent_password.bind("<Return>", lambda _: self.tentar_login())

        # Botão de Entrada (Login)
        btn_login = ctk.CTkButton(
            frame_principal,
            text="Iniciar Sessão",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=42,
            command=self.tentar_login
        )
        btn_login.pack(fill="x", padx=35, pady=(0, 10))

        # Botão para abrir modal de Registo de Novo Operador
        btn_registar = ctk.CTkButton(
            frame_principal,
            text="Registar Novo Utilizador",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color="#242E3F",
            text_color="#94A3B8",
            height=32,
            command=self.abrir_modal_registo
        )
        btn_registar.pack(fill="x", padx=35)

    def tentar_login(self):
        username = self.ent_username.get().strip()
        password = self.ent_password.get().strip()

        if not username or not password:
            messagebox.showwarning("Aviso", "Por favor, preencha o utilizador e a palavra-passe.")
            return

        # Gerar hash SHA-256 da password inserida
        pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

        # Validar credenciais na base de dados
        utilizador = autenticar_utilizador(username, pwd_hash)

        if utilizador:
            # Fechar janela de login e abrir o painel principal da aplicação
            self.destroy()
            app = JanelaPrincipal(utilizador)
            app.mainloop()
        else:
            messagebox.showerror("Erro de Autenticação", "Utilizador ou palavra-passe incorretos.")

    def abrir_modal_registo(self):
        # Abre uma janela secundária para criação de novos operadores protegida por código de empresa.
        modal = ctk.CTkToplevel(self)
        modal.title("Registar Novo Utilizador")
        modal.geometry("400x480")
        modal.resizable(False, False)
        modal.grab_set()

        ctk.CTkLabel(
            modal,
            text="Criar Nova Conta",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 10))

        form_frame = ctk.CTkFrame(modal, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=25, pady=5)

        def criar_campo(rotulo, senha=False):
            ctk.CTkLabel(form_frame, text=rotulo, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", pady=(4, 2))
            ent = ctk.CTkEntry(form_frame, height=34, font=ctk.CTkFont(size=12), show="*" if senha else "")
            ent.pack(fill="x", pady=(0, 6))
            return ent

        ent_user = criar_campo("Nome de Utilizador:")
        ent_nome = criar_campo("Nome Completo:")
        ent_pwd1 = criar_campo("Palavra-passe:", senha=True)
        ent_pwd2 = criar_campo("Confirmar Palavra-passe:", senha=True)
        ent_codigo = criar_campo("Código de Empresa / Operador:", senha=True)

        def submeter_registo():
            u = ent_user.get().strip()
            nome = ent_nome.get().strip()
            p1 = ent_pwd1.get().strip()
            p2 = ent_pwd2.get().strip()
            codigo = ent_codigo.get().strip()

            # Validação do Código de Empresa secreto
            CODIGO_EMPRESA_SECRETO = "LUXURY2026"
            if codigo != CODIGO_EMPRESA_SECRETO:
                messagebox.showerror("Acesso Negado", "O Código de Empresa / Operador está incorreto.")
                return

            if not u or not p1:
                messagebox.showerror("Erro", "O utilizador e a palavra-passe são obrigatórios.")
                return

            if p1 != p2:
                messagebox.showerror("Erro", "As palavras-passe não coincidem.")
                return

            pwd_hash = hashlib.sha256(p1.encode("utf-8")).hexdigest()
            sucesso, msg = registar_utilizador(username=u, password_hash=pwd_hash, nome_completo=nome)

            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                modal.destroy()
            else:
                messagebox.showerror("Erro", msg)

        ctk.CTkButton(
            modal,
            text="Concluir Registo",
            fg_color="#10B981",
            hover_color="#059669",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            command=submeter_registo
        ).pack(pady=15)