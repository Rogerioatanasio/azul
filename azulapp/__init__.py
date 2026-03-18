from flask import Flask
from .extensions import db, migrate

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///local.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "dev-key"

    UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    def allowed_file(filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


    db.init_app(app)
    migrate.init_app(app, db)

    return app
