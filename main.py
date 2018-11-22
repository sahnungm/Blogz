from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://Blogz:hooyo@localhost:8889/Blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = "lolcopter"

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(1000))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user'] = username
            return redirect('/newpost')
        elif not(user):
            flash('User does not exit', 'error')
            return render_template('login.html')
        else:
            flash('User password incorrect', 'error')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        name_message = ""

        if name_error(username) or password_error(password) or match_error(password, verify):
            if name_error(username):
                username = ""
                name_message = "Please enter a valid username"
            return render_template('signup.html', username=username, name_error=name_error(username), name_message=name_message, password_error=password_error(password), match_error=match_error(password, verify))

        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['user'] = username
            return redirect ('/newpost')
        else:
            name_message = "User already exists"
            return render_template('signup.html', name_error=True, name_message=name_message)

    return render_template('signup.html')

def name_error(username):
    if len(username) < 3:
        return True
    elif " " in username:
        return True
    else:
        return False

def password_error(password):
    if len(password) < 3:
        return True
    else:
        return False

def match_error(password, verify):
    if password == verify:
        return False
    else:
        return True

@app.route('/blog', methods=['GET', 'POST'])
def blogs():

    id = request.args.get("id")
    if id:
        post = Blog.query.filter_by(id=id).first()
        return render_template('post.html', title=post.title, body=post.body, user=post.owner)

    
    posts = []
    user = request.args.get("user")
    if user:
        post_ids = []
        og_posts = Blog.query.filter_by(owner_id=user)
        for post in og_posts:
            post_ids.append(post.id)
        post_ids.reverse()
        for num in post_ids:
            posts.append(Blog.query.filter_by(id=num).first())        
    else:
        count = len(Blog.query.all())
        for num in range(count, 0, -1):
            posts.append(Blog.query.filter_by(id=num).first())
    return render_template('blog.html', posts = posts)

@app.route('/newpost', methods=['GET', 'POST'])
def add_post():

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        user = User.query.filter_by(username=session['user']).first()
        title_error = True
        body_error = True
        if title:
            title_error = False
        if body:
            body_error = False

        if title_error or body_error:
            return render_template("newpost.html", title=title, body=body, title_error=title_error, body_error=body_error)
        else:
            new_post = Blog(title, body, user)
            db.session.add(new_post)
            db.session.commit()
            return redirect("/blog?id={0}".format(new_post.id))
        

    return render_template("newpost.html")

@app.route('/index')
def index():
    users = User.query.all()

    return render_template("index.html", users=users)

@app.route('/logout', methods=['POST'])
def logout():
    del session['user']
    return redirect('/blog')

@app.before_request
def require_login():
    allowed_routes = ['login', 'index', 'blogs', 'signup']
    if request.endpoint not in allowed_routes and 'user' not in session:
        return redirect('/login')

if __name__ == "__main__":
    app.run()