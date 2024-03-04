from flask import render_template,request,redirect,url_for,flash,session
from app import app
from models import db,User,Section,Book
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime



@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()
    if not username or not password:
        flash('Please fill out all fields')
        return redirect(url_for('login'))
    if not user:
        flash('Username does not exist')
        return redirect(url_for('login'))
    if not check_password_hash(user.passhash, password):
        flash('Incorrect password')
        return redirect(url_for('login'))
    session['userid'] = user.id
    return redirect(url_for('index'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register' , methods=['POST'])
def register_post():
    username=request.form.get('username')
    password=request.form.get('password')
    confirm_password=request.form.get('confirm_password')
    name=request.form.get('name')

    if password!=confirm_password:
        flash('Passwords do not match')
        return redirect(url_for('register'))
    if not username or not password or not confirm_password:
        flash('Please fill out all fields')
        return redirect(url_for('register'))
    

    user=User.query.filter_by(username=username).first()
    if user:
        flash('Username already exists')
        return redirect(url_for('register'))
    
    password_hash=generate_password_hash(password)

    new_user=User(username=username,passhash=password_hash,name=name)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))


#decorator to check if user is logged in

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'userid' in session:
            return func(*args, **kwargs)
        else:
            flash('Please login to continue')
            return redirect(url_for('login'))
    return inner
#decorator to check if user is admin

def librarian_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'userid' in session:
            user=User.query.get(session['userid'])
            if user.is_librarian:
                return func(*args, **kwargs)
            else:
                flash('You are not authorized to access this page')
                return redirect(url_for('index'))
        else:
            flash('Please login to continue')
            return redirect(url_for('login'))
    return inner



@app.route('/')
@auth_required
def index():
    user=User.query.get(session['userid'])
    if user.is_librarian:
        return redirect(url_for('librarian'))
    # if 'userid' in session:
    return render_template('index.html')
    
    
@app.route('/profile')
@auth_required
def profile():
    #if 'userid' in session:
        user=User.query.filter_by(id=session['userid']).first()
        return render_template('profile.html',user=user)

@app.route('/profile', methods=['POST'])
@auth_required
def profile_post():
    username = request.form.get('username')
    cpassword = request.form.get('cpassword')
    new_password = request.form.get('new_password')
    name = request.form.get('name')

    if not username or not cpassword or not new_password:
        flash('Please fill out all fields')
        return redirect(url_for('profile'))

    user = User.query.filter_by(id=session['userid']).first()
    if not check_password_hash(user.passhash, cpassword):
        flash('Incorrect password')
        return redirect(url_for('profile'))
    if username != user.username:
        new_username = User.query.filter_by(username=username).first()
        if new_username:
            flash('Username already exists')
            return redirect(url_for('profile'))

    new_password_hash = generate_password_hash(new_password)
    user.username = username
    user.passhash = new_password_hash
    user.name = name
    db.session.commit()  # Commit changes to the database
    flash('Profile updated')
    return redirect(url_for('profile'))

@app.route('/logout')
@auth_required
def logout():
    session.pop('userid',None)
    return redirect(url_for('login'))

@app.route('/librarian')
@librarian_required
def librarian():
    sections=Section.query.all()
    return render_template('librarian.html' , sections=sections)

@app.route('/section/add')
@librarian_required
def add_section():
    return render_template('sections/add_section.html')

@app.route('/section/add', methods=['POST'])
@librarian_required
def add_section_post():
    section_name = request.form.get('title')
    date_str = request.form.get('date_created')
    description = request.form.get('description')


    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD format.')
        return redirect(url_for('add_section'))

    if not section_name or not date_str or not description:
        flash('Please fill out all fields')
        return redirect(url_for('add_section'))
    section=Section(title=section_name,date_created=date,description=description)
    db.session.add(section)
    db.session.commit()
    flash('Section added successfully')
    return redirect(url_for('librarian'))

