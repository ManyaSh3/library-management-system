from flask import render_template,request,redirect,url_for,flash,session,render_template_string
from app import app
from flask import send_from_directory
from models import db,User,Section,Book,book_issue,book_request,remaining_issue_days,book_rating,book_feedback,transaction_history,book_return
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import plotly.graph_objs as go
from plotly.offline import plot
from collections import defaultdict





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

    update_remaining_days(user.id)

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
    
 
#routes for users
    
@app.route('/')
@auth_required
def index():
    user = User.query.get(session.get('userid'))

    # Check if user exists
    if not user:
        flash('User not found. Please log in again.')
        return redirect(url_for('login'))

    if user.is_librarian:
        return redirect(url_for('librarian'))
    
    
    sections = Section.query.all()
    books = Book.query.all()

    cname = request.args.get('cname') or ''
    pname = request.args.get('pname') or ''

    all_sections = Section.query.all()

    if cname:
        sections = Section.query.filter(Section.title.ilike(f'%{cname}%')).all()

    if pname:
        books = Book.query.filter(Book.title.ilike(f'%{pname}%')).all()
    
    return render_template('index.html', user=user, sections=sections, books=books, cname=cname, pname=pname , all_sections=all_sections)




@app.route('/remaining_days/<int:user_id>', methods=['POST'])
@auth_required
def update_remaining_days(user_id):
    import datetime

    # Get current date
    current_date = datetime.datetime.now()  

    # Find all books issued to the specified user
    borrowed_books = book_issue.query.filter_by(user_id=user_id, status=True).all()

    # Create a dictionary to store the last update date for each remaining_days_entry
    last_update_dates = defaultdict(lambda: None)

    if borrowed_books:
        for borrowed_book in borrowed_books:
            # Find the corresponding remaining_issue_days for the current borrowed_book
            remaining_days_entry = remaining_issue_days.query.filter_by(user_id=user_id, book_id=borrowed_book.book_id).first()

            if remaining_days_entry:
                # Calculate the difference in days between current date and remaining_days
                borrowed_date = borrowed_book.date_issued
                borrowed_duration = remaining_days_entry.remaining_days
                elapsed_time = (current_date - borrowed_date ).days  + 1
                days_difference = borrowed_duration - elapsed_time

                if days_difference < 0:
                    borrowed_book.status = False
                    db.session.commit()

                # Check if the update has already been done for the current day
                last_update_date = last_update_dates[remaining_days_entry.id]
                if last_update_date != current_date.date():
                    # Update remaining days in the remaining_issue_days table
                    remaining_days_entry.remaining_days = days_difference
                    db.session.commit()

                    # Update the last update date in the dictionary
                    last_update_dates[remaining_days_entry.id] = current_date.date()
            else:
                # Handle the case when the entry doesn't exist
                print(f"Warning: No remaining days entry found for book_id {borrowed_book.book_id} and user_id {user_id}.")
    else:
        return "No borrowed books found for this user."

@app.route('/check_overdue_books')
@librarian_required  # Assuming this decorator is used for librarian authentication
def check_overdue_books():
    # Logic to retrieve overdue books
    overdue_books = book_issue.query.filter(book_issue.status == False).all()
    book_ids = [book.book_id for book in overdue_books]
    books = Book.query.filter(Book.id.in_(book_ids)).all()

    return render_template('expired_books.html', expired_books=overdue_books, books=books)

@app.route('/revoke_book/<int:book_id>', methods=['POST'])
@librarian_required  # Assuming this decorator is used for librarian authentication
def revoke_book(book_id):
    book = book_issue.query.get_or_404(book_id)
    current_user = book.user_id
    db.session.delete(book)
    db.session.commit()
    remaining_days_entry = remaining_issue_days.query.filter_by(book_id=book_id,user_id=current_user ).first()
    if remaining_days_entry:
        db.session.delete(remaining_days_entry)
        db.session.commit()
    flash('The book has been revoked successfully.', 'success')
    return redirect(url_for('check_overdue_books'))   # Redirect back to the expired books page

