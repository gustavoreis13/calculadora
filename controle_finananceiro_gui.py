import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3
import datetime
from functools import partial
from calendar import month_name, monthrange # monthrange para ajudar com datas

# --- LÓGICA DO BANCO DE DADOS (Backend) ---
NOME_BANCO_DADOS = 'controle_financeiro.db'

def conectar_bd():
    conn = sqlite3.connect(NOME_BANCO_DADOS)
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor()

def inicializar_banco_de_dados():
    # ... (código inalterado)
    conn, cursor = conectar_bd()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes_tb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            categoria TEXT,
            data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def buscar_transacoes_db(ano=None, mes=None):
    # ... (código inalterado)
    conn, cursor = conectar_bd()
    try:
        query = "SELECT id, tipo, descricao, valor, categoria, data_registro FROM transacoes_tb"
        params = []
        conditions = []
        if ano:
            conditions.append("strftime('%Y', data_registro) = ?")
            params.append(str(ano))
        if mes:
            mes_formatado = f"{int(mes):02d}"
            conditions.append("strftime('%m', data_registro) = ?")
            params.append(mes_formatado)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY data_registro DESC, id DESC"
        cursor.execute(query, params)
        linhas_db = cursor.fetchall()
        return [dict(linha) for linha in linhas_db]
    except sqlite3.Error as e: raise e
    finally: conn.close()

def calcular_saldo_db(ano=None, mes=None):
    # ... (código inalterado)
    total_ganhos, total_despesas = 0.0, 0.0
    conn, cursor = conectar_bd()
    try:
        query = "SELECT tipo, valor FROM transacoes_tb"
        params = []
        conditions = []
        if ano:
            conditions.append("strftime('%Y', data_registro) = ?")
            params.append(str(ano))
        if mes:
            mes_formatado = f"{int(mes):02d}"
            conditions.append("strftime('%m', data_registro) = ?")
            params.append(mes_formatado)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        cursor.execute(query, params)
        for linha in cursor.fetchall():
            transacao = dict(linha)
            if transacao['tipo'] == 'ganho': total_ganhos += transacao['valor']
            elif transacao['tipo'] == 'despesa': total_despesas += transacao['valor']
        return total_ganhos, total_despesas, total_ganhos - total_despesas
    except sqlite3.Error as e: raise e
    finally: conn.close()

def buscar_anos_disponiveis_db():
    # ... (código inalterado)
    conn, cursor = conectar_bd()
    try:
        cursor.execute("SELECT DISTINCT strftime('%Y', data_registro) as ano FROM transacoes_tb ORDER BY ano DESC")
        anos = [row['ano'] for row in cursor.fetchall() if row['ano'] is not None]
        return anos
    except sqlite3.Error as e: raise e
    finally: conn.close()


def adicionar_ganho_db(descricao, valor):
    # ... (código inalterado)
    conn, cursor = conectar_bd()
    try:
        cursor.execute("INSERT INTO transacoes_tb (tipo, descricao, valor, categoria, data_registro) VALUES (?, ?, ?, ?, ?)",
                       ('ganho', descricao, valor, None, datetime.datetime.now().isoformat()))
        conn.commit(); return True
    except sqlite3.Error as e: conn.rollback(); raise e
    finally: conn.close()


def adicionar_despesa_db(descricao, valor, categoria, data_registro_iso=None): # Modificado
    """Adiciona uma nova despesa, opcionalmente com data específica."""
    conn, cursor = conectar_bd()
    if data_registro_iso is None:
        data_registro_iso = datetime.datetime.now().isoformat()
    try:
        cursor.execute('''
            INSERT INTO transacoes_tb (tipo, descricao, valor, categoria, data_registro)
            VALUES (?, ?, ?, ?, ?)
        ''', ('despesa', descricao, valor, categoria, data_registro_iso))
        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        raise e # Propaga o erro para ser tratado pela GUI
    finally:
        conn.close()

def _buscar_transacao_por_id_db(id_transacao):
    # ... (código inalterado)
    conn, cursor = conectar_bd()
    try:
        cursor.execute("SELECT * FROM transacoes_tb WHERE id = ?", (id_transacao,))
        linha_db = cursor.fetchone()
        return dict(linha_db) if linha_db else None
    except sqlite3.Error as e: raise e
    finally: conn.close()

def editar_transacao_db(id_transacao, descricao, valor, categoria):
    # ... (código inalterado)
    conn, cursor = conectar_bd()
    try:
        cursor.execute("UPDATE transacoes_tb SET descricao = ?, valor = ?, categoria = ? WHERE id = ?",
                       (descricao, valor, categoria, id_transacao))
        conn.commit(); return True
    except sqlite3.Error as e: conn.rollback(); raise e
    finally: conn.close()

def excluir_transacao_db(id_transacao):
    # ... (código inalterado)
    conn, cursor = conectar_bd()
    try:
        cursor.execute("DELETE FROM transacoes_tb WHERE id = ?", (id_transacao,))
        conn.commit(); return cursor.rowcount > 0
    except sqlite3.Error as e: conn.rollback(); raise e
    finally: conn.close()


