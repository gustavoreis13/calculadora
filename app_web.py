import sqlite3
import datetime
from flask import Flask, render_template, request, redirect, url_for # Novas importações!

# --- LÓGICA DO BANCO DE DADOS (Inalterada) ---
NOME_BANCO_DADOS = 'controle_financeiro.db'

def conectar_bd():
    conn = sqlite3.connect(NOME_BANCO_DADOS)
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor()

def inicializar_banco_de_dados():
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
    conn, cursor = conectar_bd()
    try:
        query = "SELECT id, tipo, descricao, valor, categoria, data_registro FROM transacoes_tb"
        params = []
        conditions = []
        if ano: conditions.append("strftime('%Y', data_registro) = ?"); params.append(str(ano))
        if mes: conditions.append("strftime('%m', data_registro) = ?"); params.append(f"{int(mes):02d}")
        if conditions: query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY data_registro DESC, id DESC"
        cursor.execute(query, params)
        return [dict(linha) for linha in cursor.fetchall()]
    except sqlite3.Error as e: print(f"Erro: {e}"); raise e
    finally: conn.close()

def adicionar_despesa_db(descricao, valor, categoria):
    conn, cursor = conectar_bd()
    try:
        data_atual_iso = datetime.datetime.now().isoformat()
        cursor.execute("INSERT INTO transacoes_tb (tipo, descricao, valor, categoria, data_registro) VALUES (?, ?, ?, ?, ?)",
                       ('despesa', descricao, valor, categoria, data_atual_iso))
        conn.commit(); return True
    except sqlite3.Error as e: conn.rollback(); raise e
    finally: conn.close()

# --- APLICAÇÃO WEB COM FLASK ---
app = Flask(__name__)

@app.route('/')
def pagina_inicial():
    try:
        transacoes_do_banco = buscar_transacoes_db()
        for transacao in transacoes_do_banco:
            data_obj = datetime.datetime.fromisoformat(transacao['data_registro'])
            transacao['data_formatada'] = data_obj.strftime('%d/%m/%Y')
        return render_template('index.html', transacoes=transacoes_do_banco)
    except Exception as e:
        return f"<h1>Ocorreu um Erro</h1><p>Não foi possível buscar as transações: {e}</p>"

# ESTA É A NOVA ROTA QUE DÁ VIDA AO BOTÃO
@app.route('/despesa/nova', methods=['GET', 'POST'])
def adicionar_despesa_web():
    if request.method == 'POST':
        try:
            descricao = request.form['descricao']
            valor = float(request.form['valor'])
            categoria = request.form['categoria']

            if not descricao or valor <= 0 or not categoria:
                return "Erro: Todos os campos são obrigatórios e o valor deve ser positivo.", 400

            adicionar_despesa_db(descricao, valor, categoria)
            
            return redirect(url_for('pagina_inicial'))
        except Exception as e:
            return f"<h1>Ocorreu um Erro ao Salvar</h1><p>Não foi possível salvar a despesa: {e}</p>"
    
    # Se o método for GET, apenas mostra o formulário
    return render_template('form_despesa.html')

if __name__ == '__main__':
    inicializar_banco_de_dados()
    app.run(debug=True)