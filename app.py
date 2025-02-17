import os
import zipfile
from flask import Flask, request, redirect, url_for, render_template, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField, PasswordField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Use a secure random key in production
app.config['UPLOAD_FOLDER'] = 'data'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16 MB

# User management
login_manager = LoginManager()
login_manager.init_app(app)

# Dummy user store
users = {'user': {'password': 'password'}}  # Replace with a database in production

class User(UserMixin):
    def __init__(self, username):
        self.username = username

@login_manager.user_loader
def load_user(username):
    return User(username) if username in users else None

# Form for user login
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Form for uploading ZIP files
class UploadForm(FlaskForm):
    site_name = StringField('Site/API Name', validators=[DataRequired()])
    zip_file = FileField('ZIP File', validators=[DataRequired()])
    submit = SubmitField('Upload')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('upload'))
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        site_name = form.site_name.data
        zip_file = form.zip_file.data

        # Create a directory for the site
        site_path = os.path.join(app.config['UPLOAD_FOLDER'], site_name)
        os.makedirs(site_path, exist_ok=True)

        # Save the uploaded ZIP file
        zip_file_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_file.filename)
        zip_file.save(zip_file_path)

        # Extract the ZIP file
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(site_path)

        # Provide the URL to access the running project
        return f'Project running at <a href="/site/{site_name}">/site/{site_name}</a>'

    return render_template('upload.html', form=form)

@app.route('/site/<site_name>')
@login_required
def site(site_name):
    return f'You are viewing the site: {site_name}'

@app.route('/')
def index():
    return redirect(url_for('login'))

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)