@app.route('/return_book/<int:book_id>', methods=['POST'])
@auth_required  
def return_book(book_id):
    book = Book.query.get(book_id)
    print(book_id)
    if not book:
        flash('Book not found')
        return redirect(url_for('index'))

    # Check if the book is borrowed by the current user
    borrowed_book = book_issue.query.filter_by(book_id=book_id, user_id=session.get('userid')).first()

    if not borrowed_book:
        flash('You have not borrowed this book')
        return redirect(url_for('index'))

    # Remove the association between the user and the book by deleting the book_issue record
    db.session.delete(borrowed_book)
    db.session.commit()

    # Delete the corresponding entry in remaining_issue_days
    remaining_days_entry = remaining_issue_days.query.filter_by(book_id=book_id, user_id=session.get('userid')).first()
    if remaining_days_entry:
        db.session.delete(remaining_days_entry)
        db.session.commit()

    flash('Book returned successfully')
    return redirect(url_for('index'))



@app.route('/borrowed_books')
@auth_required
def borrowed_books():
    user_id = session.get('userid')    
    borrowed_books = book_issue.query.filter_by(user_id=user_id, status=True).all()
    overdue_books = book_issue.query.filter_by(user_id=user_id, status= False).all()
    remaining_days_dict = {}  # Dictionary to store remaining days for each book

    # Fetch remaining days for each book
    for book in borrowed_books:
        remaining_days_obj = remaining_issue_days.query.filter_by(book_id=book.book_id, user_id=user_id).first()
        if remaining_days_obj:
            remaining_days_dict[book.book_id] = remaining_days_obj.remaining_days

    return render_template('borrowed_books.html', borrowed_books=borrowed_books, overdue_books=overdue_books,remaining_days_dict=remaining_days_dict)


@app.route('/request_book/<int:book_id>', methods=['POST'])
@auth_required
def request_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        flash('Book not found')
        return redirect(url_for('index'))
    
    # Check if the book is already borrowed
    borrowed_book = book_issue.query.filter_by(book_id=book_id, user_id=session.get('userid')).first()
    if borrowed_book:
        flash('You have already borrowed this book')
        return redirect(url_for('index'))
    requested_book = book_request.query.filter_by(book_id=book_id, user_id=session.get('userid')).first()
    if requested_book:
        flash('You have already requested this book')
        return redirect(url_for('index'))
    # Check the number of issued books
    issued_books_count = book_issue.query.filter_by(user_id=session.get('userid'), status=True).count()
    if issued_books_count >= 5:
        flash('You have already issued 5 books. Return some before issuing more.')
        return redirect(url_for('index'))

    # Get the number of days from the form submission
    days = int(request.form['days'])
    
    # Request the book
    new_borrowed_book = book_request(book_id=book_id, user_id=session.get('userid'), date_requested=datetime.now(), status=True)
    db.session.add(new_borrowed_book)
    
    # Update the remaining_issue_days table
    remaining_issue_days_entry = remaining_issue_days.query.filter_by(book_id=book_id, user_id=session.get('userid')).first() 

    if not remaining_issue_days_entry:
        remaining_issue_days_entry = remaining_issue_days(
            user_id=session.get('userid'),
            book_id=book_id,
            remaining_days=days
        )
    else:
        remaining_issue_days_entry.remaining_days = days

    db.session.add(remaining_issue_days_entry)
    db.session.commit()

    
    flash('Book requested successfully')
    return redirect(url_for('index'))
@app.route('/requested_books')
@librarian_required
def requested_books():
    requested_books = book_request.query.filter_by(status=True).all()
    return render_template('review_book.html', requested_books=requested_books)

@app.route('/cancel_request/<int:book_id>', methods=['POST'])
@librarian_required
def cancel_request(book_id):
    book = Book.query.get(book_id)
    if not book:
        flash('Book not found')
        return redirect(url_for('librarian'))
    
    # Check if the book is requested by the current user
    requested_book = book_request.query.filter_by(book_id=book_id).first()

    if not requested_book:
        flash('You have not requested this book')
        return redirect(url_for('librarian'))
    
    # Remove the association between the user and the book by deleting the book_request record
    db.session.delete(requested_book)
    db.session.commit()

    flash('Book request cancelled successfully')
    return redirect(url_for('librarian'))

