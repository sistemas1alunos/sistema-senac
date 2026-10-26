from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, make_response
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, uuid
from datetime import datetime
from weasyprint import HTML
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

app = Flask(__name__)
app.secret_key = "senac2026_chave_secreta_super_segura"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ===== USUÁRIOS DO SISTEMA =====
USUARIOS = {
    "eriberto": {"senha": "!Sen@c.E1", "cargo": "Pedagogo Eriberto"},
    "karol": {"senha": "!Sen@c.K2", "cargo": "Psicopedagoga Karoline"},
    "barbara": {"senha": "!Sen@c.B3", "cargo": "Psicóloga Barbara"},
    "eliete": {"senha": "!Sen@c.E4", "cargo": "Inspetora Eliete"},
    "ericasantos": {"senha": "!Sen@c.E5", "cargo": "Apoio de sala Erica"},
    "luciana": {"senha": "!Sen@c.lu", "cargo": "Coordenadora Luciana"},
    "yasnaya": {"senha": "!Sen@c.Yas", "cargo": "Apoio de sala Yasnaya"},
    "erickacristina": {"senha": "!Sen@c.Ec", "cargo": "Coodernadora Erika Cristina"},
    "cayre": {"senha": "!Sen@c.C6", "cargo": " Cayre"}
}
SENHA_GERAL = "!Sen@c"

# ===== CÓDIGOS DAS OCORRÊNCIAS =====
OCORRENCIAS = {
    "F01": {"nome": "Fardamento incorreto/incompleto", "cor": "#1e3a8a"},
    "C01": {"nome": "Uso de celular sem autorização", "cor": "#f97316"},
    "A01": {"nome": "Atraso", "cor": "#f59e0b"},
    "G01": {"nome": "Advertência grave / situação grave", "cor": "#dc2626"},
    "D01": {"nome": "Desrespeito / conflito interpessoal", "cor": "#7c3aed"},
    "B01": {"nome": "Bullying / intimidação", "cor": "#be123c"},
    "P01": {"nome": "Preconceito / discriminação", "cor": "#9f1239"},
    "V01": {"nome": "Violência / ameaça", "cor": "#991b1b"},
    "FQ1": {"nome": "Falta / ausência", "cor": "#475569"},
    "M01": {"nome": "Falta de material / atividade", "cor": "#0891b2"},
    "I01": {"nome": "Indisciplina / interrupção", "cor": "#0d9488"},
    "S01": {"nome": "Saída sem autorização", "cor": "#d97706"},
    "T01": {"nome": "Uso inadequado de equipamento", "cor": "#78350f"},
    "O01": {"nome": "Outro / observação", "cor": "#64748b"},
}
FUNCIONARIOS = [
    "Coordenadora Luciana", "Pedagogo Eriberto",
    "Psicopedagoga Karoline", "Psicóloga Barbara",
    "Apoio de sala Erica", "Apoio de sala Yasnaya",
    "Inspetora Eliete", "Estagiária"
]

