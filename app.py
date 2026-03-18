from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from uuid import uuid4
import json
import os
import re

from azulapp.extensions import db, migrate
from azulapp.models import Trabalhador, Usuario

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///local.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "dev-key"

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db.init_app(app)
migrate.init_app(app, db)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ==============================
# FUNÇÕES AUXILIARES
# ==============================

def normalizar_whatsapp(numero: str) -> str:
    numero = re.sub(r"\D", "", numero)

    if len(numero) == 11:
        numero = "55" + numero

    return f"https://wa.me/{numero}"


# ==============================
# CONFIGURAÇÃO DO CAMINHO DO JSON (LEGADO - pode remover depois)
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_DADOS = os.path.join(BASE_DIR, "data", "trabalhadores.json")

os.makedirs(os.path.dirname(CAMINHO_DADOS), exist_ok=True)

if not os.path.exists(CAMINHO_DADOS):
    with open(CAMINHO_DADOS, "w", encoding="utf-8") as f:
        json.dump([], f)


def carregar_trabalhadores():
    with open(CAMINHO_DADOS, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


PROFISSOES_PERMITIDAS = [
    "Pedreiro",
    "Eletricista",
    "Encanador",
    "Pintor",
    "Faxineira",
    "Ajudante Geral",
]


# ==============================
# ROTAS
# ==============================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "").strip()

        if not email or not senha:
            flash("Preencha email e senha.", "error")
            return redirect(url_for("register"))

        if Usuario.query.filter_by(email=email).first():
            flash("Email já cadastrado.", "error")
            return redirect(url_for("register"))

        user = Usuario(
            email=email,
            senha_hash=generate_password_hash(senha)
        )
        db.session.add(user)
        db.session.commit()

        flash("Conta criada! Agora faça login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "").strip()

        user = Usuario.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.senha_hash, senha):
            flash("Login inválido.", "error")
            return redirect(url_for("login"))

        session.clear()
        session["user_id"] = user.id
        flash("Logado com sucesso!", "success")
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Você saiu da conta.", "success")
    return redirect(url_for("home"))


@app.route("/trabalhar", methods=["GET", "POST"])
def trabalhar():
    if "user_id" not in session:
        flash("Faça login para cadastrar seu perfil profissional.", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    perfil_existente = Trabalhador.query.filter_by(usuario_id=user_id).first()
    if perfil_existente:
        flash("Você já possui um perfil cadastrado. Edite o perfil existente.", "error")
        return redirect(url_for("editar_trabalhador", trabalhador_id=perfil_existente.id))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        profissao = request.form.get("profissao", "").strip()
        whatsapp = request.form.get("whatsapp", "").strip()
        cidade = request.form.get("cidade", "").strip()
        estado = request.form.get("estado", "").strip().upper()

        if profissao not in PROFISSOES_PERMITIDAS:
            flash("Selecione uma profissão válida.", "error")
            return redirect(url_for("trabalhar"))

        if not nome or not profissao or not whatsapp:
            flash("Preencha nome, profissão e WhatsApp.", "error")
            return redirect(url_for("trabalhar"))

        if len(nome) < 2:
            flash("Nome muito curto.", "error")
            return redirect(url_for("trabalhar"))

        if estado and len(estado) != 2:
            flash("Estado deve ter 2 letras (ex: SP).", "error")
            return redirect(url_for("trabalhar"))

        if cidade and len(cidade) < 2:
            flash("Cidade inválida.", "error")
            return redirect(url_for("trabalhar"))

        whatsapp_limpo = re.sub(r"\D", "", whatsapp)

        if len(whatsapp_limpo) in (10, 11):
            pass
        elif len(whatsapp_limpo) in (12, 13) and whatsapp_limpo.startswith("55"):
            pass
        else:
            flash("WhatsApp inválido. Use DDD + número (ex: 13 99999-9999).", "error")
            return redirect(url_for("trabalhar"))

        arquivo = request.files.get("foto")
        nome_arquivo_final = None

        if arquivo and arquivo.filename:
            if not allowed_file(arquivo.filename):
                flash("Formato de imagem inválido. Use PNG/JPG/JPEG/WEBP.", "error")
                return redirect(url_for("trabalhar"))

            filename = secure_filename(arquivo.filename)
            ext = filename.rsplit(".", 1)[1].lower()
            nome_arquivo_final = f"{uuid4().hex}.{ext}"

            caminho = os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo_final)
            arquivo.save(caminho)

        novo = Trabalhador(
            nome=nome,
            profissao=profissao,
            whatsapp=whatsapp_limpo,
            cidade=cidade or None,
            estado=estado or None,
            foto=nome_arquivo_final,
            usuario_id=user_id
        )

        db.session.add(novo)
        db.session.commit()

        flash("Cadastro realizado com sucesso!", "success")
        return redirect(url_for("home"))

    return render_template("trabalhar.html")


@app.route("/trabalhador/<int:trabalhador_id>/editar", methods=["GET", "POST"])
def editar_trabalhador(trabalhador_id):
    if "user_id" not in session:
        flash("Faça login para continuar.", "error")
        return redirect(url_for("login"))

    t = Trabalhador.query.get_or_404(trabalhador_id)

    if t.usuario_id != session.get("user_id"):
        flash("Você não tem permissão para editar este perfil.", "error")
        return redirect(url_for("contratar"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        profissao = request.form.get("profissao", "").strip()
        whatsapp = request.form.get("whatsapp", "").strip()
        cidade = request.form.get("cidade", "").strip()
        estado = request.form.get("estado", "").strip().upper()

        if profissao not in PROFISSOES_PERMITIDAS:
            flash("Selecione uma profissão válida.", "error")
            return redirect(url_for("editar_trabalhador", trabalhador_id=trabalhador_id))

        if not nome or not profissao or not whatsapp:
            flash("Preencha nome, profissão e WhatsApp.", "error")
            return redirect(url_for("editar_trabalhador", trabalhador_id=trabalhador_id))

        if estado and len(estado) != 2:
            flash("Estado deve ter 2 letras (ex: SP).", "error")
            return redirect(url_for("editar_trabalhador", trabalhador_id=trabalhador_id))

        whatsapp_limpo = re.sub(r"\D", "", whatsapp)
        if len(whatsapp_limpo) in (10, 11):
            pass
        elif len(whatsapp_limpo) in (12, 13) and whatsapp_limpo.startswith("55"):
            pass
        else:
            flash("WhatsApp inválido. Use DDD + número.", "error")
            return redirect(url_for("editar_trabalhador", trabalhador_id=trabalhador_id))

        arquivo = request.files.get("foto")
        if arquivo and arquivo.filename:
            if not allowed_file(arquivo.filename):
                flash("Formato de imagem inválido. Use PNG/JPG/JPEG/WEBP.", "error")
                return redirect(url_for("editar_trabalhador", trabalhador_id=trabalhador_id))

            filename = secure_filename(arquivo.filename)
            ext = filename.rsplit(".", 1)[1].lower()
            nome_arquivo_final = f"{uuid4().hex}.{ext}"

            caminho = os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo_final)
            arquivo.save(caminho)

            t.foto = nome_arquivo_final

        t.nome = nome
        t.profissao = profissao
        t.whatsapp = whatsapp_limpo
        t.cidade = cidade or None
        t.estado = estado or None

        db.session.commit()
        flash("Dados atualizados com sucesso!", "success")
        return redirect(url_for("contratar"))

    return render_template(
        "editar_trabalhador.html",
        t=t,
        profissoes=PROFISSOES_PERMITIDAS
    )

@app.route("/destacar/<int:id>", methods=["POST"])
def destacar(id):
    if "user_id" not in session:
        flash("Faça login para continuar.", "error")
        return redirect(url_for("login"))

    t = Trabalhador.query.get_or_404(id)

    if t.usuario_id != session.get("user_id"):
        flash("Você não tem permissão para alterar este perfil.", "error")
        return redirect(url_for("contratar"))

    t.destaque = True
    t.plano = "destaque"

    db.session.commit()

    flash("Seu perfil foi marcado como destaque.", "success")
    return redirect(url_for("contratar"))

@app.route("/planos/<int:id>")
def planos(id):
    if "user_id" not in session:
        flash("Faça login para continuar.", "error")
        return redirect(url_for("login"))

    t = Trabalhador.query.get_or_404(id)

    if t.usuario_id != session.get("user_id"):
        flash("Você não tem permissão.", "error")
        return redirect(url_for("contratar"))

    return render_template("planos.html", t=t)

@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    if "user_id" not in session:
        flash("Faça login para continuar.", "error")
        return redirect(url_for("login"))

    t = Trabalhador.query.get_or_404(id)

    if t.usuario_id != session.get("user_id"):
        flash("Você não tem permissão para excluir este perfil.", "error")
        return redirect(url_for("contratar"))

    if t.foto:
        caminho = os.path.join(app.config["UPLOAD_FOLDER"], t.foto)
        if os.path.exists(caminho):
            os.remove(caminho)

    db.session.delete(t)
    db.session.commit()

    flash("Profissional removido com sucesso.", "success")
    return redirect(url_for("contratar"))


@app.route("/contratar")
def contratar():
    profissao = request.args.get("profissao", "").strip()
    cidade = request.args.get("cidade", "").strip()

    query = Trabalhador.query

    if profissao:
        query = query.filter_by(profissao=profissao)

    if cidade:
        query = query.filter(Trabalhador.cidade.ilike(f"%{cidade}%"))

    trabalhadores_db = query.order_by(
        Trabalhador.destaque.desc(),
        Trabalhador.foto.is_(None),
        Trabalhador.cidade.is_(None),
        Trabalhador.nome.asc()
    ).all()

    trabalhadores = []
    for t in trabalhadores_db:
        trabalhadores.append({
            "id": t.id,
            "nome": t.nome,
            "profissao": t.profissao,
            "whatsapp": t.whatsapp,
            "whatsapp_link": normalizar_whatsapp(t.whatsapp),
            "cidade": t.cidade,
            "estado": t.estado,
            "foto": t.foto,
            "usuario_id": t.usuario_id,
            "destaque": t.destaque,
            "plano": t.plano,
        })

    profissoes = sorted({t.profissao for t in trabalhadores_db})

    print("DEBUG trabalhadores:", trabalhadores[:5])

    total_encontrados = len(trabalhadores)

    return render_template(
        "contratar.html",
        trabalhadores=trabalhadores,
        profissoes=profissoes,
        profissao_selecionada=profissao,
        cidade_selecionada=cidade,
        total_encontrados=total_encontrados,
    )


if __name__ == "__main__":
    app.run(debug=True)