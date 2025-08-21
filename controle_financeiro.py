import sqlite3
import datetime

# Nome do arquivo do banco de dados
NOME_BANCO_DADOS = 'controle_financeiro.db'

def conectar_bd():
    """Conecta ao banco de dados SQLite e retorna a conexão e o cursor."""
    conn = sqlite3.connect(NOME_BANCO_DADOS)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    return conn, cursor

def inicializar_banco_de_dados():
    """Cria a tabela de transações no banco de dados, se ela não existir."""
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

def _converter_linha_para_dicionario(linha_db):
    """Converte uma linha do banco de dados (objeto Row) para um dicionário."""
    if linha_db:
        return dict(linha_db)
    return None

def _buscar_transacao_por_id(id_transacao):
    """Busca uma transação específica pelo seu ID."""
    conn, cursor = conectar_bd()
    try:
        cursor.execute("SELECT * FROM transacoes_tb WHERE id = ?", (id_transacao,))
        linha_db = cursor.fetchone()
        return _converter_linha_para_dicionario(linha_db)
    except sqlite3.Error as e:
        print(f"Erro ao buscar transação por ID: {e}")
        return None
    finally:
        conn.close()

def _exibir_lista_formatada(lista_a_exibir, titulo):
    print(f"\n--- {titulo} ---")
    if not lista_a_exibir:
        print("Nenhuma transação encontrada.")
        return

    print(f"{'ID':<5} {'Data':<12} {'Tipo':<10} {'Descrição':<25} {'Valor (R$)':<15} {'Categoria':<20}")
    print("-" * 90)

    for transacao_dict in lista_a_exibir:
        valor_formatado = f"{transacao_dict['valor']:.2f}"
        categoria_exibida = transacao_dict['categoria'] if transacao_dict['categoria'] is not None else "-"
        # Tratamento para data_registro que pode ser string ou datetime dependendo da origem
        if isinstance(transacao_dict['data_registro'], str):
            data_obj = datetime.datetime.fromisoformat(transacao_dict['data_registro'])
        else: # Assume que é um objeto datetime
            data_obj = transacao_dict['data_registro']
        data_formatada = data_obj.strftime('%d/%m/%Y')


        print(f"{transacao_dict['id']:<5} {data_formatada:<12} {transacao_dict['tipo'].capitalize():<10} {transacao_dict['descricao']:<25} {valor_formatado:<15} {categoria_exibida:<20}")
    print("-" * 90)

def adicionar_ganho():
    print("\n-- Adicionar Novo(s) Ganho(s) --")
    while True:
        descricao = input("Descrição do ganho (ex: Salário, Venda de item): ")
        valor = 0.0
        while True:
            try:
                valor_str = input("Valor do ganho (ex: 50.75): ")
                valor = float(valor_str.replace(',', '.'))
                if valor <= 0:
                    print("O valor do ganho deve ser positivo. Tente novamente.")
                else:
                    break
            except ValueError:
                print("Valor inválido. Por favor, insira um número (ex: 50.75 ou 1200).")

        conn, cursor = conectar_bd()
        try:
            cursor.execute('''
                INSERT INTO transacoes_tb (tipo, descricao, valor, categoria)
                VALUES (?, ?, ?, ?)
            ''', ('ganho', descricao, valor, None))
            conn.commit()
            print(f"Ganho '{descricao}' no valor de R$ {valor:.2f} adicionado com sucesso!")
        except sqlite3.Error as e:
            print(f"Erro ao adicionar ganho ao banco de dados: {e}")
            conn.rollback()
        finally:
            conn.close()

        continuar = input("Deseja adicionar outro ganho? (s/n): ").strip().lower()
        if continuar != 's':
            break

