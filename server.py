from flask import Flask, render_template, request, redirect, session, flash
from mysql_connection import connectToMySQL
from flask_bcrypt import Bcrypt
import re

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.secret_key = 'ermergerdertsersercert'
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

@app.route('/')
def loginPage():
	if 'reg' not in session:
		session['reg'] = True
	return render_template('login.html')

@app.route('/', methods=['POST'])
def flipForm():
	if session['reg'] == True:
		session['reg'] = False
	else:
		session['reg'] = True
	return redirect('/')

@app.route('/process', methods=['POST'])
def login_reg():
	validations = 0
	if request.form.get('login') is not None:
		if len(request.form['email'])<1 or not EMAIL_REGEX.match(request.form['email']):
			validations +=1
			flash('Email cannot be blank or is invalid')
		if len(request.form['password'])<1:
			validations +=1
			flash('Password was empty')
		if validations == 0 :
			db = connectToMySQL('jam_space')
			query = 'SELECT password, username, id FROM users WHERE email = "{}"'.format(request.form['email'])
			user = db.query_db(query)
			if user and bcrypt.check_password_hash(user[0]['password'], request.form['password']):
				session['username'] = user[0]['username']
				session['id'] = user[0]['id']
				return redirect('/dashboard')
			else:
				flash('There is no account associated with this email')
		return redirect('/')

	elif request.form.get('register') is not None:
		if len(request.form['username'])<3:
			validations += 1
			flash('Username needs to be longer than 3 characters')
		if len(request.form['email'])<1 or not EMAIL_REGEX.match(request.form['email']):
			validations +=1
			flash('Email cannot be blank or is invalid')
		db = connectToMySQL('jam_space')
		query = 'SELECT username FROM users WHERE email = "{}"'.format(request.form['email'])
		user = db.query_db(query)
	
		if len(user) > 0:
			validations +=1
			flash('Email already in use!')
		if len(request.form['password'])<4 or request.form['password'] != request.form['c_password']:
			validations +=1
			flash('Password cannot be blank or does not match')
		if validations == 0 :
			password = bcrypt.generate_password_hash(request.form['password'])
			db = connectToMySQL('jam_space')
			query = 'INSERT INTO users (username, email, password, created_at, updated_at) VALUES (%(username)s, %(email)s, %(password)s, NOW(), NOW())'
			data = {
				'username': request.form['username'],
				'email': request.form['email'],
				'password': password
			}
			db.query_db(query, data)
			db = connectToMySQL('jam_space')
			query = "SELECT id, username FROM users WHERE email ='{}'".format(request.form['email'])
			user = db.query_db(query)
			session['username'] = user[0]['username']
			session['id'] = user[0]['id']
			return redirect('/dashboard')
		elif validations >= 1:
			return redirect('/')

@app.route('/dashboard')
def dashboard():
	db = connectToMySQL('jam_space')
	if session.get('username') is None:
		return redirect('/')
	query = "SELECT posts.id, posts.content, posts.created_at, users.username FROM posts LEFT JOIN users ON posts.user_id=users.id"
	posts = db.query_db(query)
	db = connectToMySQL('jam_space')
	query = "SELECT comments.id, comments.content, comments.created_at, comments.user_id, users.username, posts.id AS post_id FROM comments LEFT JOIN users ON comments.user_id=users.id LEFT JOIN posts ON comments.post_id=posts.id"
	comments = db.query_db(query)

	return render_template('index.html', posts=posts, comments=comments)

@app.route('/logout')
def logout():
	session.clear()
	return redirect('/')

@app.route('/post', methods=['POST'])
def post():
	db = connectToMySQL('jam_space')
	if request.form.get('post') is not None:
		query = 'INSERT INTO posts (content, user_id, created_at, updated_at) VALUES (%(content)s, %(user_id)s, NOW(), NOW())'
		data = {
			'content': request.form['content'],
			'user_id': session['id']
		}
		db.query_db(query, data)
		return redirect('/dashboard')
	elif request.form.get('comment') is not None:
		db = connectToMySQL('jam_space')
		query = "INSERT INTO comments (content, user_id, post_id, created_at, updated_at) VALUES (%(content)s, %(user_id)s, %(post_id)s, NOW(), NOW())"
		data = {
			'content': request.form['content'],
			'user_id': session['id'],
			'post_id': request.form['post_id']
		}
		db.query_db(query, data)
		return redirect('/dashboard')


@app.route('/deleteComment', methods=['POST'])
def deleteComment():

	db = connectToMySQL('jam_space')
	if request.form.get('id') is not None:
		query = ('DELETE FROM comments WHERE id = %(id)s and user_id = %(userid)s')
		data = {
			"id": request.form.get('id'),
			"userid" : session['id']
		}
		db.query_db(query, data)
		return redirect('/dashboard')
	else: 
		return redirect('/dashboard')

@app.route('/deletePost', methods=['POST'])
def deletePost():

	db = connectToMySQL('jam_space')
	if request.form.get('id') is not None:
		query = ('DELETE FROM posts WHERE id = %(id)s and user_id = %(userid)s')
		data = {
			"id": request.form.get('id'),
			"userid" : session['id']
		}
		db.query_db(query, data)
		return redirect('/dashboard')
	else: 
		return redirect('/dashboard')


app.run(debug=True)
