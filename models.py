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

class Section(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(32), nullable=False , unique=True)
    date_created=db.Column(db.DateTime, nullable=False)
    description=db.Column(db.String(256), nullable=True)
    books=db.relationship('Book',backref='section',lazy=True)

    


class Book(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(32), nullable=False)
    author=db.Column(db.String(32), nullable=False)
    content=db.Column(db.String(256), nullable=False)
    date_created=db.Column(db.DateTime, nullable=False)
    section_id=db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    # book_issues=db.relationship('book_issue',backref='book',lazy=True)
    # book_returns=db.relationship('book_return',backref='book',lazy=True)
    # book_requests=db.relationship('book_request',backref='book',lazy=True)
    # book_ratings=db.relationship('book_rating',backref='book',lazy=True)
    # book_feedbacks=db.relationship('book_feedback',backref='book',lazy=True)
    # transaction_historys=db.relationship('transaction_history',backref='book',lazy=True)


class book_issue(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    book_id=db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_issued=db.Column(db.DateTime, nullable=False)
    date_return=db.Column(db.DateTime, nullable=False)
    status=db.Column(db.Boolean,nullable=False, default=False)
    books=db.relationship('Book',backref='book_issue',lazy=True)
    users=db.relationship('User',backref='book_issue',lazy=True)


class book_return(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    book_id=db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_returned=db.Column(db.DateTime, nullable=False)
    books=db.relationship('Book',backref='book_return',lazy=True)
    usesr=db.relationship('User',backref='book_return',lazy=True)


class book_request(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    book_id=db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_requested=db.Column(db.DateTime, nullable=False)
    status=db.Column(db.Boolean,nullable=False, default=False) #False=Pending, True=Approved or Rejected 
    books=db.relationship('Book',backref='book_request',lazy=True)
    users=db.relationship('User',backref='book_request',lazy=True)

class book_rating(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    book_id=db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating=db.Column(db.Integer, nullable=False)
    books=db.relationship('Book',backref='book_rating',lazy=True)
    users=db.relationship('User',backref='book_rating',lazy=True)

class book_feedback(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    book_id=db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    feedback=db.Column(db.String(256), nullable=False)
    books=db.relationship('Book',backref='book_feedback',lazy=True)
    users=db.relationship('User',backref='book_feedback',lazy=True)

class transaction_history(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    book_id=db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date=db.Column(db.DateTime, nullable=False)
    action=db.Column(db.String(32), nullable=False) #Issue, Return, Request, Rating, Feedback , Delete
    books=db.relationship('Book',backref='transaction_history',lazy=True)
    users=db.relationship('User',backref='transaction_history',lazy=True)



with app.app_context():
    db.create_all()

    #if librarian not present, create one
    librarian=User.query.filter_by(is_librarian=True).first()

    if not librarian:
        password_hash=generate_password_hash('librarian')
        librarian=User(username='librarian',passhash=password_hash,name='librarian',is_librarian=True)
        db.session.add(librarian)
        db.session.commit()