def adicionar_despesa():
    print("\n-- Adicionar Nova(s) Despesa(s) --")
    while True:
        descricao = input("Descrição da despesa (ex: Aluguel, Supermercado): ")
        valor = 0.0
        while True:
            try:
                valor_str = input("Valor da despesa (ex: 70.30): ")
                valor = float(valor_str.replace(',', '.'))
                if valor <= 0:
                    print("O valor da despesa deve ser positivo. Tente novamente.")
                else:
                    break
            except ValueError:
                print("Valor inválido. Por favor, insira um número (ex: 70.30 ou 150).")
        categoria = input("Categoria da despesa (ex: Moradia, Alimentação, Lazer): ")

        conn, cursor = conectar_bd()
        try:
            cursor.execute('''
                INSERT INTO transacoes_tb (tipo, descricao, valor, categoria)
                VALUES (?, ?, ?, ?)
            ''', ('despesa', descricao, valor, categoria))
            conn.commit()
            print(f"Despesa '{descricao}' ({categoria}) no valor de R$ {valor:.2f} adicionada com sucesso!")
        except sqlite3.Error as e:
            print(f"Erro ao adicionar despesa ao banco de dados: {e}")
            conn.rollback()
        finally:
            conn.close()

        continuar = input("Deseja adicionar outra despesa? (s/n): ").strip().lower()
        if continuar != 's':
            break

def listar_transacoes():
    conn, cursor = conectar_bd()
    try:
        cursor.execute("SELECT id, tipo, descricao, valor, categoria, data_registro FROM transacoes_tb ORDER BY data_registro DESC, id DESC")
        linhas_db = cursor.fetchall()
        transacoes_lista_dict = [_converter_linha_para_dicionario(linha) for linha in linhas_db]
        _exibir_lista_formatada(transacoes_lista_dict, "Lista de Todas as Transações")
    except sqlite3.Error as e:
        print(f"Erro ao listar transações: {e}")
    finally:
        conn.close()

def ver_saldo():
    print("\n--- Saldo Atual ---")
    saldo = 0.0
    total_ganhos = 0.0
    total_despesas = 0.0

    conn, cursor = conectar_bd()
    try:
        cursor.execute("SELECT tipo, valor FROM transacoes_tb")
        for linha in cursor.fetchall():
            transacao_dict = _converter_linha_para_dicionario(linha)
            if transacao_dict['tipo'] == 'ganho':
                saldo += transacao_dict['valor']
                total_ganhos += transacao_dict['valor']
            elif transacao_dict['tipo'] == 'despesa':
                saldo -= transacao_dict['valor']
                total_despesas += transacao_dict['valor']

        print(f"Total de Ganhos:   R$ {total_ganhos:.2f}")
        print(f"Total de Despesas: R$ {total_despesas:.2f}")
        print("-" * 30)
        if saldo >= 0:
            print(f"Saldo Disponível:  R$ {saldo:.2f}")
        else:
            print(f"Saldo Disponível: -R$ {abs(saldo):.2f} (Negativo)")
        print("-" * 30)
    except sqlite3.Error as e:
        print(f"Erro ao calcular saldo: {e}")
    finally:
        conn.close()

def filtrar_transacoes():
    print("\n--- Filtrar Transações ---")
    conn_check, cursor_check = conectar_bd()
    cursor_check.execute("SELECT COUNT(*) FROM transacoes_tb")
    count = cursor_check.fetchone()[0]
    conn_check.close()

    if count == 0:
        print("\nNenhuma transação registrada para filtrar.")
        return

    print("1. Ver apenas Ganhos")
    print("2. Ver apenas Despesas")
    print("0. Voltar ao Menu Principal")

    while True:
        escolha_filtro = input("Escolha o tipo de transação para filtrar: ")
        sql_query = ""
        titulo_lista = ""

        if escolha_filtro == '1':
            sql_query = "SELECT * FROM transacoes_tb WHERE tipo = 'ganho' ORDER BY data_registro DESC, id DESC"
            titulo_lista = "Ganhos Registrados"
        elif escolha_filtro == '2':
            sql_query = "SELECT * FROM transacoes_tb WHERE tipo = 'despesa' ORDER BY data_registro DESC, id DESC"
            titulo_lista = "Despesas Registradas"
        elif escolha_filtro == '0':
            return
        else:
            print("Opção de filtro inválida. Tente novamente.")
            continue

        conn, cursor = conectar_bd()
        try:
            cursor.execute(sql_query)
            linhas_db = cursor.fetchall()
            transacoes_lista_dict = [_converter_linha_para_dicionario(linha) for linha in linhas_db]
            _exibir_lista_formatada(transacoes_lista_dict, titulo_lista)
            break
        except sqlite3.Error as e:
            print(f"Erro ao filtrar transações: {e}")
            break
        finally:
            conn.close()