class AppControleFinanceiro:
    def __init__(self, root_window):
        # ... (Configurações de __init__ como cores, estilos, frames principais,
        #      comboboxes de filtro, treeview, saldos, status_bar - inalterados)
        self.root = root_window
        self.root.title("Controle Financeiro Pessoal")
        self.root.geometry("1000x800")

        self.cor_fundo_principal = "#2e2e2e"
        self.cor_fundo_secundario = "#3c3c3c"
        self.cor_texto_principal = "#e0e0e0"
        self.cor_texto_secundario = "#c0c0c0"
        self.cor_selecao_treeview = "#555555"
        self.cor_required_label = "#75aadb"
        self.root.configure(bg=self.cor_fundo_principal)
        style = ttk.Style(self.root)
        try:
            if 'clam' in style.theme_names(): style.theme_use('clam')
            elif 'alt' in style.theme_names(): style.theme_use('alt')
        except Exception: pass
        style.configure('.', background=self.cor_fundo_principal, foreground=self.cor_texto_principal)
        style.configure('TFrame', background=self.cor_fundo_principal)
        style.configure('TLabel', background=self.cor_fundo_principal, foreground=self.cor_texto_principal, font=('Arial', 10))
        style.configure('Bold.TLabel', background=self.cor_fundo_principal, foreground=self.cor_texto_principal, font=('Arial', 10, 'bold'))
        style.configure('Required.TLabel', background=self.cor_fundo_principal, foreground=self.cor_required_label)
        style.configure('Status.TLabel', background=self.cor_fundo_principal, padding=5)
        style.configure('TButton', background="#505050", foreground=self.cor_texto_principal, font=('Arial', 10), padding=5)
        style.map('TButton', background=[('active', '#606060'), ('disabled', '#404040')], foreground=[('disabled', self.cor_texto_secundario)])
        style.configure("Treeview", background=self.cor_fundo_secundario, foreground=self.cor_texto_principal, fieldbackground=self.cor_fundo_secundario, rowheight=25)
        style.configure("Treeview.Heading", background="#4a4a4a", foreground=self.cor_texto_principal, font=('Arial', 10, 'bold'), padding=5)
        style.map("Treeview", background=[('selected', self.cor_selecao_treeview)], foreground=[('selected', self.cor_texto_principal)])
        style.map("Treeview.Heading", background=[('active', '#5a5a5a')])
        style.configure('TEntry', fieldbackground=self.cor_fundo_secundario, foreground=self.cor_texto_principal, insertcolor=self.cor_texto_principal)
        style.configure('Vertical.TScrollbar', background='#505050', troughcolor=self.cor_fundo_secundario, bordercolor=self.cor_fundo_principal, arrowcolor=self.cor_texto_principal)
        style.map('Vertical.TScrollbar', background=[('active', '#606060')])
        style.configure('TLabelframe', background=self.cor_fundo_principal, bordercolor=self.cor_texto_secundario, padding=(10, 5))
        style.configure('TLabelframe.Label', background=self.cor_fundo_principal, foreground=self.cor_texto_principal, font=('Arial', 10, 'bold'))
        style.configure('TCombobox', fieldbackground=self.cor_fundo_secundario, background=self.cor_fundo_secundario, foreground=self.cor_texto_principal, selectbackground=self.cor_selecao_treeview, selectforeground=self.cor_texto_principal, arrowcolor=self.cor_texto_principal)
        style.configure('TCheckbutton', background=self.cor_fundo_principal, foreground=self.cor_texto_principal) # Estilo para Checkbutton
        style.map('TCheckbutton', background=[('active', self.cor_fundo_secundario)], indicatorcolor=[('selected', self.cor_required_label), ('!selected', self.cor_texto_secundario)])


        self.root.option_add('*TCombobox*Listbox.background', self.cor_fundo_secundario)
        self.root.option_add('*TCombobox*Listbox.foreground', self.cor_texto_principal)
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.cor_selecao_treeview)
        self.root.option_add('*TCombobox*Listbox.selectForeground', self.cor_texto_principal)

        labelframe_acoes = ttk.Labelframe(self.root, text="Ações", padding=(10, 10))
        labelframe_acoes.pack(fill=tk.X, padx=10, pady=(10,5))
        self.btn_add_ganho = ttk.Button(labelframe_acoes, text="Adicionar Ganho", command=self.abrir_janela_adicionar_ganho)
        self.btn_add_ganho.pack(side=tk.LEFT, padx=5)
        self.btn_add_despesa = ttk.Button(labelframe_acoes, text="Adicionar Despesa", command=self.abrir_janela_adicionar_despesa)
        self.btn_add_despesa.pack(side=tk.LEFT, padx=5)
        self.btn_editar = ttk.Button(labelframe_acoes, text="Editar Selecionada", command=self.iniciar_edicao_transacao, state=tk.DISABLED)
        self.btn_editar.pack(side=tk.LEFT, padx=5)
        self.btn_excluir = ttk.Button(labelframe_acoes, text="Excluir Selecionada", command=self.iniciar_exclusao_transacao, state=tk.DISABLED)
        self.btn_excluir.pack(side=tk.LEFT, padx=5)

        labelframe_filtros = ttk.Labelframe(self.root, text="Filtrar por Período", padding=(10,10))
        labelframe_filtros.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(labelframe_filtros, text="Ano:").pack(side=tk.LEFT, padx=(0,5))
        self.ano_selecionado_var = tk.StringVar()
        self.combo_ano = ttk.Combobox(labelframe_filtros, textvariable=self.ano_selecionado_var, width=8, state="readonly", style='TCombobox')
        self.combo_ano.pack(side=tk.LEFT, padx=(0,10))
        self.combo_ano.bind('<<ComboboxSelected>>', self._on_filtro_periodo_changed)
        self._popular_combobox_ano()
        ttk.Label(labelframe_filtros, text="Mês:").pack(side=tk.LEFT, padx=(0,5))
        self.mes_selecionado_var = tk.StringVar()
        self.nomes_meses_pt = [""] + [month_name[i].capitalize() for i in range(1,13)]
        self.combo_mes = ttk.Combobox(labelframe_filtros, textvariable=self.mes_selecionado_var, values=self.nomes_meses_pt[1:], width=12, state="readonly", style='TCombobox')
        self.combo_mes.pack(side=tk.LEFT, padx=(0,10))
        self.combo_mes.bind('<<ComboboxSelected>>', self._on_filtro_periodo_changed)
        self.combo_mes.current(datetime.datetime.now().month - 1)
        btn_limpar_filtro = ttk.Button(labelframe_filtros, text="Ver Todos/Limpar Filtro", command=self._limpar_filtro_periodo)
        btn_limpar_filtro.pack(side=tk.LEFT, padx=10)
        self.filtro_mes_ano_ativo = True

        self.labelframe_lista = ttk.Labelframe(self.root, text="Transações Registradas", padding=(10,10))
        self.labelframe_lista.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        btn_atualizar = ttk.Button(self.labelframe_lista, text="Atualizar Lista e Saldos", command=self.atualizar_tudo)
        btn_atualizar.pack(pady=(0,10))
        self.cols_info = {'ID': {'index': 0, 'type': 'int', 'width': 50, 'anchor': tk.CENTER}, 'Data': {'index': 1, 'type': 'date', 'width': 100, 'anchor': tk.CENTER}, 'Tipo': {'index': 2, 'type': 'str', 'width': 100}, 'Descrição': {'index': 3, 'type': 'str', 'width': 250}, 'Valor (R$)': {'index': 4, 'type': 'float', 'width': 120, 'anchor': tk.E}, 'Categoria': {'index': 5, 'type': 'str', 'width': 150}}
        self.tree_transacoes_cols = list(self.cols_info.keys())
        self.tree_transacoes = ttk.Treeview(self.labelframe_lista, columns=self.tree_transacoes_cols, show='headings', selectmode="browse")
        self.sort_by_column_states = {}
        for col_name in self.tree_transacoes_cols:
            col_data = self.cols_info[col_name]
            self.tree_transacoes.heading(col_name, text=col_name, command=partial(self._sort_treeview_column, col_name, False))
            self.tree_transacoes.column(col_name, width=col_data['width'], anchor=col_data.get('anchor', tk.W))
            self.sort_by_column_states[col_name] = False
        self.tree_transacoes.pack(expand=True, fill=tk.BOTH, pady=(0,5))
        scrollbar = ttk.Scrollbar(self.tree_transacoes, orient=tk.VERTICAL, command=self.tree_transacoes.yview, style='Vertical.TScrollbar')
        self.tree_transacoes.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_transacoes.bind('<<TreeviewSelect>>', self._on_treeview_select)
        self.tree_transacoes.bind('<Double-1>', self._on_treeview_double_click)

        labelframe_saldos = ttk.Labelframe(self.root, text="Resumo Financeiro do Período", padding=(10,10))
        labelframe_saldos.pack(fill=tk.X, padx=10, pady=(5,10))
        saldo_container = ttk.Frame(labelframe_saldos) 
        saldo_container.pack(pady=5)
        self.lbl_total_ganhos_texto = ttk.Label(saldo_container, text="Total de Ganhos: ", style="Bold.TLabel")
        self.lbl_total_ganhos_texto.grid(row=0, column=0, sticky=tk.E, padx=5)
        self.lbl_total_ganhos_valor = ttk.Label(saldo_container, text="R$ 0.00")
        self.lbl_total_ganhos_valor.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.lbl_total_despesas_texto = ttk.Label(saldo_container, text="Total de Despesas: ", style="Bold.TLabel")
        self.lbl_total_despesas_texto.grid(row=1, column=0, sticky=tk.E, padx=5, pady=2)
        self.lbl_total_despesas_valor = ttk.Label(saldo_container, text="R$ 0.00")
        self.lbl_total_despesas_valor.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        self.lbl_saldo_liquido_texto = ttk.Label(saldo_container, text="Saldo Líquido: ", style="Bold.TLabel")
        self.lbl_saldo_liquido_texto.grid(row=2, column=0, sticky=tk.E, padx=5, pady=2)
        self.lbl_saldo_liquido_valor = ttk.Label(saldo_container, text="R$ 0.00")
        self.lbl_saldo_liquido_valor.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        self.status_bar_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_bar_var, style="Status.TLabel", anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0,5))
        self._status_bar_job = None
        self.atualizar_tudo()
        
    # ... (Todos os métodos auxiliares e de atualização como _popular_combobox_ano,
    # _on_filtro_periodo_changed, _limpar_filtro_periodo, _configurar_janela_top_level_dark_mode,
    # mostrar_mensagem_status, _limpar_mensagem_status, _converter_valor_para_ordenacao,
    # _sort_treeview_column, _on_treeview_select, _on_treeview_double_click,
    # formatar_data_para_exibicao, atualizar_lista_transacoes, atualizar_exibicao_saldo,
    # atualizar_tudo, _centralizar_janela_toplevel - INALTERADOS)
    def _popular_combobox_ano(self):
        try:
            anos_db = buscar_anos_disponiveis_db()
            ano_atual_str = str(datetime.datetime.now().year)
            if ano_atual_str not in anos_db: anos_db.append(ano_atual_str)
            anos_db.sort(key=int, reverse=True) 
            self.combo_ano['values'] = anos_db
            if anos_db: self.ano_selecionado_var.set(ano_atual_str if ano_atual_str in anos_db else anos_db[0])
            else: self.ano_selecionado_var.set(ano_atual_str)
        except Exception as e:
            self.mostrar_mensagem_status(f"Erro ao popular anos: {e}", tipo='erro')
            self.ano_selecionado_var.set(str(datetime.datetime.now().year))
            self.combo_ano['values'] = [str(datetime.datetime.now().year)]

    def _on_filtro_periodo_changed(self, event=None):
        ano_val = self.ano_selecionado_var.get()
        mes_val = self.mes_selecionado_var.get()
        if ano_val and mes_val: 
            self.filtro_mes_ano_ativo = True
            self.atualizar_tudo()

    def _limpar_filtro_periodo(self):
        self.filtro_mes_ano_ativo = False
        self._popular_combobox_ano() 
        self.combo_mes.current(datetime.datetime.now().month - 1) 
        self.atualizar_tudo()

    def _configurar_janela_top_level_dark_mode(self, janela_top_level, form_title="Formulário"):
        janela_top_level.configure(bg=self.cor_fundo_principal)
        main_form_labelframe = ttk.Labelframe(janela_top_level, text=form_title, padding=(15,10))
        main_form_labelframe.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        return main_form_labelframe
    
    def _centralizar_janela_toplevel(self, janela_top):
        janela_top.update_idletasks()
        width = janela_top.winfo_width(); height = janela_top.winfo_height()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        janela_top.geometry(f'{width}x{height}+{x}+{y}')

    def mostrar_mensagem_status(self, mensagem, duracao_ms=4000, tipo='info'):
        if self._status_bar_job: self.root.after_cancel(self._status_bar_job)
        cor_map = {'sucesso': "#77dd77", 'erro': "#ff6961", 'info': self.cor_texto_secundario}
        self.status_bar_var.set(mensagem)
        self.status_bar.config(foreground=cor_map.get(tipo, self.cor_texto_principal))
        self._status_bar_job = self.root.after(duracao_ms, self._limpar_mensagem_status)

    def _limpar_mensagem_status(self): self.status_bar_var.set(""); self._status_bar_job = None

    def _converter_valor_para_ordenacao(self, valor_str, tipo_coluna):
        if valor_str is None or valor_str == "-": return "" if tipo_coluna == 'str' else (datetime.datetime.min if tipo_coluna == 'date' else 0)
        if tipo_coluna == 'int': return int(valor_str)
        elif tipo_coluna == 'float':
            try: return float(str(valor_str).replace('R$', '').replace('.', '',100).replace(',', '.').strip())
            except ValueError: return 0.0
        elif tipo_coluna == 'date':
            try: return datetime.datetime.strptime(valor_str, '%d/%m/%Y')
            except ValueError: return datetime.datetime.min 
        return str(valor_str).lower() 

    def _sort_treeview_column(self, col_name, reverse):
        col_type = self.cols_info[col_name]['type']
        try:
            data_list = [(self._converter_valor_para_ordenacao(self.tree_transacoes.set(item_id, col_name), col_type), item_id)
                         for item_id in self.tree_transacoes.get_children('')]
        except Exception as e: self.mostrar_mensagem_status(f"Erro ao ordenar: {e}", tipo='erro'); return
        data_list.sort(key=lambda x: x[0], reverse=reverse)
        for i, (val, item_id) in enumerate(data_list): self.tree_transacoes.move(item_id, '', i)
        for c in self.tree_transacoes_cols:
             current_text = c
             if c == col_name: current_text += ' ▼' if reverse else ' ▲'
             self.tree_transacoes.heading(c, text=current_text, command=partial(self._sort_treeview_column, c, (not reverse if c == col_name else self.sort_by_column_states.get(c, False) )))
        self.sort_by_column_states[col_name] = reverse

    def _on_treeview_select(self, event):
        state = tk.NORMAL if self.tree_transacoes.selection() else tk.DISABLED
        self.btn_editar.config(state=state)
        self.btn_excluir.config(state=state)

    def _on_treeview_double_click(self, event):
        if self.tree_transacoes.selection(): self.iniciar_edicao_transacao()

    def formatar_data_para_exibicao(self, data_iso):
        if not data_iso: return ""
        if isinstance(data_iso, str):
            try: data_obj = datetime.datetime.fromisoformat(data_iso)
            except ValueError: return data_iso 
        else: data_obj = data_iso
        return data_obj.strftime('%d/%m/%Y')
    
    def atualizar_lista_transacoes(self):
        for i in self.tree_transacoes.get_children(): self.tree_transacoes.delete(i)
        ano_f, mes_f = None, None
        titulo_lista = "Todas as Transações Registradas" 
        if self.filtro_mes_ano_ativo:
            try:
                ano_str = self.ano_selecionado_var.get()
                mes_nome = self.mes_selecionado_var.get()
                if ano_str: ano_f = int(ano_str)
                if mes_nome and mes_nome in self.nomes_meses_pt: mes_f = self.nomes_meses_pt.index(mes_nome)
                if ano_f and mes_f: titulo_lista = f"Transações de {self.nomes_meses_pt[mes_f]}/{ano_f}"
                elif ano_f: titulo_lista = f"Transações de Todo o Ano de {ano_f}"
                elif mes_f: titulo_lista = f"Transações de {self.nomes_meses_pt[mes_f]} (Todos os Anos)"
                else: self.filtro_mes_ano_ativo = False; ano_f, mes_f = None, None
            except ValueError: 
                self.mostrar_mensagem_status("Seleção de Ano/Mês inválida para filtro.", tipo='erro')
                ano_f, mes_f = None, None; self.filtro_mes_ano_ativo = False
        self.labelframe_lista.config(text=titulo_lista)
        try:
            transacoes = buscar_transacoes_db(ano=ano_f, mes=mes_f)
            if transacoes:
                for transacao in transacoes:
                    self.tree_transacoes.insert('', tk.END, values=(
                        transacao['id'], self.formatar_data_para_exibicao(transacao['data_registro']),
                        transacao['tipo'].capitalize(), transacao['descricao'],
                        f"{transacao['valor']:.2f}", transacao['categoria'] if transacao['categoria'] is not None else "-"
                    ))
            for col_name in self.tree_transacoes_cols:
                 self.tree_transacoes.heading(col_name, text=col_name, command=partial(self._sort_treeview_column, col_name, False))
                 self.sort_by_column_states[col_name] = False
        except Exception as e: self.mostrar_mensagem_status(f"Erro ao buscar transações: {e}", tipo='erro')

    def atualizar_exibicao_saldo(self):
        ano_f, mes_f = None, None
        if self.filtro_mes_ano_ativo:
            try:
                ano_str = self.ano_selecionado_var.get()
                mes_nome = self.mes_selecionado_var.get()
                if ano_str: ano_f = int(ano_str)
                if mes_nome and mes_nome in self.nomes_meses_pt: mes_f = self.nomes_meses_pt.index(mes_nome)
                if not (ano_f and mes_f): ano_f, mes_f = None, None
            except ValueError: ano_f, mes_f = None, None
        try:
            total_ganhos, total_despesas, saldo_liquido = calcular_saldo_db(ano=ano_f, mes=mes_f)
            self.lbl_total_ganhos_valor.config(text=f"R$ {total_ganhos:.2f}")
            self.lbl_total_despesas_valor.config(text=f"R$ {total_despesas:.2f}")
            cor_saldo_texto = "#77dd77" if saldo_liquido >= 0 else "#ff6961"
            self.lbl_saldo_liquido_valor.config(text=f"R$ {saldo_liquido:.2f}", foreground=cor_saldo_texto)
        except Exception as e: self.mostrar_mensagem_status(f"Erro ao calcular saldo: {e}", tipo='erro')

    def atualizar_tudo(self):
        self.atualizar_lista_transacoes()
        self.atualizar_exibicao_saldo()
        self._on_treeview_select(None)

    # --- Métodos para Adicionar Ganho (semelhantes à versão anterior, adaptados para tema) ---
    def _salvar_novo_ganho(self, janela_adicionar, entry_descricao, entry_valor):
        # ... (lógica de validação e chamada a adicionar_ganho_db) ...
        descricao = entry_descricao.get().strip()
        valor_str = entry_valor.get().strip().replace(',', '.')
        if not descricao: messagebox.showerror("Erro de Validação", "Descrição: * não pode ser vazia.", parent=janela_adicionar); return
        if not valor_str: messagebox.showerror("Erro de Validação", "Valor (R$): * não pode ser vazio.", parent=janela_adicionar); return
        try:
            valor = float(valor_str)
            if valor <= 0: messagebox.showerror("Erro de Validação", "Valor deve ser positivo.", parent=janela_adicionar); return
        except ValueError: messagebox.showerror("Erro de Validação", "Valor inválido.", parent=janela_adicionar); return
        try:
            if adicionar_ganho_db(descricao, valor): # Passa a data da primeira parcela
                self.mostrar_mensagem_status("Ganho adicionado com sucesso!", tipo='sucesso')
                janela_adicionar.destroy(); self.atualizar_tudo()
        except Exception as e: messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o ganho: {e}", parent=janela_adicionar)


    def abrir_janela_adicionar_ganho(self):
        # ... (código da janela de adicionar ganho, usando _configurar_janela_top_level_dark_mode)
        janela_ganho = tk.Toplevel(self.root)
        janela_ganho.title("Adicionar Novo Ganho")
        janela_ganho.geometry("400x180") 
        janela_ganho.resizable(False, False); janela_ganho.transient(self.root); janela_ganho.grab_set()
        form_labelframe = self._configurar_janela_top_level_dark_mode(janela_ganho, "Detalhes do Ganho")
        lbl_descricao = ttk.Label(form_labelframe, text="Descrição: *", style="Required.TLabel")
        lbl_descricao.grid(row=0, column=0, padx=5, pady=8, sticky=tk.W)
        entry_descricao = ttk.Entry(form_labelframe, width=35, style='TEntry')
        entry_descricao.grid(row=0, column=1, padx=5, pady=8, sticky=tk.EW)
        entry_descricao.focus()
        lbl_valor = ttk.Label(form_labelframe, text="Valor (R$): *", style="Required.TLabel")
        lbl_valor.grid(row=1, column=0, padx=5, pady=8, sticky=tk.W)
        entry_valor = ttk.Entry(form_labelframe, width=20, style='TEntry')
        entry_valor.grid(row=1, column=1, padx=5, pady=8, sticky=tk.W)
        frame_botoes = ttk.Frame(form_labelframe) 
        frame_botoes.grid(row=2, column=0, columnspan=2, pady=(15,5))
        btn_salvar = ttk.Button(frame_botoes, text="Salvar", style='TButton', command=lambda: self._salvar_novo_ganho(janela_ganho, entry_descricao, entry_valor))
        btn_salvar.pack(side=tk.LEFT, padx=10)
        janela_ganho.bind("<Return>", lambda e: self._salvar_novo_ganho(janela_ganho, entry_descricao, entry_valor))
        btn_cancelar = ttk.Button(frame_botoes, text="Cancelar", style='TButton', command=janela_ganho.destroy)
        btn_cancelar.pack(side=tk.LEFT, padx=10)
        self._centralizar_janela_toplevel(janela_ganho)


    # --- Métodos para Adicionar Despesa (COM LÓGICA DE PARCELAS) ---
    def _toggle_campos_parcela(self, var_parcelado, lbl_num_parcelas, entry_num_parcelas, lbl_valor_parcela, entry_valor_parcela, lbl_valor_original, entry_valor_original, lbl_data_primeira_parcela, entry_data_primeira_parcela):
        if var_parcelado.get():
            lbl_num_parcelas.grid(); entry_num_parcelas.grid()
            lbl_valor_parcela.grid(); entry_valor_parcela.grid()
            lbl_data_primeira_parcela.grid(); entry_data_primeira_parcela.grid()
            lbl_valor_original.config(text="Valor Total (R$): *") # Muda o label do valor original
        else:
            lbl_num_parcelas.grid_remove(); entry_num_parcelas.grid_remove()
            lbl_valor_parcela.grid_remove(); entry_valor_parcela.grid_remove()
            lbl_data_primeira_parcela.grid_remove(); entry_data_primeira_parcela.grid_remove()
            lbl_valor_original.config(text="Valor (R$): *") # Volta o label do valor original

    def _salvar_nova_despesa(self, janela_adicionar, entry_descricao, entry_valor_principal, entry_categoria,
                             var_parcelado, entry_num_parcelas, entry_valor_parcela, entry_data_primeira_parcela):
        descricao_base = entry_descricao.get().strip()
        categoria = entry_categoria.get().strip()
        
        if not descricao_base: messagebox.showerror("Erro de Validação", "Descrição: * não pode ser vazia.", parent=janela_adicionar); return
        if not categoria: messagebox.showerror("Erro de Validação", "Categoria: * não pode ser vazia.", parent=janela_adicionar); return

        is_parcelado = var_parcelado.get()

        if is_parcelado:
            valor_parcela_str = entry_valor_parcela.get().strip().replace(',', '.')
            num_parcelas_str = entry_num_parcelas.get().strip()
            data_primeira_str = entry_data_primeira_parcela.get().strip()

            if not valor_parcela_str: messagebox.showerror("Erro de Validação", "Valor da Parcela: * não pode ser vazio.", parent=janela_adicionar); return
            if not num_parcelas_str: messagebox.showerror("Erro de Validação", "No. de Parcelas: * não pode ser vazio.", parent=janela_adicionar); return
            if not data_primeira_str: messagebox.showerror("Erro de Validação", "Data da 1ª Parcela: * não pode ser vazia (DD/MM/AAAA).", parent=janela_adicionar); return

            try:
                valor_da_parcela = float(valor_parcela_str)
                if valor_da_parcela <= 0: messagebox.showerror("Erro de Validação", "Valor da parcela deve ser positivo.", parent=janela_adicionar); return
            except ValueError: messagebox.showerror("Erro de Validação", "Valor da parcela inválido.", parent=janela_adicionar); return
            try:
                total_parcelas = int(num_parcelas_str)
                if total_parcelas <= 1 : messagebox.showerror("Erro de Validação", "No. de parcelas deve ser maior que 1.", parent=janela_adicionar); return
            except ValueError: messagebox.showerror("Erro de Validação", "No. de parcelas inválido.", parent=janela_adicionar); return
            try:
                data_primeira_obj = datetime.datetime.strptime(data_primeira_str, "%d/%m/%Y")
            except ValueError: messagebox.showerror("Erro de Validação", "Formato da Data da 1ª Parcela inválido. Use DD/MM/AAAA.", parent=janela_adicionar); return

            sucesso_total = True
            for i in range(total_parcelas):
                descricao_parcela = f"{descricao_base} (Parcela {i+1}/{total_parcelas})"
                
                current_month = data_primeira_obj.month + i
                current_year = data_primeira_obj.year + (current_month - 1) // 12
                current_month = (current_month - 1) % 12 + 1
                
                # Tenta manter o dia, mas ajusta para o último dia do mês se o dia original não existir
                day_of_installment = data_primeira_obj.day
                _, last_day_of_target_month = monthrange(current_year, current_month)
                if day_of_installment > last_day_of_target_month:
                    day_of_installment = last_day_of_target_month
                
                data_parcela_obj = datetime.datetime(current_year, current_month, day_of_installment)
                data_parcela_iso = data_parcela_obj.isoformat()

                try:
                    if not adicionar_despesa_db(descricao_parcela, valor_da_parcela, categoria, data_parcela_iso):
                        sucesso_total = False; break # Para o loop se uma inserção falhar
                except Exception as e:
                    messagebox.showerror("Erro ao Salvar Parcela", f"Não foi possível salvar a parcela {i+1}: {e}", parent=janela_adicionar)
                    sucesso_total = False; break
            
            if sucesso_total:
                self.mostrar_mensagem_status(f"{total_parcelas} parcelas adicionadas com sucesso!", tipo='sucesso')
                janela_adicionar.destroy(); self.atualizar_tudo()
            # Se não foi sucesso total, uma mensagem de erro já foi mostrada.

        else: # Despesa não parcelada
            valor_principal_str = entry_valor_principal.get().strip().replace(',', '.')
            if not valor_principal_str: messagebox.showerror("Erro de Validação", "Valor (R$): * não pode ser vazio.", parent=janela_adicionar); return
            try:
                valor = float(valor_principal_str)
                if valor <= 0: messagebox.showerror("Erro de Validação", "Valor da despesa deve ser positivo.", parent=janela_adicionar); return
            except ValueError: messagebox.showerror("Erro de Validação", "Valor inválido.", parent=janela_adicionar); return
            try:
                if adicionar_despesa_db(descricao_base, valor, categoria): # Data será CURRENT_TIMESTAMP
                    self.mostrar_mensagem_status("Despesa adicionada com sucesso!", tipo='sucesso')
                    janela_adicionar.destroy(); self.atualizar_tudo()
            except Exception as e: messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar a despesa: {e}", parent=janela_adicionar)


    def abrir_janela_adicionar_despesa(self):
        janela_despesa = tk.Toplevel(self.root)
        janela_despesa.title("Adicionar Nova Despesa")
        # A geometria será ajustada dinamicamente
        janela_despesa.resizable(False, False); janela_despesa.transient(self.root); janela_despesa.grab_set()

        form_labelframe = self._configurar_janela_top_level_dark_mode(janela_despesa, "Detalhes da Despesa")
        
        row_idx = 0
        lbl_descricao = ttk.Label(form_labelframe, text="Descrição: *", style="Required.TLabel")
        lbl_descricao.grid(row=row_idx, column=0, padx=5, pady=8, sticky=tk.W)
        entry_descricao = ttk.Entry(form_labelframe, width=35, style='TEntry')
        entry_descricao.grid(row=row_idx, column=1, padx=5, pady=8, sticky=tk.EW)
        entry_descricao.focus()
        row_idx+=1

        # Valor principal / Valor Total (se parcelado)
        lbl_valor_principal = ttk.Label(form_labelframe, text="Valor (R$): *", style="Required.TLabel")
        lbl_valor_principal.grid(row=row_idx, column=0, padx=5, pady=8, sticky=tk.W)
        entry_valor_principal = ttk.Entry(form_labelframe, width=20, style='TEntry')
        entry_valor_principal.grid(row=row_idx, column=1, padx=5, pady=8, sticky=tk.W)
        row_idx+=1

        lbl_categoria = ttk.Label(form_labelframe, text="Categoria: *", style="Required.TLabel")
        lbl_categoria.grid(row=row_idx, column=0, padx=5, pady=8, sticky=tk.W)
        entry_categoria = ttk.Entry(form_labelframe, width=35, style='TEntry')
        entry_categoria.grid(row=row_idx, column=1, padx=5, pady=8, sticky=tk.EW)
        row_idx+=1

        var_parcelado = tk.BooleanVar()
        chk_parcelado = ttk.Checkbutton(form_labelframe, text="Compra Parcelada?", variable=var_parcelado, style='TCheckbutton')
        chk_parcelado.grid(row=row_idx, column=0, columnspan=2, padx=5, pady=10, sticky=tk.W)
        row_idx+=1

        # Campos de parcela (inicialmente escondidos por grid_remove, mas criados)
        lbl_num_parcelas = ttk.Label(form_labelframe, text="No. de Parcelas: *", style="Required.TLabel")
        entry_num_parcelas = ttk.Entry(form_labelframe, width=10, style='TEntry')
        lbl_valor_parcela = ttk.Label(form_labelframe, text="Valor da Parcela: *", style="Required.TLabel")
        entry_valor_parcela = ttk.Entry(form_labelframe, width=20, style='TEntry')
        lbl_data_primeira_parcela = ttk.Label(form_labelframe, text="Data da 1ª Parcela (DD/MM/AAAA): *", style="Required.TLabel")
        entry_data_primeira_parcela = ttk.Entry(form_labelframe, width=20, style='TEntry')
        entry_data_primeira_parcela.insert(0, datetime.date.today().strftime("%d/%m/%Y"))


        # Posiciona os campos de parcela, mas eles são gerenciados pelo _toggle_campos_parcela
        lbl_num_parcelas.grid(row=row_idx, column=0, padx=5, pady=8, sticky=tk.W)
        entry_num_parcelas.grid(row=row_idx, column=1, padx=5, pady=8, sticky=tk.W)
        row_idx+=1
        lbl_valor_parcela.grid(row=row_idx, column=0, padx=5, pady=8, sticky=tk.W)
        entry_valor_parcela.grid(row=row_idx, column=1, padx=5, pady=8, sticky=tk.W)
        row_idx+=1
        lbl_data_primeira_parcela.grid(row=row_idx, column=0, padx=5, pady=8, sticky=tk.W)
        entry_data_primeira_parcela.grid(row=row_idx, column=1, padx=5, pady=8, sticky=tk.W)
        row_idx+=1

        # Comando para o Checkbutton
        chk_parcelado.config(command=lambda: self._toggle_campos_parcela(var_parcelado, lbl_num_parcelas, entry_num_parcelas, lbl_valor_parcela, entry_valor_parcela, lbl_valor_principal, entry_valor_principal, lbl_data_primeira_parcela, entry_data_primeira_parcela))
        self._toggle_campos_parcela(var_parcelado, lbl_num_parcelas, entry_num_parcelas, lbl_valor_parcela, entry_valor_parcela, lbl_valor_principal, entry_valor_principal, lbl_data_primeira_parcela, entry_data_primeira_parcela) # Estado inicial


        frame_botoes = ttk.Frame(form_labelframe)
        frame_botoes.grid(row=row_idx, column=0, columnspan=2, pady=(15,5))
        btn_salvar = ttk.Button(frame_botoes, text="Salvar", style='TButton',
                                command=lambda: self._salvar_nova_despesa(janela_despesa, entry_descricao, entry_valor_principal, entry_categoria, var_parcelado, entry_num_parcelas, entry_valor_parcela, entry_data_primeira_parcela))
        btn_salvar.pack(side=tk.LEFT, padx=10)
        janela_despesa.bind("<Return>", lambda e: self._salvar_nova_despesa(janela_despesa, entry_descricao, entry_valor_principal, entry_categoria, var_parcelado, entry_num_parcelas, entry_valor_parcela, entry_data_primeira_parcela))
        btn_cancelar = ttk.Button(frame_botoes, text="Cancelar", style='TButton', command=janela_despesa.destroy)
        btn_cancelar.pack(side=tk.LEFT, padx=10)
        
        janela_despesa.update_idletasks() # Importante para o cálculo da geometria antes de centralizar
        # A geometria da janela de despesa agora pode ser maior se os campos de parcela estiverem visíveis
        # Poderíamos ajustar a geometria inicial da janela_despesa aqui ou deixar como está.
        # Por simplicidade, a altura inicial da janela de despesa pode precisar de ajuste manual para o pior caso.
        # Ou recalcular e definir a geometria aqui após os widgets serem mostrados/escondidos.
        # Vamos dar um tamanho inicial maior para a janela de despesa para acomodar os campos de parcela.
        if not var_parcelado.get(): # Se não parcelado, a janela pode ser menor
             janela_despesa.geometry("400x260") # Altura para despesa normal
        else: # Se parcelado, precisa de mais altura
             janela_despesa.geometry("450x400") # Altura para despesa parcelada

        self._centralizar_janela_toplevel(janela_despesa)


    def _salvar_edicao_transacao(self, janela_editar, id_transacao, entry_descricao, entry_valor, entry_categoria_widget, tipo_original):
        # ... (código da versão anterior)
        nova_descricao = entry_descricao.get().strip()
        novo_valor_str = entry_valor.get().strip().replace(',', '.')
        nova_categoria = None
        if tipo_original == 'despesa' and entry_categoria_widget: nova_categoria = entry_categoria_widget.get().strip()
        if not nova_descricao: messagebox.showerror("Erro de Validação", "Descrição: * não pode ser vazia.", parent=janela_editar); return
        if not novo_valor_str: messagebox.showerror("Erro de Validação", "Valor (R$): * não pode ser vazio.", parent=janela_editar); return
        if tipo_original == 'despesa' and not nova_categoria: messagebox.showerror("Erro de Validação", "Categoria: * não pode ser vazia.", parent=janela_editar); return
        try:
            novo_valor = float(novo_valor_str)
            if novo_valor <= 0: messagebox.showerror("Erro de Validação", "Valor deve ser positivo.", parent=janela_editar); return
        except ValueError: messagebox.showerror("Erro de Validação", "Valor inválido.", parent=janela_editar); return
        try:
            if editar_transacao_db(id_transacao, nova_descricao, novo_valor, nova_categoria):
                self.mostrar_mensagem_status("Transação atualizada com sucesso!", tipo='sucesso')
                janela_editar.destroy(); self.atualizar_tudo()
        except Exception as e: messagebox.showerror("Erro ao Editar", f"Não foi possível editar: {e}", parent=janela_editar)

    def abrir_janela_editar_transacao(self, id_transacao):
        # ... (código da versão anterior)
        try: transacao_atual = _buscar_transacao_por_id_db(id_transacao)
        except Exception as e: messagebox.showerror("Erro", f"Erro ao buscar transação: {e}"); return
        if not transacao_atual: messagebox.showerror("Erro", "Transação não encontrada."); return
        janela_editar = tk.Toplevel(self.root)
        janela_editar.title(f"Editar Transação ID: {id_transacao}")
        janela_editar.geometry("450x280" if transacao_atual['tipo'] == 'ganho' else "450x320") 
        janela_editar.resizable(False, False); janela_editar.transient(self.root); janela_editar.grab_set()
        form_labelframe = self._configurar_janela_top_level_dark_mode(janela_editar, f"Editando Transação {id_transacao}")
        row_idx = 0
        ttk.Label(form_labelframe, text="Tipo:", style='TLabel').grid(row=row_idx, column=0, padx=5, pady=8, sticky=tk.W)
        ttk.Label(form_labelframe, text=transacao_atual['tipo'].capitalize(), style='TLabel').grid(row=row_idx, column=1, padx=5, pady=8, sticky=tk.W)
        row_idx += 1
        lbl_descricao = ttk.Label(form_labelframe, text="Descrição: *", style="Required.TLabel")
        lbl_descricao.grid(row=row_idx, column=0, padx=5, pady=8, sticky=tk.W)
        entry_descricao = ttk.Entry(form_labelframe, width=35, style='TEntry')
        entry_descricao.grid(row=row_idx, column=1, padx=5, pady=8, sticky=tk.EW)
        entry_descricao.insert(0, transacao_atual['descricao']); entry_descricao.focus()
        row_idx += 1
        lbl_valor = ttk.Label(form_labelframe, text="Valor (R$): *", style="Required.TLabel")
        lbl_valor.grid(row=row_idx, column=0, padx=5, pady=8, sticky=tk.W)
        entry_valor = ttk.Entry(form_labelframe, width=20, style='TEntry')
        entry_valor.grid(row=row_idx, column=1, padx=5, pady=8, sticky=tk.W)
        entry_valor.insert(0, f"{transacao_atual['valor']:.2f}")
        row_idx += 1
        entry_categoria_widget = None 
        if transacao_atual['tipo'] == 'despesa':
            lbl_categoria = ttk.Label(form_labelframe, text="Categoria: *", style="Required.TLabel")
            lbl_categoria.grid(row=row_idx, column=0, padx=5, pady=8, sticky=tk.W)
            entry_categoria_widget = ttk.Entry(form_labelframe, width=35, style='TEntry')
            entry_categoria_widget.grid(row=row_idx, column=1, padx=5, pady=8, sticky=tk.EW)
            entry_categoria_widget.insert(0, transacao_atual['categoria'] or "")
            row_idx += 1
        frame_botoes = ttk.Frame(form_labelframe)
        frame_botoes.grid(row=row_idx, column=0, columnspan=2, pady=(15,5))
        btn_salvar = ttk.Button(frame_botoes, text="Salvar Alterações", style='TButton', command=lambda: self._salvar_edicao_transacao(janela_editar, id_transacao, entry_descricao, entry_valor, entry_categoria_widget, transacao_atual['tipo']))
        btn_salvar.pack(side=tk.LEFT, padx=10)
        janela_editar.bind("<Return>", lambda e: self._salvar_edicao_transacao(janela_editar, id_transacao, entry_descricao, entry_valor, entry_categoria_widget, transacao_atual['tipo']))
        btn_cancelar = ttk.Button(frame_botoes, text="Cancelar", style='TButton', command=janela_editar.destroy)
        btn_cancelar.pack(side=tk.LEFT, padx=10)
        self._centralizar_janela_toplevel(janela_editar)

    def iniciar_edicao_transacao(self):
        # ... (código da versão anterior)
        selecionado = self.tree_transacoes.selection()
        if not selecionado: messagebox.showwarning("Nenhuma Seleção", "Selecione uma transação para editar.", parent=self.root); return
        try:
            id_transacao = self.tree_transacoes.item(selecionado[0], 'values')[0]
            self.abrir_janela_editar_transacao(int(id_transacao))
        except (IndexError, TypeError): messagebox.showerror("Erro", "Não foi possível obter dados da seleção.", parent=self.root)

    def iniciar_exclusao_transacao(self):
        # ... (código da versão anterior)
        selecionado = self.tree_transacoes.selection()
        if not selecionado: messagebox.showwarning("Nenhuma Seleção", "Selecione uma transação para excluir.", parent=self.root); return
        try:
            valores = self.tree_transacoes.item(selecionado[0], 'values')
            id_t, desc_t, val_t = int(valores[0]), valores[3], valores[4]
            confirmar = messagebox.askyesno("Confirmar Exclusão", f"Excluir: ID {id_t}, {desc_t}, R$ {val_t}?", icon='warning', parent=self.root)
            if confirmar:
                try:
                    if excluir_transacao_db(id_t):
                        self.mostrar_mensagem_status("Transação excluída!", tipo='sucesso'); self.atualizar_tudo()
                    else: self.mostrar_mensagem_status(f"ID {id_t} não encontrado para exclusão.", tipo='info')
                except Exception as e: messagebox.showerror("Erro ao Excluir", f"Não foi possível excluir: {e}", parent=self.root)
        except (IndexError, TypeError): messagebox.showerror("Erro", "Não foi possível obter dados da seleção.", parent=self.root)


if __name__ == '__main__':
    inicializar_banco_de_dados()
    root = tk.Tk()
    app = AppControleFinanceiro(root)
    root.mainloop()