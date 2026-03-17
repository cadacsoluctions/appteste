import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import os

# ---------------- CONFIGURAÇÃO INICIAL ----------------
st.set_page_config(page_title="Cadac ERP Pro", layout="wide", page_icon="🚀")

# Conexão com o banco
conn = sqlite3.connect("loja.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    # TABELA DE USUÁRIOS (Essencial para o login)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            usuario TEXT UNIQUE, 
            senha TEXT
        )
    """)
    cursor.execute("CREATE TABLE IF NOT EXISTS empresa(id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, dono TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS produtos(id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, preco REAL, custo REAL, estoque INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS clientes(id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT, email TEXT, aniversario TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS fornecedores(id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT, email TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS contas(id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, fornecedor TEXT, descricao TEXT, valor REAL, vencimento TEXT, pago INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS vendas(id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, produto TEXT, quantidade INTEGER, valor REAL, pagamento TEXT, data TEXT)")
    conn.commit()

# Executa a criação das tabelas logo no início
init_db()

# Lógica para definir qual logo usar
if os.path.exists("logo_usuario.png"):
    LOGO_PATH = "logo_usuario.png"
elif os.path.exists("logo.png"):
    LOGO_PATH = "logo.png"
else:
    LOGO_PATH = None

# --- CONTROLE DE SESSÃO ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# --- TELA DE ACESSO (LOGIN E CADASTRO) ---
def tela_acesso():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if LOGO_PATH:
            st.image(LOGO_PATH, width=150)
            
        aba_login, aba_cadastro = st.tabs(["Entrar", "Criar Conta"])

        with aba_login:
            with st.form("form_login"):
                u = st.text_input("Usuário")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("Acessar"):
                    user_db = pd.read_sql(f"SELECT * FROM usuarios WHERE usuario='{u}' AND senha='{s}'", conn)
                    if not user_db.empty:
                        st.session_state["autenticado"] = True
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos")

        with aba_cadastro:
            with st.form("form_cadastro"):
                novo_u = st.text_input("Escolha um Usuário")
                novo_s = st.text_input("Escolha uma Senha", type="password")
                confirma_s = st.text_input("Confirme a Senha", type="password")
                
                if st.form_submit_button("Cadastrar"):
                    if novo_u and novo_s:
                        if novo_s == confirma_s:
                            try:
                                cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", (novo_u, novo_s))
                                conn.commit()
                                st.success(f"Conta '{novo_u}' criada! Vá para a aba 'Entrar'.")
                            except sqlite3.IntegrityError:
                                st.error("Este nome de usuário já existe.")
                            except Exception as e:
                                st.error(f"Erro no banco: {e}")
                        else:
                            st.error("As senhas não coincidem.")
                    else:
                        st.error("Preencha todos os campos.")

# --- TRAVA DE SEGURANÇA ---
if not st.session_state["autenticado"]:
    tela_acesso()
    st.stop()

# ---------------- FUNÇÃO PDF COM LOGO ----------------
def gerar_comprovante(empresa, cliente, produto, valor, pagamento):
    nome_arquivo = f"comprovante_{datetime.now().strftime('%H%M%S')}.pdf"
    doc = SimpleDocTemplate(nome_arquivo, pagesize=A4)
    styles = getSampleStyleSheet()
    conteudo = []

    if LOGO_PATH:
        img = Image(LOGO_PATH, 1.5*inch, 1.5*inch)
        conteudo.append(img)
    
    conteudo.append(Paragraph(f"<b>{empresa.upper()}</b>", styles["Title"]))
    conteudo.append(Spacer(1, 12))
    conteudo.append(Paragraph(f"<b>COMPROVANTE DE VENDA</b>", styles["Heading2"]))
    conteudo.append(Paragraph("-" * 80, styles["Normal"]))
    conteudo.append(Paragraph(f"<b>CLIENTE:</b> {cliente}", styles["Normal"]))
    conteudo.append(Paragraph(f"<b>PRODUTO:</b> {produto}", styles["Normal"]))
    conteudo.append(Paragraph(f"<b>VALOR TOTAL:</b> R$ {valor:.2f}", styles["Normal"]))
    conteudo.append(Paragraph(f"<b>DATA:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    conteudo.append(Paragraph("-" * 80, styles["Normal"]))
    
    doc.build(conteudo)
    return nome_arquivo

# ---------------- ONBOARDING (CONFIG EMPRESA) ----------------
try:
    empresa_df = pd.read_sql("SELECT * FROM empresa", conn)
    empresa_nome = empresa_df.iloc[0]["nome"] if not empresa_df.empty else None
except:
    empresa_nome = None

if not empresa_nome:
    st.title("🚀 Configuração Inicial")
    with st.form("config_inicial"):
        n = st.text_input("Nome da Empresa")
        d = st.text_input("Nome do Proprietário")
        if st.form_submit_button("Finalizar"):
            if n and d:
                cursor.execute("INSERT INTO empresa(nome, dono) VALUES (?,?)", (n, d))
                conn.commit()
                st.rerun()
    st.stop()

# ---------------- MENU LATERAL ----------------
st.sidebar.title(f"🏢 {empresa_nome}")
if st.sidebar.button("Sair / Logout"):
    st.session_state["autenticado"] = False
    st.rerun()

menu = st.sidebar.radio("Navegação", [
    "Dashboard", "Produtos", "Clientes", "Fornecedores", "Vendas", "Financeiro", "Relatórios"
])

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.title("📊 Painel de Controle")
    vendas_df = pd.read_sql("SELECT * FROM vendas", conn)
    contas_df = pd.read_sql("SELECT * FROM contas WHERE pago=0", conn)
    
    c1, c2, c3 = st.columns(3)
    faturamento = vendas_df['valor'].sum() if not vendas_df.empty else 0.0
    a_pagar = contas_df['valor'].sum() if not contas_df.empty else 0.0
    
    c1.metric("Faturamento Total", f"R$ {faturamento:,.2f}")
    c2.metric("Contas a Pagar", f"R$ {a_pagar:,.2f}")
    c3.metric("Vendas Realizadas", len(vendas_df))

# ---------------- PRODUTOS ----------------
if menu == "Produtos":
    st.header("📦 Estoque de Produtos")
    tab1, tab2 = st.tabs(["Cadastrar Novo", "Lista e Edição Completa"])
    
    with tab1:
        with st.form("cad_prod"):
            pn = st.text_input("Nome do Produto")
            pc = st.number_input("Preço de Custo (R$)", min_value=0.0)
            pv = st.number_input("Preço de Venda (R$)", min_value=0.0)
            pe = st.number_input("Estoque Inicial", min_value=0, step=1)
            if st.form_submit_button("Salvar Produto"):
                cursor.execute("INSERT INTO produtos(nome, preco, custo, estoque) VALUES (?,?,?,?)", (pn, pv, pc, pe))
                conn.commit()
                st.success(f"Produto {pn} cadastrado!")
                st.rerun()

    with tab2:
        df_p = pd.read_sql("SELECT * FROM produtos", conn)
        busca_p = st.text_input("🔍 Pesquisar produto pelo nome")
        if busca_p:
            df_p = df_p[df_p['nome'].str.contains(busca_p, case=False, na=False)]
        
        st.dataframe(df_p, use_container_width=True)
        
        if not df_p.empty:
            st.divider()
            p_id = st.selectbox("Selecione o ID do Produto para editar", df_p["id"])
            p_atual = df_p[df_p['id'] == p_id].iloc[0]
            
            with st.form("edit_prod_completo"):
                en = st.text_input("Alterar Nome", value=p_atual['nome'])
                ec = st.number_input("Alterar Custo", value=float(p_atual['custo']))
                ev = st.number_input("Alterar Venda", value=float(p_atual['preco']))
                ee = st.number_input("Ajustar Estoque", value=int(p_atual['estoque']))
                
                c_b1, c_b2 = st.columns(2)
                if c_b1.form_submit_button("Atualizar Produto"):
                    cursor.execute("UPDATE produtos SET nome=?, custo=?, preco=?, estoque=? WHERE id=?", (en, ec, ev, ee, p_id))
                    conn.commit()
                    st.rerun()
                if c_b2.form_submit_button("Excluir Produto"):
                    cursor.execute("DELETE FROM produtos WHERE id=?", (p_id,))
                    conn.commit()
                    st.rerun()

# ---------------- CLIENTES ----------------
if menu == "Clientes":
    st.header("👥 Gestão de Clientes")
    tab1, tab2 = st.tabs(["Cadastrar Cliente", "Lista e Edição"])
    
    with tab1:
        with st.form("cad_cli"):
            cn = st.text_input("Nome Completo")
            ct = st.text_input("Telefone")
            ce = st.text_input("E-mail")
            ca = st.date_input("Data de Nascimento", value=date(2000,1,1),min_value=date(1920, 1, 1), # Permite selecionar desde 1920
    max_value=date.today(), format="DD/MM/YYYY")
            if st.form_submit_button("Salvar Cadastro"):
                cursor.execute("INSERT INTO clientes(nome, telefone, email, aniversario) VALUES (?,?,?,?)", (cn, ct, ce, str(ca)))
                conn.commit()
                st.rerun()

    with tab2:
        df_c = pd.read_sql("SELECT * FROM clientes", conn)
        busca_c = st.text_input("🔍 Pesquisar cliente pelo nome")
        if busca_c:
            df_c = df_c[df_c['nome'].str.contains(busca_c, case=False, na=False)]
            
        if not df_c.empty:
            df_c['aniversario'] = pd.to_datetime(df_c['aniversario']).dt.strftime('%d/%m/%Y')
            st.dataframe(df_c, use_container_width=True)
            
            st.divider()
            c_id = st.selectbox("Selecione o ID para Editar", df_c["id"])
            c_raw = pd.read_sql(f"SELECT * FROM clientes WHERE id={c_id}", conn).iloc[0]
            
            with st.form("edit_cli"):
                en = st.text_input("Nome", value=c_raw['nome'])
                et = st.text_input("Telefone", value=c_raw['telefone'])
                ee = st.text_input("E-mail", value=c_raw['email'])
                ea = st.date_input("Nascimento", value=datetime.strptime(c_raw['aniversario'], '%Y-%m-%d').date(), format="DD/MM/YYYY")
                
                col1, col2 = st.columns(2)
                if col1.form_submit_button("Atualizar"):
                    cursor.execute("UPDATE clientes SET nome=?, telefone=?, email=?, aniversario=? WHERE id=?", (en, et, ee, str(ea), c_id))
                    conn.commit()
                    st.rerun()
                if col2.form_submit_button("🗑️ Excluir"):
                    cursor.execute("DELETE FROM clientes WHERE id=?", (c_id,))
                    conn.commit()
                    st.rerun()

# ---------------- FORNECEDORES ----------------
if menu == "Fornecedores":
    st.header("🏭 Fornecedores")
    tab1, tab2 = st.tabs(["Cadastrar", "Lista e Edição"])
    with tab1:
        with st.form("cad_forn"):
            fn = st.text_input("Nome/Empresa")
            ft = st.text_input("Telefone")
            fe = st.text_input("E-mail")
            if st.form_submit_button("Salvar"):
                cursor.execute("INSERT INTO fornecedores(nome, telefone, email) VALUES (?,?,?)", (fn, ft, fe))
                conn.commit()
                st.rerun()
    with tab2:
        df_f = pd.read_sql("SELECT * FROM fornecedores", conn)
        st.dataframe(df_f, use_container_width=True)
        if not df_f.empty:
            f_id = st.selectbox("ID Fornecedor", df_f["id"])
            f_at = df_f[df_f['id'] == f_id].iloc[0]
            with st.form("edit_f"):
                en = st.text_input("Nome", value=f_at['nome'])
                et = st.text_input("Telefone", value=f_at['telefone'])
                ee = st.text_input("E-mail", value=f_at['email'])
                if st.form_submit_button("Atualizar"):
                    cursor.execute("UPDATE fornecedores SET nome=?, telefone=?, email=? WHERE id=?", (en, et, ee, f_id))
                    conn.commit()
                    st.rerun()

# ---------------- VENDAS ----------------
if menu == "Vendas":
    st.header("🛒 Ponto de Venda (PDV)")
    df_p = pd.read_sql("SELECT * FROM produtos", conn)
    df_c = pd.read_sql("SELECT * FROM clientes", conn)
    
    if df_p.empty:
        st.warning("Cadastre produtos antes de vender!")
    else:
        col_v1, col_v2 = st.columns(2)
        
        with col_v1:
            p_sel = st.selectbox("Escolha o Produto", df_p["nome"])
            c_sel = st.selectbox("Cliente", df_c["nome"] if not df_c.empty else ["Consumidor Final"])
            qtd = st.number_input("Quantidade", min_value=1, step=1)
        
        with col_v2:
            forma_pg = st.selectbox("Forma de Pagamento", ["Pix", "Dinheiro", "Cartão"])
            # Novo campo de desconto
            tipo_desconto = st.radio("Tipo de Desconto", ["R$ (Valor)", "% (Porcentagem)"], horizontal=True)
            valor_desc = st.number_input("Valor do Desconto", min_value=0.0, step=0.5)

        # LÓGICA DE CÁLCULO
        preco_unit = df_p[df_p['nome']==p_sel]['preco'].iloc[0]
        subtotal = preco_unit * qtd
        
        if tipo_desconto == "% (Porcentagem)":
            total_desconto = (subtotal * valor_desc) / 100
        else:
            total_desconto = valor_desc
            
        v_total_final = subtotal - total_desconto
        
        # Exibição dos valores para conferência
        st.divider()
        c_res1, c_res2, c_res3 = st.columns(3)
        c_res1.write(f"**Subtotal:** R$ {subtotal:.2f}")
        c_res2.write(f"**Desconto aplicado:** - R$ {total_desconto:.2f}")
        c_res3.subheader(f"Total: R$ {max(0.0, v_total_final):.2f}") # max garante que não fique negativo

        if st.button("Finalizar Venda e Gerar Comprovante"):
            if v_total_final < 0:
                st.error("O desconto não pode ser maior que o valor da venda!")
            else:
                # Salvamos o valor final já com desconto no banco
                cursor.execute("INSERT INTO vendas(cliente, produto, quantidade, valor, pagamento, data) VALUES (?,?,?,?,?,?)", 
                               (c_sel, p_sel, qtd, v_total_final, forma_pg, datetime.now().isoformat()))
                
                # Baixa no estoque
                cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE nome=?", (qtd, p_sel))
                conn.commit()
                
                # Gera o PDF com o valor final
                pdf_path = gerar_comprovante(empresa_nome, c_sel, p_sel, v_total_final, forma_pg)
                with open(pdf_path, "rb") as f:
                    st.download_button("📥 Baixar Comprovante PDF", f, file_name=pdf_path)
                st.success(f"Venda de R$ {v_total_final:.2f} registrada com sucesso!")

# ---------------- FINANCEIRO ----------------
if menu == "Financeiro":
    st.header("💰 Gestão Financeira")
    with st.form("financeiro_form"):
        cat = st.selectbox("Categoria", ["Fornecedor", "Luz", "Aluguel", "Outros"])
        f_nome = "N/A"
        if cat == "Fornecedor":
            df_forn = pd.read_sql("SELECT nome FROM fornecedores", conn)
            if not df_forn.empty:
                f_nome = st.selectbox("Selecione o Fornecedor", df_forn["nome"])
            else:
                st.warning("Nenhum fornecedor cadastrado.")
        
        desc = st.text_input("Descrição da Conta")
        v_tot = st.number_input("Valor Total (R$)", min_value=0.0)
        parc = st.number_input("Quantidade de Parcelas", min_value=1, value=1)
        venc = st.date_input("Vencimento da 1ª Parcela", format="DD/MM/YYYY")
        
        if st.form_submit_button("Lançar Contas"):
            v_p = v_tot / parc
            for i in range(parc):
                dt = venc + timedelta(days=i*30)
                cursor.execute("INSERT INTO contas(tipo, fornecedor, descricao, valor, vencimento) VALUES (?,?,?,?,?)", 
                               (cat, f_nome, f"{desc} ({i+1}/{parc})", v_p, dt.isoformat()))
            conn.commit()
            st.success("Lançamento realizado!")
            st.rerun()
            
    st.subheader("Contas Pendentes")
    df_a = pd.read_sql("SELECT * FROM contas WHERE pago=0", conn)
    if not df_a.empty:
        df_a['vencimento'] = pd.to_datetime(df_a['vencimento']).dt.strftime('%d/%m/%Y')
        st.dataframe(df_a, use_container_width=True)
        id_b = st.selectbox("ID para Baixa", df_a["id"])
        if st.button("Confirmar Pagamento"):
            cursor.execute("UPDATE contas SET pago=1 WHERE id=?", (id_b,))
            conn.commit()
            st.rerun()

# ---------------- RELATÓRIOS ----------------
if menu == "Relatórios":
    st.header("📊 Relatórios Gerenciais")
    opcao_rel = st.selectbox("Escolha o Relatório", 
                            ["Vendas Realizadas", "Rotatividade de Estoque", "Contas a Pagar/Pagas", "Aniversariantes"])
    
    if opcao_rel == "Vendas Realizadas":
        df_v = pd.read_sql("SELECT * FROM vendas", conn)
        if not df_v.empty:
            df_v['data'] = pd.to_datetime(df_v['data']).dt.strftime('%d/%m/%Y %H:%M')
            st.dataframe(df_v, use_container_width=True)

    elif opcao_rel == "Rotatividade de Estoque":
        query = """
            SELECT p.nome as 'Produto', p.estoque as 'Em Estoque', SUM(v.quantidade) as 'Total Vendido'
            FROM produtos p
            LEFT JOIN vendas v ON p.nome = v.produto
            GROUP BY p.nome
            ORDER BY SUM(v.quantidade) DESC
        """
        df_rot = pd.read_sql(query, conn)
        df_rot['Total Vendido'] = df_rot['Total Vendido'].fillna(0).astype(int)
        st.dataframe(df_rot, use_container_width=True)

    elif opcao_rel == "Contas a Pagar/Pagas":
        status = st.radio("Filtrar por:", ["Pendentes", "Pagas", "Todas"], horizontal=True)
        q = "SELECT * FROM contas WHERE pago=0" if status == "Pendentes" else "SELECT * FROM contas WHERE pago=1" if status == "Pagas" else "SELECT * FROM contas"
        df_c_rel = pd.read_sql(q, conn)
        if not df_c_rel.empty:
            df_c_rel['vencimento'] = pd.to_datetime(df_c_rel['vencimento']).dt.strftime('%d/%m/%Y')
            st.dataframe(df_c_rel, use_container_width=True)

    elif opcao_rel == "Aniversariantes":
        mes = date.today().month
        df_cli = pd.read_sql("SELECT * FROM clientes", conn)
        if not df_cli.empty:
            df_cli['aniversario_dt'] = pd.to_datetime(df_cli['aniversario'])
            filtro = df_cli[df_cli['aniversario_dt'].dt.month == mes].copy()
            if not filtro.empty:
                filtro['aniversario'] = filtro['aniversario_dt'].dt.strftime('%d/%m/%Y')
                st.dataframe(filtro[['nome', 'telefone', 'aniversario']], use_container_width=True)