def editar_transacao():
    print("\n--- Editar Transação ---")
    listar_transacoes()

    conn_check, cursor_check = conectar_bd()
    cursor_check.execute("SELECT COUNT(*) FROM transacoes_tb")
    count = cursor_check.fetchone()[0]
    conn_check.close()
    if count == 0:
        return

    id_para_editar = None
    while True:
        try:
            id_str = input("Digite o ID da transação que deseja editar (ou 0 para cancelar): ")
            id_para_editar = int(id_str)
            if id_para_editar == 0:
                print("Edição cancelada.")
                return
            break
        except ValueError:
            print("ID inválido. Por favor, insira um número.")

    transacao_atual = _buscar_transacao_por_id(id_para_editar)

    if not transacao_atual:
        print(f"Transação com ID {id_para_editar} não encontrada.")
        return

    print("\nDados atuais da transação:")
    _exibir_lista_formatada([transacao_atual], f"Detalhes da Transação ID {id_para_editar}")

    print("\nDigite os novos valores. Pressione Enter para manter o valor atual.")
    nova_descricao_str = input(f"Nova descrição [{transacao_atual['descricao']}]: ")
    nova_descricao = nova_descricao_str if nova_descricao_str else transacao_atual['descricao']

    novo_valor = transacao_atual['valor']
    while True:
        try:
            novo_valor_str = input(f"Novo valor [{transacao_atual['valor']:.2f}]: ")
            if not novo_valor_str:
                break
            novo_valor_temp = float(novo_valor_str.replace(',', '.'))
            if novo_valor_temp <= 0:
                print("O valor da transação deve ser positivo. Tente novamente.")
            else:
                novo_valor = novo_valor_temp
                break
        except ValueError:
            print("Valor inválido. Por favor, insira um número.")

    nova_categoria = transacao_atual['categoria']
    if transacao_atual['tipo'] == 'despesa':
        nova_categoria_str = input(f"Nova categoria [{transacao_atual['categoria'] or ''}]: ")
        nova_categoria = nova_categoria_str if nova_categoria_str else transacao_atual['categoria']
        if not nova_categoria:
             nova_categoria_input = input("Categoria não pode ser vazia para despesa. Digite a categoria (ou Enter para manter a original, se houver): ")
             nova_categoria = nova_categoria_input if nova_categoria_input else transacao_atual['categoria']
             if not nova_categoria: # Ainda vazia, força algo ou cancela
                 print("Despesa deve ter uma categoria. Edição da categoria cancelada ou definir padrão.")
                 # Poderia forçar um default: nova_categoria = "Outros" ou simplesmente manter a original se existir
                 nova_categoria = transacao_atual['categoria'] if transacao_atual['categoria'] else "Outros"


    print("\n--- Revisão das Alterações ---")
    print(f"Descrição: de '{transacao_atual['descricao']}' para '{nova_descricao}'")
    print(f"Valor: de R$ {transacao_atual['valor']:.2f} para R$ {novo_valor:.2f}")
    if transacao_atual['tipo'] == 'despesa':
        print(f"Categoria: de '{transacao_atual['categoria'] or '-'}' para '{nova_categoria or '-'}'")

    confirmar = input("\nDeseja salvar estas alterações? (s/n): ").strip().lower()
    if confirmar == 's':
        conn, cursor = conectar_bd()
        try:
            cursor.execute('''
                UPDATE transacoes_tb
                SET descricao = ?, valor = ?, categoria = ?
                WHERE id = ?
            ''', (nova_descricao, novo_valor, nova_categoria, id_para_editar))
            conn.commit()
            print("Transação atualizada com sucesso!")
        except sqlite3.Error as e:
            print(f"Erro ao atualizar transação: {e}")
            conn.rollback()
        finally:
            conn.close()
    else:
        print("Alterações descartadas.")

