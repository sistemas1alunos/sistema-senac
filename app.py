from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "senac2026_chave_secreta_super_segura"

# CAMINHO CORRIGIDO PARA O PYTHONANYWHERE (Não apague o "sistemaalun0s")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

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
    # Garante que o banco fique na mesma pasta do app.py
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
    
    # Insere as turmas padrão se a tabela estiver vazia
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
        FOREIGN KEY(aluno_id) REFERENCES alunos(id)
    )""")
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    db_path = os.path.join(BASE_DIR, "database.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

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
        if request.form.get("senha") == SENHA_GERAL:
            session["logado"] = True
            return redirect(url_for("dashboard"))
        erro = "Senha incorreta!"
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
        LEFT JOIN ocorrencias o ON a.id = o.aluno_id
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
            # O app.config pega o caminho absoluto correto agora
            foto.save(os.path.join(app.config["UPLOAD_FOLDER"], foto_nome))

    conn = get_db()
    conn.execute("INSERT INTO alunos (nome, turma, turno, foto, criado_em) VALUES (?,?,?,?,?)",
                 (nome, turma, turno, foto_nome, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/alunos/<int:aid>", methods=["DELETE"])
def excluir_aluno(aid):
    conn = get_db()
    conn.execute("DELETE FROM ocorrencias WHERE aluno_id = ?", (aid,))
    conn.execute("DELETE FROM alunos WHERE id = ?", (aid,))
    conn.commit()
    conn.close()
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
        data_nascimento=?, nome_responsavel=?, telefone_responsavel=?, 
        especificidade=?, observacoes_medicas=? WHERE id=?""",
        (data.get("data_nascimento", ""), data.get("nome_responsavel", ""), 
         data.get("telefone_responsavel", ""), data.get("especificidade", ""), 
         data.get("observacoes_medicas", ""), aid))
    
    conn.commit()
    conn.close()
    
    return jsonify({"ok": True})

# ===== API OCORRÊNCIAS =====
@app.route("/api/ocorrencias", methods=["POST"])
def registrar_ocorrencia():
    data = request.get_json()
    conn = get_db()
    conn.execute("""INSERT INTO ocorrencias 
        (aluno_id, codigo, descricao, registrado_por, data)
        VALUES (?,?,?,?,?)""",
        (data["aluno_id"], data["codigo"], data.get("descricao", ""),
         data["registrado_por"], datetime.now().strftime("%d/%m/%Y %H:%M")))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/ocorrencias/<int:aluno_id>")
def listar_ocorrencias(aluno_id):
    conn = get_db()
    rows = conn.execute("""SELECT * FROM ocorrencias WHERE aluno_id = ? 
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
    turno = data.get("turno")
    qtd = data.get("qtd_alunos")
    
    if not nome or not turno or not qtd:
        return jsonify({"erro": "Preencha todos os campos"}), 400
        
    try:
        conn = get_db()
        conn.execute("INSERT INTO turmas (nome, turno, qtd_alunos) VALUES (?, ?, ?)", (nome, turno, qtd))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Essa turma já está cadastrada!"}), 400

@app.route("/api/turmas/<int:tid>", methods=["DELETE"])
def deletar_turma(tid):
    conn = get_db()
    conn.execute("DELETE FROM turmas WHERE id = ?", (tid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

# ===== ROTA PARA AVANÇO DE ANO =====
@app.route("/api/avancar_ano", methods=["POST"])
def avancar_ano():
    conn = get_db()
    turmas = conn.execute("SELECT nome FROM turmas ORDER BY nome DESC").fetchall()
    
    # O "ORDER BY nome DESC" garante que ele mude a 3A antes da 2A, evitando erro de duplicação
    for t in turmas:
        nome_atual = t['nome']
        num_atual = int(nome_atual[0]) if nome_atual[0].isdigit() else 1
        letra = nome_atual[1:] if len(nome_atual) > 1 else ""
        
        novo_num = num_atual + 1
        if novo_num > 3: novo_num = 3 
        
        novo_nome = f"{novo_num}{letra}"
        
        # Só atualiza se o nome for diferente (evita erro se já for 3A e virar 3A)
        if nome_atual != novo_nome:
            conn.execute("UPDATE alunos SET turma = ? WHERE turma = ?", (novo_nome, nome_atual))
            conn.execute("UPDATE turmas SET nome = ? WHERE nome = ?", (novo_nome, nome_atual))
        
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "msg": "Alunos avançados de ano com sucesso!"})

# ===== ROTA PARA O MURAL GERAL E NOTIFICAÇÕES =====
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
        WHERE 1=1
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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