@app.route('/approve_request/<int:book_id>', methods=['POST'])
@librarian_required
def approve_request(book_id):
    book = Book.query.get(book_id)
    if not book:
        flash('Book not found')
        return redirect(url_for('librarian'))
    
    requested_book = book_request.query.filter_by(book_id=book_id).first()
    if not requested_book:
        flash('You have not requested this book')
        return redirect(url_for('librarian'))
    
    issued_books_count = 0  # Initialize issued_books_count with a default value

    issued_books_count = book_issue.query.filter(
        book_issue.user_id == requested_book.user_id,
        book_issue.status == True  # Assuming True indicates the book is issued
    ).count()

    if issued_books_count >= 5:
        flash('User has already issued 5 books. Cannot issue more.')
        return redirect(url_for('requested_books'))

    add_book = book_issue(book_id=book_id, user_id=requested_book.user_id, date_issued=datetime.now(), date_return=datetime.now(), status=True)
    db.session.add(add_book)
    db.session.commit()
    
    # Remove the association between the user and the book by deleting the book_request record
    db.session.delete(requested_book)
    db.session.commit()

    flash('Book request approved successfully')
    return redirect(url_for('requested_books'))





@app.route('/dashboard')
@auth_required
def dashboard():
    # Retrieve borrowed books data from the book_issue table for the current user
    user_id = session.get('userid')

    # Filter borrowed books by user_id and status
    borrowed_books = book_issue.query.filter_by(user_id=user_id, status=True).all()

    # Extract section names and counts from borrowed books
    section_counts = {}
    for borrowed_book in borrowed_books:
        section_title = borrowed_book.books.section.title
        section_counts[section_title] = section_counts.get(section_title, 0) + 1

    section_names = list(section_counts.keys())
    section_book_counts = list(section_counts.values())

    # Create a Donut chart for section distribution of borrowed books
    fig_donut = go.Figure(data=[go.Pie(labels=section_names, values=section_book_counts, hole=.3)])
    fig_donut.update_layout(
        title="Section Distribution",  # Add a title to the plot
        title_font_size=24,  # Customize the title font size
        title_font_color="brown",  # Customize the title font color
        width=600,  # Set the width of the plot
        height=400,  # Set the height of the plot
        paper_bgcolor='rgba(0,0,0,0)',  # Set background color to be transparent
        plot_bgcolor='rgba(0,0,0,0)',  # Set plot background color to be transparent
        font=dict(
            family="Arial, sans-serif",  # Customize the font family
            size=10,  # Customize the font size
            color="black"  # Customize the font color
        ),
        legend=dict(
            orientation="v",  # Set orientation to vertical
            x=0,  # Set x position to the left
            y=0.5  # Set y position to the middle
        )
    )


    # Get all sections
    all_sections = Section.query.all()
    all_section_names = [section.title for section in all_sections]

    # Initialize counts for all sections to 0
    section_book_counts = [0] * len(all_sections)

    # Update counts for sections where the user has borrowed books
    for borrowed_book in borrowed_books:
        section_title = borrowed_book.books.section.title
        section_index = all_section_names.index(section_title)
        section_book_counts[section_index] += 1

    # Create a Bar graph for books distribution per section
    fig_bar = go.Figure(data=[go.Bar(x=all_section_names, y=section_book_counts)])
    fig_bar.update_layout(
        title="Number of Books per Section",  # Add a title to the plot
        title_font_size=24,  # Customize the title font size
        title_font_color="brown",  # Customize the title font color
        width=600,  # Set the width of the plot
        height=400,  # Set the height of the plot
        paper_bgcolor='rgba(0,0,0,0)',  # Set background color to be transparent
        plot_bgcolor='rgba(0,0,0,0)',  # Set plot background color to be transparent
        font=dict(
            family="Arial, sans-serif",  # Customize the font family
            size=14,  # Customize the font size
            color="black"  # Customize the font color
        )
    )


    # Convert Plotly figures to HTML strings
    plot_html_donut = fig_donut.to_html(full_html=False)
    plot_html_bar = fig_bar.to_html(full_html=False)

    # Render the template with plot HTML using render_template_string
    return render_template('dashboard.html' ,plot_html_donut=plot_html_donut, plot_html_bar=plot_html_bar)


