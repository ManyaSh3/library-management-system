from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db= SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(32), unique=True)
    passhash=db.Column(db.String(256), nullable=False)
    name=db.Column(db.String(64), nullable=True)
    is_librarian=db.Column(db.Boolean,nullable=False, default=False)

with app.app_context():
    db.create_all()

    librarian=User.query.filter_by(is_librarian=True).first()

    if not librarian:
        password_hash=generate_password_hash('librarian')
        librarian=User(username='librarian',passhash=password_hash,name='librarian',is_librarian=True)
        db.session.add(librarian)
        db.session.commit()