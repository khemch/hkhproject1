import os
import requests
from flask import Flask, session, render_template, request, flash, redirect, url_for
from flask_session import Session
from flaskext.mysql import MySQL
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from pymysql.cursors import DictCursor
from wtforms import Form, StringField, SelectField, TextAreaField, PasswordField, validators
from functools import wraps
from passlib.hash import sha256_crypt

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'hkhproject1'
app.config['MYSQL_DATABASE_CURSORCLASS'] = 'DictCursor'

#init MYSQL
mysql = MySQL(cursorclass=DictCursor)
mysql.init_app(app)

# Home page
@app.route("/")
def index():
    return render_template('home.html')

# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# Search Form Class
class SearchForm(Form):
    req = StringField('Request', [validators.Length(min=1, max=50)])

# Review Form Class
class ReviewForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    rating = StringField('Rating (1 to 5)', [validators.Length(max=1)])
    body = TextAreaField('Body', [validators.Length(min=1)])

# Search
@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm(request.form)
    if request.method == 'POST':
        req = form.req.data

        # Create cursor
        cur = mysql.get_db().cursor()

        # Get user by username
        result = cur.execute('SELECT * FROM books WHERE title LIKE "%{0}%" OR author LIKE "%{0}%" OR isbn LIKE "%{0}%" OR year LIKE "%{0}%"'.format(req))

        if result > 0:
            data = cur.fetchall()

            return render_template('searchresults.html', data=data)

            # Close connection
            cur.close()
        else:
            error = 'No results found'
            return render_template('searchresults.html', error=error)

        return redirect(url_for('search'))
    return render_template('search.html', form=form)

# User register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create curseor
        cur = mysql.get_db().cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.get_db().commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.get_db().cursor()

        # Get user by username
        result = cur.execute('SELECT * FROM users WHERE username = %s', [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('search'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)

            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please log in', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

#API
@app.route('/api/<string:isbn>/', methods=['GET'])
def api(isbn):
    # Create Cursor
    cur = mysql.get_db().cursor()

    # Get data
    result = cur.execute("SELECT * FROM books LEFT JOIN goodreads ON books.isbn = goodreads.isbn WHERE books.isbn='{}'".format(isbn))

    data = cur.fetchone()

    if result > 0:
        return render_template('api.html', data=data)
    else:
        return render_template('404.html')

    # Close connection
    cur.close()

# Single Book
@app.route('/book/<string:id>/', methods=['GET', 'POST'])
@is_logged_in
def book(id):

    # Create Cursor
    cur = mysql.get_db().cursor()

    # Get result
    result = cur.execute("SELECT * FROM books LEFT JOIN goodreads ON books.isbn = goodreads.isbn WHERE books.isbn='{}'".format(id))

    book = cur.fetchone()

    if result > 0:
    # Close connection
        cur.close()

        # Create another Cursor
        cur = mysql.get_db().cursor()

        resultreview = cur.execute("SELECT * FROM reviews WHERE book='{}'".format(id))

        if resultreview > 0:
            # Get stored hash
            reviewdata = cur.fetchone()
            # Close connection
            cur.close()
            form = False
        else:
            reviewdata = False
            form = ReviewForm(request.form)
            if request.method == 'POST' and form.validate():
                title = form.title.data
                body = form.body.data
                rating = form.rating.data

                # Create Cursor
                cur = mysql.get_db().cursor()
                # Execute
                cur.execute("INSERT INTO reviews(title, body, rating, author, book) VALUES(%s, %s, %s, %s, %s)", (title, body, rating, session['username'], id))
                # Commit to DB
                mysql.get_db().commit()

                # Close connection
                cur.close()

                flash('Review added', 'success')

                return redirect(url_for('search'))

        return render_template('book.html', book=book, form=form, reviewdata=reviewdata)

    else:
        return render_template('404.html')

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