@app.route('/librarian/dashboard')
def librarian_dashboard():
    # Retrieve section data from the Section table
    sections = Section.query.all()
    
    # Extract section names and counts
    section_names = [section.title for section in sections]
    section_counts = [len(section.books) for section in sections]  # Assuming each section has a "books" attribute

    # Create a Donut chart with custom dimensions for section distribution
    fig_donut = go.Figure(data=[go.Pie(labels=section_names, values=section_counts, hole=.3)])
    fig_donut.update_layout(
        title="Section Distribution",  # Add a title to the plot
        title_font_size=24,  # Customize the title font size
        title_font_color="brown",  # Customize the title font color
        width=600,  # Set the width of the plot
        height=400,  # Set the height of the plot
        paper_bgcolor='rgba(0,0,0,0)',  # Set background color to be transparent
        plot_bgcolor='rgba(0,0,0,0)',  # Set plot background color to be transparent
        font=dict(
            family="Arial, sans-serif",  # Customize the font family
            size=10,  # Customize the font size
            color="black"  # Customize the font color
        ),
        legend=dict(
            orientation="v",  # Set orientation to vertical
            x=0,  # Set x position to the left
            y=0.5  # Set y position to the middle
        )
    )

    # Create a bar graph for number of books issued per section
    books_issued_per_section = [Book.query.filter_by(section_id=section.id).join(book_issue).filter_by(status=True).count() for section in sections]
    fig_bar = go.Figure([go.Bar(x=section_names, y=books_issued_per_section)])
    fig_bar.update_layout(
        title="Number of Books issued per Section",  # Add a title to the plot
        title_font_size=24,  # Customize the title font size
        title_font_color="brown",  # Customize the title font color
        width=600,  # Set the width of the plot
        height=400,  # Set the height of the plot
        paper_bgcolor='rgba(0,0,0,0)',  # Set background color to be transparent
        plot_bgcolor='rgba(0,0,0,0)',  # Set plot background color to be transparent
        font=dict(
            family="Arial, sans-serif",  # Customize the font family
            size=14,  # Customize the font size
            color="black"  # Customize the font color
        )
    )

    # Convert Plotly figures to HTML strings
    plot_html_donut = fig_donut.to_html(full_html=False)
    plot_html_bar = fig_bar.to_html(full_html=False)

    # Render the template with the plot HTML
    return render_template('librarian_dashboard.html', 
                           plot_html_donut=plot_html_donut, 
                           plot_html_bar=plot_html_bar)

#routes for rating and feedback
@app.route('/rate_book/<int:book_id>', methods=['POST'])
@auth_required
def submit_rating(book_id):
    rating = request.form.get('rating')
    if not rating:
        flash('Please provide a rating')
        return redirect(url_for('rate_book', book_id=book_id))

    # Check if the user has already rated the book
    rated_book = book_rating.query.filter_by(book_id=book_id, user_id=session.get('userid')).first()
    if rated_book:
        flash('You have already rated this book')
        return redirect(url_for('borrowed_books'))

    # Add the rating to the database
    new_rating = book_rating(book_id=book_id, user_id=session.get('userid'), rating=rating)
    db.session.add(new_rating)
    db.session.commit()

    flash('Rating submitted successfully')
    return redirect(url_for('borrowed_books'))

@app.route('/rate_book/<int:book_id>' , methods=['GET' , 'POST'])
@auth_required
def rate_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        flash('Book not found')
        return redirect(url_for('index'))

    # Check if the user has already rated the book
    rated_book = book_rating.query.filter_by(book_id=book_id, user_id=session.get('userid')).first()
    if rated_book:
        flash('You have already rated this book')
        return redirect(url_for('borrowed_books'))

    return render_template('rate_book.html', book=book)


@app.route('/feedback_book/<int:book_id>', methods=['POST'])
@auth_required
def submit_feedback(book_id):
    feedback = request.form.get('feedback')
    if not feedback:
        flash('Please provide feedback')
        return redirect(url_for('feedback_book', book_id=book_id))

    # Check if the user has already provided feedback for the book
    feedback_given = book_feedback.query.filter_by(book_id=book_id, user_id=session.get('userid')).first()
    if feedback_given:
        flash('You have already provided feedback for this book')
        return redirect(url_for('borrowed_books'))

    # Add the feedback to the database
    new_feedback = book_feedback(book_id=book_id, user_id=session.get('userid'), feedback=feedback)
    db.session.add(new_feedback)
    db.session.commit()

    flash('Feedback submitted successfully')
    return redirect(url_for('borrowed_books'))

