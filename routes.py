from flask import render_template,request,redirect,url_for,flash,session
from app import app
from models import db,User
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps



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
    return render_template('librarian.html')

@app.route('/section/add')
@librarian_required
def add_section():
    return render_template('sections/add_section.html')

@app.route('/section/add', methods=['POST'])
@librarian_required
def add_section_post():
    return "Add section"

@app.route('/section/<int:section_id>')
@librarian_required
def view_section(section_id):
    return "View section"

@app.route('/section/<int:section_id>/edit')
@librarian_required
def edit_section(section_id):
    return "Edit section"

@app.route('/section/<int:section_id>/delete')
@librarian_required
def delete_section(section_id):
    return "Delete section"