@app.route('/section/<int:section_id>')
@librarian_required
def view_section(section_id):
    sections=Section.query.get(section_id)
    if not sections:
        flash('Section not found')
        return redirect(url_for('librarian'))
    books=Book.query.filter_by(section_id=section_id).all()
    return render_template('sections/view_section.html',section=sections,books=books)

@app.route('/section/<int:section_id>/edit')
@librarian_required
def edit_section(section_id):
    section=Section.query.get(section_id)
    if not section:
        flash('Section not found')
        return redirect(url_for('librarian'))
    return render_template('sections/edit_section.html',section=section)

@app.route('/section/<int:section_id>/edit', methods=['POST'])
@librarian_required
def edit_section_post(section_id):
    section_name = request.form.get('title')
    description = request.form.get('description')

    if not section_name or not description:
        flash('Please fill out all fields')
        return redirect(url_for('edit_section', section_id=section_id))

    section = Section.query.get(section_id)
    section.title = section_name
    section.description = description
    db.session.commit()
    flash('Section updated successfully')
    return redirect(url_for('librarian'))

@app.route('/section/<int:section_id>/delete')
@librarian_required
def delete_section(section_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section not found')
        return redirect(url_for('librarian'))
    return render_template('sections/delete_section.html', section=section)

@app.route('/section/<int:section_id>/delete', methods=['POST'])
@librarian_required
def delete_section_post(section_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section not found')
    db.session.delete(section)
    db.session.commit()
    flash('Section deleted successfully')
    return redirect(url_for('librarian'))

#routes for books

@app.route('/book/add/<int:section_id>')
@librarian_required
def add_books(section_id):
    sections = Section.query.all()
    section=Section.query.get(section_id)
    if not section:
        flash('No sections found. Please add a section first')
        return redirect(url_for('librarian'))
    now = datetime.now().strftime('%Y-%m-%d')
    return render_template('books/add_books.html' , sections=sections , now=now , section=section)


@app.route('/book/add', methods=['POST'])
@librarian_required
def add_books_post():
    title = request.form.get('title')
    author = request.form.get('author')
    content=request.form.get('content')
    str_date=request.form.get('date_created')
    section_id=request.form.get('section_id')

    try:
        date = datetime.strptime(str_date, '%Y-%m-%d')
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD format.')
        return redirect(url_for('add_books'))
    

    if not title or not author or not content or not str_date or not section_id:
        flash('Please fill out all fields')
        return redirect(url_for('add_books'))

    book = Book(title=title, author=author, content=content , date_created=date, section_id=section_id)
    db.session.add(book)
    db.session.commit()
    flash('Book added successfully')
    return redirect(url_for('librarian'))

@app.route('/book/<int:book_id>/edit')
@librarian_required
def edit_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        flash('Book not found')
        return redirect(url_for('librarian'))
    sections = Section.query.all()
    return render_template('books/edit_book.html', books=book, sections=sections)

@app.route('/book/<int:book_id>/edit', methods=['POST'])
@librarian_required
def edit_book_post(book_id):
    title = request.form.get('title')
    author = request.form.get('author')
    content = request.form.get('content')
    section_id = request.form.get('section_id')

    if not title or not section_id:
        flash('Please fill out all fields')
        return redirect(url_for('edit_book', book_id=book_id))

    book = Book.query.get(book_id)
    book.title = title
    book.author = author
    book.content = content

    book.section_id = section_id
    db.session.commit()
    flash('Book updated successfully')
    return redirect(url_for('librarian'))

@app.route('/book/<int:book_id>/delete')
@librarian_required
def delete_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        flash('Book not found')
        return redirect(url_for('librarian'))
    return render_template('books/delete_book.html', book=book)

@app.route('/book/<int:book_id>/delete', methods=['POST'])
@librarian_required
def delete_book_post(book_id):
    book = Book.query.get(book_id)
    if book is not None:
        db.session.delete(book)
        db.session.commit()
        flash('Book deleted successfully')
        return redirect(url_for('librarian'))
    else:
        flash('Book not found')
        return redirect(url_for('librarian'))
    
 