@app.route('/feedback_book/<int:book_id>', methods=['GET'])
@auth_required
def feedback_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        flash('Book not found')
        return redirect(url_for('index'))
    
    # Check if the user has already provided feedback for the book
    feedback_given = book_feedback.query.filter_by(book_id=book_id, user_id=session.get('userid')).first()
    if feedback_given:
        flash('You have already provided feedback for this book')
        return redirect(url_for('borrowed_books'))
    
    return render_template('feedback_book.html', book=book)
 
@app.route('/pdf_view/<int:book_id>')
def pdf_view(book_id):
    # Assuming the PDF file is named "Naruto v01.pdf" and is located in the static folder
    pdf_filename = 'Naruto v01.pdf'
    # Send the PDF file to the client
    return send_from_directory(app.static_folder, pdf_filename)


@app.route('/book_ratings_feedback')
def book_ratings_feedback():
    # Fetch book ratings and feedbacks from the database
    book_ratings = book_rating.query.all()
    book_feedbacks = book_feedback.query.all()
    return render_template('book_ratings_feedback.html', 
                           book_ratings=book_ratings, 
                           book_feedbacks=book_feedbacks)

@app.context_processor
def utility_processor():
    def get_book_title(book_id):
        book = Book.query.get(book_id)
        if book:
            return book.title
        else:
            return "Unknown"
    return dict(get_book_title=get_book_title)


@app.route('/library_status')
def library_status():
    # Fetch borrowed books and overdue books from the database
    borrowed_books = book_issue.query.filter_by(status=True).all()
    overdue_books = book_issue.query.filter_by(status= False).all()
    remaining_days=remaining_issue_days.query.all()

    return render_template('library_status.html', 
                           borrowed_books=borrowed_books, 
                           overdue_books=overdue_books,remaining_days=remaining_days)

@app.route('/revoke_access/<int:book_id>', methods=['POST'])
@librarian_required  # Assuming this decorator is used for librarian authentication
def revoke_access(book_id):
    book = book_issue.query.get_or_404(book_id)
    current_user = book.user_id
    db.session.delete(book)
    # Remove the entry from remaining issue days
    remaining_days_entry = remaining_issue_days.query.filter_by(id=book_id,user_id=current_user).first()
    db.session.delete(remaining_days_entry)
    db.session.commit()
    return redirect(url_for('library_status'))   # Redirect back to the expired books page

# Sample route for processing payment and initiating download

@app.route('/process_payment', methods=['POST'])
def process_payment():
    book_id = request.form.get('book_id')
    print('yes')
    # Update the transaction history
    action = 'Payment Made'
    date = datetime.now()
    new_transaction = transaction_history(book_id=book_id, user_id=session.get('userid'), date=date, action=action)
    db.session.add(new_transaction)
    db.session.commit()

    # Simulate payment processing
    import time
    time.sleep(2)  # Adjust the sleep time as needed for actual payment processing time

    # Modify the payment button attributes
    return redirect(url_for('download_book_after_payment', book_id=book_id))

# Route for rendering the HTML page
@app.route('/download_book/<int:book_id>', methods=['GET'])
def download_book(book_id):
    return render_template('download.html', book_id=book_id)

@app.route('/download_book_after_payment/<int:book_id>', methods=['GET'])
def download_book_after_payment(book_id):
    return render_template('download_after_payment.html', book_id=book_id)

from flask import send_file
# Route for processing download after successful payment
@app.route('/process_download/<int:book_id>', methods=['GET'])
def process_download(book_id):
    # Assuming the sample.pdf file is located in the static folder
    pdf_path = 'static/book/Naruto v01.pdf'
    # You can also add logic here to check authorization or other conditions before allowing download
    return send_file(pdf_path, as_attachment=True)

@app.route('/faq')
def faq():
    return render_template('faq.html')