def excluir_transacao():
    """Permite ao usuário excluir uma transação existente."""
    print("\n--- Excluir Transação ---")
    listar_transacoes() # Mostra as transações para o usuário escolher o ID

    conn_check, cursor_check = conectar_bd()
    cursor_check.execute("SELECT COUNT(*) FROM transacoes_tb")
    count = cursor_check.fetchone()[0]
    conn_check.close()
    if count == 0:
        # listar_transacoes já informa, mas podemos retornar aqui.
        return

    id_para_excluir = None
    while True:
        try:
            id_str = input("Digite o ID da transação que deseja excluir (ou 0 para cancelar): ")
            id_para_excluir = int(id_str)
            if id_para_excluir == 0:
                print("Exclusão cancelada.")
                return
            break
        except ValueError:
            print("ID inválido. Por favor, insira um número.")

    transacao_a_excluir = _buscar_transacao_por_id(id_para_excluir)

    if not transacao_a_excluir:
        print(f"Transação com ID {id_para_excluir} não encontrada.")
        return

    print("\nVocê está prestes a excluir a seguinte transação:")
    _exibir_lista_formatada([transacao_a_excluir], f"Detalhes da Transação ID {id_para_excluir}")

    confirmar = input("Tem certeza que deseja excluir esta transação? (s/n): ").strip().lower()

    if confirmar == 's':
        conn, cursor = conectar_bd()
        try:
            cursor.execute("DELETE FROM transacoes_tb WHERE id = ?", (id_para_excluir,))
            conn.commit()
            # Verifica se alguma linha foi realmente afetada/deletada
            if cursor.rowcount > 0:
                print("Transação excluída com sucesso!")
            else:
                # Isso não deveria acontecer se _buscar_transacao_por_id encontrou algo, mas é uma checagem extra
                print(f"Nenhuma transação encontrada com o ID {id_para_excluir} para excluir (pode já ter sido removida).")

        except sqlite3.Error as e:
            print(f"Erro ao excluir transação: {e}")
            conn.rollback()
        finally:
            conn.close()
    else:
        print("Exclusão cancelada pelo usuário.")


def mostrar_menu():
    print("\n--- Controle Financeiro Pessoal ---")
    print("Escolha uma opção:")
    print("1. Adicionar Ganho")
    print("2. Adicionar Despesa")
    print("3. Ver Saldo")
    print("4. Listar Todas as Transações")
    print("5. Filtrar Transações")
    print("6. Editar Transação")
    print("7. Excluir Transação") # Nova opção
    print("0. Sair")

    while True:
        escolha = input("Digite sua opção: ")
        if escolha == '1':
            adicionar_ganho()
            return True
        elif escolha == '2':
            adicionar_despesa()
            return True
        elif escolha == '3':
            ver_saldo()
            return True
        elif escolha == '4':
            listar_transacoes()
            return True
        elif escolha == '5':
            filtrar_transacoes()
            return True
        elif escolha == '6':
            editar_transacao()
            return True
        elif escolha == '7': # Nova opção
            excluir_transacao()
            return True
        elif escolha == '0':
            print("Obrigado por usar o Controle Financeiro. Até logo!")
            return False
        else:
            print("Opção inválida. Por favor, tente novamente.")

def main():
    inicializar_banco_de_dados()
    print("Bem-vindo ao seu Controle Financeiro Pessoal!")
    print(f"Usando banco de dados: {NOME_BANCO_DADOS}")

    while mostrar_menu():
        input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    main()