# ===== BANCO DE DADOS =====
def init_db():
    db_path = os.path.join(BASE_DIR, "database.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("""CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        turma TEXT NOT NULL,
        turno TEXT NOT NULL,
        foto TEXT,
        data_nascimento TEXT,
        nome_responsavel TEXT,
        telefone_responsavel TEXT,
        especificidade TEXT,
        observacoes_medicas TEXT,
        criado_em TEXT
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS turmas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        turno TEXT NOT NULL,
        qtd_alunos INTEGER NOT NULL
    )""")
    
    c.execute("SELECT COUNT(*) FROM turmas")
    if c.fetchone()[0] == 0:
        turmas_padrao = [
            ("1A", "Manhã", 39), ("1B", "Manhã", 38),
            ("2A", "Tarde", 35), ("2B", "Tarde", 35)
        ]
        c.executemany("INSERT INTO turmas (nome, turno, qtd_alunos) VALUES (?, ?, ?)", turmas_padrao)

    c.execute("""CREATE TABLE IF NOT EXISTS ocorrencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        codigo TEXT NOT NULL,
        descricao TEXT,
        registrado_por TEXT NOT NULL,
        data TEXT NOT NULL,
        excluida INTEGER DEFAULT 0,
        anexo TEXT, 
        FOREIGN KEY(aluno_id) REFERENCES alunos(id)
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT NOT NULL,
        acao TEXT NOT NULL,
        detalhes TEXT,
        data_hora TEXT NOT NULL
    )""")

    # 👇 CORRIGIDO AQUI (Removido o espaço extra no início) 👇
    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        cargo TEXT NOT NULL
    )""")
    
    # Insere os usuários padrão se a tabela estiver vazia
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        usuarios_padrao = [
            ("eriberto", "!Sen@c.E1", "Pedagogo Eriberto"),
            ("karol", "!Sen@c.K2", "Psicopedagoga Karoline"),
            ("barbara", "!Sen@c.B3", "Psicóloga Barbara"),
            ("eliete", "!Sen@c.E4", "Inspetora Eliete"),
            ("ericasantos", "!Sen@c.E5", "Apoio de sala Erica"),
            ("luciana", "!Sen@c.lu", "Coordenadora Luciana"),
            ("yasnaya", "!Sen@c.Yas", "Apoio de sala Yasnaya"),
            ("erickacristina", "!Sen@c.Ec", "Coordenadora Erika Cristina"),
            ("cayre", "!Sen@c.C6", "Cayre")
        ]
        c.executemany("INSERT INTO usuarios (login, senha, cargo) VALUES (?, ?, ?)", usuarios_padrao)
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    db_path = os.path.join(BASE_DIR, "database.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def registrar_log(usuario, acao, detalhes):
    conn = get_db()
    data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
    conn.execute("INSERT INTO logs (usuario, acao, detalhes, data_hora) VALUES (?, ?, ?, ?)",
                 (usuario, acao, detalhes, data_atual))
    conn.commit()
    conn.close()

# ===== MIDDLEWARE DE BLOQUEIO =====
@app.before_request
def proteger():
    rotas_livres = ["login", "static", "logout"]
    if request.endpoint and request.endpoint not in rotas_livres:
        if not session.get("logado"):
            return redirect(url_for("login"))

# ===== ROTAS =====
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        user = request.form.get("usuario", "").strip().lower()
        senha = request.form.get("senha", "")
        
        conn = get_db()
        row = conn.execute("SELECT * FROM usuarios WHERE login = ? AND senha = ?", (user, senha)).fetchone()
        conn.close()
        
        if row:
            session["logado"] = True
            session["usuario_nome"] = row["cargo"]
            return redirect(url_for("dashboard"))
        else:
            erro = "Usuário ou senha incorretos!"
            
    return render_template("login.html", erro=erro)
    
@app.route("/logout")
def logout():
    session.clear()
    return "", 204 

@app.route("/")
def dashboard():
    conn = get_db()
    turmas = [r["turma"] for r in conn.execute("SELECT DISTINCT turma FROM alunos ORDER BY turma")]
    conn.close()
    
    legenda = []
    for k, v in OCORRENCIAS.items():
        legenda.append({"codigo": k, "nome": v["nome"], "cor": v["cor"]})
    
    return render_template(
        "dashboard.html", 
        turmas=turmas, 
        funcionarios=FUNCIONARIOS, 
        ocorrencias=OCORRENCIAS,
        legenda=legenda
    )

# ===== API ALUNOS =====
@app.route("/api/alunos")
def api_alunos():
    conn = get_db()
    turma = request.args.get("turma", "")
    busca = request.args.get("busca", "").strip()
    turno = request.args.get("turno", "").strip()

    sql = """
        SELECT a.*, COUNT(o.id) as total_ocorrencias 
        FROM alunos a
        LEFT JOIN ocorrencias o ON a.id = o.aluno_id AND o.excluida = 0
        WHERE 1=1
    """
    params = []
    
    if turma:
        sql += " AND a.turma = ?"
        params.append(turma)
    if turno:
        sql += " AND a.turno = ?"
        params.append(turno)
    if busca:
        sql += " AND a.nome LIKE ?"
        params.append(f"%{busca}%")
        
    sql += " GROUP BY a.id ORDER BY a.nome"
    
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/alunos", methods=["POST"])
def cadastrar_aluno():
    nome = request.form.get("nome", "").strip()
    turma = request.form.get("turma", "").strip().upper()
    turno = request.form.get("turno", "").strip()
    foto = request.files.get("foto")

    if not nome or not turma or not turno:
        return jsonify({"erro": "Preencha todos os campos"}), 400

    foto_nome = None
    if foto and foto.filename:
        ext = os.path.splitext(foto.filename)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".webp"]:
            foto_nome = f"{uuid.uuid4().hex}{ext}"
            foto.save(os.path.join(app.config["UPLOAD_FOLDER"], foto_nome))

    conn = get_db()
    conn.execute("INSERT INTO alunos (nome, turma, turno, foto, criado_em) VALUES (?,?,?,?,?)",
                 (nome, turma, turno, foto_nome, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    registrar_log(session.get("usuario_nome"), "Cadastrar Aluno", f"Cadastrou o aluno {nome} na turma {turma}.")
    
    return jsonify({"ok": True})

@app.route("/api/alunos/<int:aid>", methods=["DELETE"])
def excluir_aluno(aid):
    conn = get_db()
    conn.execute("DELETE FROM ocorrencias WHERE aluno_id = ?", (aid,))
    conn.execute("DELETE FROM alunos WHERE id = ?", (aid,))
    conn.commit()
    conn.close()
    
    registrar_log(session.get("usuario_nome"), "Excluir Aluno", f"Apagou o aluno ID {aid} e suas ocorrências.")
    
    return jsonify({"ok": True})

@app.route("/aluno/<int:aid>")
def pagina_aluno(aid):
    return render_template("aluno.html")

@app.route("/api/alunos/<int:aid>", methods=["GET"])
def get_aluno(aid):
    conn = get_db()
    row = conn.execute("SELECT * FROM alunos WHERE id = ?", (aid,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"erro": "Aluno não encontrado"}), 404
    return jsonify(dict(row))

@app.route("/api/alunos/<int:aid>", methods=["PUT"])
def atualizar_aluno(aid):
    data = request.get_json()
    conn = get_db()
    
    conn.execute("""UPDATE alunos SET 
        nome=?, turma=?, turno=?,
        data_nascimento=?, nome_responsavel=?, telefone_responsavel=?, 
        especificidade=?, observacoes_medicas=? WHERE id=?""",
        (data.get("nome"), data.get("turma"), data.get("turno"),
         data.get("data_nascimento", ""), data.get("nome_responsavel", ""), 
         data.get("telefone_responsavel", ""), data.get("especificidade", ""), 
         data.get("observacoes_medicas", ""), aid))
    
    conn.commit()
    conn.close()
    registrar_log(session.get("usuario_nome"), "Editar Aluno", f"Editou os dados do aluno ID {aid}.")

    return jsonify({"ok": True})

# ===== API OCORRÊNCIAS =====
@app.route("/api/ocorrencias", methods=["POST"])
def registrar_ocorrencia():
    aluno_id = request.form.get("aluno_id")
    codigo = request.form.get("codigo")
    descricao = request.form.get("descricao", "")
    data_manual = request.form.get("data")
    hora_manual = request.form.get("hora", "")
    anexo = request.files.get("anexo")
    
    if data_manual:
        data_formatada = f"{data_manual} às {hora_manual}" if hora_manual else data_manual
    else:
        data_formatada = datetime.now().strftime("%d/%m/%Y às %H:%M")

    anexo_nome = None
    if anexo and anexo.filename:
        ext = os.path.splitext(anexo.filename)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".webp", ".pdf"]:
            anexo_nome = f"{uuid.uuid4().hex}{ext}"
            anexo.save(os.path.join(app.config["UPLOAD_FOLDER"], anexo_nome))
        
    conn = get_db()
    conn.execute("""INSERT INTO ocorrencias 
        (aluno_id, codigo, descricao, registrado_por, data, anexo)
        VALUES (?,?,?,?,?,?)""",
        (aluno_id, codigo, descricao,
         session.get("usuario_nome", "Desconhecido"), data_formatada, anexo_nome))
    
    conn.commit()
    conn.close()
    return jsonify({"ok": True})
    
@app.route("/api/ocorrencias/<int:aluno_id>")
def listar_ocorrencias(aluno_id):
    conn = get_db()
    rows = conn.execute("""SELECT * FROM ocorrencias WHERE aluno_id = ? AND excluida = 0
                           ORDER BY id DESC""", (aluno_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ===== API TURMAS =====
@app.route("/api/turmas", methods=["GET"])
def api_turmas():
    conn = get_db()
    rows = conn.execute("SELECT * FROM turmas ORDER BY nome").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/turmas/<int:tid>", methods=["PUT"])
def editar_turma(tid):
    data = request.get_json()
    conn = get_db()
    conn.execute("UPDATE turmas SET turno=?, qtd_alunos=? WHERE id=?", 
                 (data["turno"], data["qtd_alunos"], tid))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/turmas", methods=["POST"])
def criar_turma():
    data = request.get_json()
    nome = data.get("nome", "").strip().upper()
    qtd = data.get("qtd_alunos")
    
    if not nome or not qtd:
        return jsonify({"erro": "Preencha todos os campos"}), 400

    if not (nome.endswith('A') or nome.endswith('B')):
        return jsonify({"erro": "A turma deve terminar com A (Manhã) ou B (Tarde). Ex: 1A, 2B."}), 400

    if nome.endswith('A'):
        turno = "Manhã"
    else:
        turno = "Tarde"
        
    try:
        conn = get_db()
        conn.execute("INSERT INTO turmas (nome, turno, qtd_alunos) VALUES (?, ?, ?)", (nome, turno, qtd))
        conn.commit()
        conn.close()
        
        registrar_log(session.get("usuario_nome"), "Criar Turma", f"Criou a turma {nome} ({turno}).")
        
        return jsonify({"ok": True})
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Essa turma já está cadastrada!"}), 400

@app.route("/api/turmas/<int:tid>", methods=["DELETE"])
def deletar_turma(tid):
    conn = get_db()
    turma = conn.execute("SELECT nome FROM turmas WHERE id = ?", (tid,)).fetchone() 
    nome_turma = turma['nome'] if turma else "Desconhecida"
    
    conn.execute("DELETE FROM turmas WHERE id = ?", (tid,))
    conn.commit()
    conn.close()
    
    registrar_log(session.get("usuario_nome"), "Excluir Turma", f"Apagou a turma {nome_turma}.")
    
    return jsonify({"ok": True})

# ===== ROTA PARA FINALIZAR ANO (PROGRESSÃO) =====
@app.route("/api/finalizar_ano", methods=["POST"])
def finalizar_ano():
    data = request.get_json()
    aprovados = data.get("aprovados", [])
    
    conn = get_db()
    
    for aid in aprovados:
        aluno = conn.execute("SELECT turma FROM alunos WHERE id = ?", (aid,)).fetchone()
        if aluno:
            num_atual = int(aluno['turma'][0]) if aluno['turma'][0].isdigit() else 1
            letra = aluno['turma'][1:] if len(aluno['turma']) > 1 else ""
            if num_atual < 3:
                novo_nome = f"{num_atual + 1}{letra}"
                conn.execute("UPDATE alunos SET turma = ? WHERE id = ?", (novo_nome, aid))
            else:
                conn.execute("UPDATE alunos SET turma = 'FORMADO' WHERE id = ?", (aid,))
    
    conn.commit()
    conn.close()
    
    registrar_log(session.get("usuario_nome"), "Finalizar Ano", f"Finalizou o ano letivo para {len(aprovados)} alunos aprovados.")
    
    return jsonify({"ok": True})

# ===== ROTA PARA O MURAL GERAL =====
@app.route("/api/todas_ocorrencias")
def todas_ocorrencias():
    conn = get_db()
    turma = request.args.get("turma", "")
    aluno = request.args.get("aluno", "")
    data_ini = request.args.get("data_ini", "")
    
    sql = """
        SELECT o.*, a.nome as aluno_nome, a.turma as aluno_turma 
        FROM ocorrencias o
        JOIN alunos a ON o.aluno_id = a.id
        WHERE o.excluida = 0
    """
    params = []
    if turma:
        sql += " AND a.turma = ?"
        params.append(turma)
    if aluno:
        sql += " AND a.nome LIKE ?"
        params.append(f"%{aluno}%")
    if data_ini:
        sql += " AND o.data >= ?"
        params.append(data_ini)
        
    sql += " ORDER BY o.id DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ===== ROTA PARA O PDF =====
@app.route("/api/relatorio_pdf")
def gerar_relatorio_pdf():
    conn = get_db()
    sql = """
        SELECT o.*, a.nome as aluno_nome, a.turma as aluno_turma, a.turno 
        FROM ocorrencias o
        JOIN alunos a ON o.aluno_id = a.id
        WHERE o.excluida = 0
        ORDER BY o.id DESC
    """
    rows = conn.execute(sql).fetchall()
    conn.close()

    quem_emitiu = session.get("usuario_nome", "Sistema")

    html_content = """
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: Helvetica, Arial, sans-serif; color: #333; }
            h1 { color: #0a1f44; border-bottom: 2px solid #f97316; padding-bottom: 10px; }
            .header { margin-bottom: 30px; }
            .data { font-size: 12px; color: #666; margin-bottom: 20px; }
            .item { border-left: 4px solid #f97316; padding-left: 15px; margin-bottom: 20px; page-break-inside: avoid; }
            .item h3 { margin: 0 0 5px 0; color: #0a1f44; font-size: 16px; }
            .item p { margin: 3px 0; font-size: 13px; }
            .codigo { font-weight: bold; color: #dc2626; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏫 SENAC 2026 - Relatório de Ocorrências</h1>
            <div class="data">
                Emitido em: """ + datetime.now().strftime('%d/%m/%Y às %H:%M') + """ <br>
                <strong>Emitido por:</strong> """ + quem_emitiu + """
            </div>
        </div>
    """

    if not rows:
        html_content += "<p>Nenhuma ocorrência registrada até o momento.</p>"
    else:
        for row in rows:
            html_content += f"""
            <div class="item">
                <h3>{row['aluno_nome']} - Turma {row['aluno_turma']} ({row['turno']})</h3>
                <p><span class="codigo">Código: {row['codigo']}</span> | Data: {row['data']} | Registrado por: {row['registrado_por']}</p>
                {f"<p><strong>Obs:</strong> {row['descricao']}</p>" if row['descricao'] else ""}
            </div>
            """
    
    html_content += "</body></html>"

    pdf_bytes = HTML(string=html_content).write_pdf()

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=relatorio_senac.pdf'
    return response

# ===== ROTA PARA BAIXAR BACKUP DO BANCO =====
@app.route("/api/backup")
def backup_db():
    db_path = os.path.join(BASE_DIR, "database.db")
    
    if not os.path.exists(db_path):
        return "Banco de dados não encontrado.", 404
        
    return send_from_directory(
        directory=BASE_DIR, 
        path="database.db", 
        as_attachment=True, 
        download_name=f"backup_senac_{datetime.now().strftime('%d_%m_%Y')}.db"
    )

# ===== ROTA PARA ESTATÍSTICAS (GRÁFICOS) =====
@app.route("/api/estatisticas")
def estatisticas():
    conn = get_db()
    
    sql_turmas = """
        SELECT a.turma, COUNT(o.id) as total 
        FROM ocorrencias o
        JOIN alunos a ON o.aluno_id = a.id
        WHERE o.excluida = 0
        GROUP BY a.turma
        ORDER BY total DESC
    """
    dados_turmas = conn.execute(sql_turmas).fetchall()
    
    sql_codigos = """
        SELECT codigo, COUNT(id) as total 
        FROM ocorrencias 
        WHERE excluida = 0
        GROUP BY codigo
        ORDER BY total DESC
    """
    dados_codigos = conn.execute(sql_codigos).fetchall()
    
    conn.close()
    
    return jsonify({
        "turmas": [dict(r) for r in dados_turmas],
        "codigos": [dict(r) for r in dados_codigos]
    })

# ===== LIXEIRA =====
@app.route("/api/ocorrencias/<int:oid>", methods=["DELETE"])
def mover_para_lixeira(oid):
    conn = get_db()
    conn.execute("UPDATE ocorrencias SET excluida = 1 WHERE id = ?", (oid,))
    conn.commit()
    conn.close()
    registrar_log(session.get("usuario_nome"), "Lixeira", f"Moveu a ocorrência ID {oid} para a lixeira.")
    return jsonify({"ok": True})

@app.route("/api/lixeira", methods=["GET"])
def listar_lixeira():
    conn = get_db()
    sql = """
        SELECT o.*, a.nome as aluno_nome FROM ocorrencias o
        JOIN alunos a ON o.aluno_id = a.id
        WHERE o.excluida = 1 ORDER BY o.id DESC
    """
    rows = conn.execute(sql).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/lixeira/limpar", methods=["DELETE"])
def limpar_lixeira():
    conn = get_db()
    conn.execute("DELETE FROM ocorrencias WHERE excluida = 1")
    conn.commit()
    conn.close()
    registrar_log(session.get("usuario_nome"), "Limpar Lixeira", "Esvaziou a lixeira de ocorrências.")
    return jsonify({"ok": True})

@app.route("/api/ocorrencias/<int:oid>/restaurar", methods=["PUT"])
def restaurar_ocorrencia(oid):
    conn = get_db()
    conn.execute("UPDATE ocorrencias SET excluida = 0 WHERE id = ?", (oid,))
    conn.commit()
    conn.close()
    registrar_log(session.get("usuario_nome"), "Restaurar Ocorrência", f"Restaurou a ocorrência ID {oid} da lixeira.")
    return jsonify({"ok": True})

# ===== ROTA PARA EXPORTAR EXCEL =====
@app.route("/api/relatorio_excel")
def exportar_excel():
    conn = get_db()
    sql = """
        SELECT o.*, a.nome as aluno_nome, a.turma as aluno_turma, a.turno 
        FROM ocorrencias o
        JOIN alunos a ON o.aluno_id = a.id
        WHERE o.excluida = 0
        ORDER BY o.id DESC
    """
    rows = conn.execute(sql).fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Ocorrências Senac"

    cor_cabecalho = PatternFill(start_color="0A1F44", end_color="0A1F44", fill_type="solid")
    cor_titulo = Font(color="FFFFFF", bold=True, size=12)
    
    cabecalhos = ["Data", "Aluno", "Turma", "Turno", "Código", "Descrição", "Registrado Por"]
    ws.append(cabecalhos)

    for cell in ws[1]:
        cell.fill = cor_cabecalho
        cell.font = cor_titulo
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for row in rows:
        ws.append([
            row['data'], row['aluno_nome'], row['aluno_turma'], 
            row['turno'], row['codigo'], row['descricao'], row['registrado_por']
        ])

    larguras = [18, 30, 10, 12, 10, 40, 25]
    for i, coluna in enumerate(larguras, start=1):
        ws.column_dimensions[chr(64 + i)].width = coluna

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename=relatorio_senac_{datetime.now().strftime("%d_%m_%Y")}.xlsx'
    return response

# ===== ROTA PARA VER OS LOGS =====
@app.route("/api/logs")
def api_logs():
    conn = get_db()
    rows = conn.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])



@app.route("/api/trocar_senha", methods=["POST"])
def trocar_senha():
    data = request.get_json()
    login = data.get("login", "").strip().lower()
    senha_atual = data.get("senha_atual", "")
    nova_senha = data.get("nova_senha", "")

    conn = get_db()
    user = conn.execute("SELECT * FROM usuarios WHERE login = ? AND senha = ?", (login, senha_atual)).fetchone()
    
    if user:
        conn.execute("UPDATE usuarios SET senha = ? WHERE login = ?", (nova_senha, login))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "msg": "Senha alterada com sucesso!"})
    else:
        conn.close()
        return jsonify({"erro": "Login ou senha atual incorretos."}), 400



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
