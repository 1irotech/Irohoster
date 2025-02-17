from flask import Flask, render_template, request, redirect, url_for, session, flash
import subprocess
import os

app = Flask(__name__)
app.secret_key = 'iroff1'  # Change this to a random secret key
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory user storage (for demonstration purposes)
users = {}
# Store bot processes and their states
bot_processes = {}
bot_states = {}

# Owner credentials
OWNER_PASSWORD = 'bajsal11'  # Change this to a secure password

@app.route('/')
def home_page():  # Renamed the function to avoid conflict
    if 'username' in session:
        return render_template('home.html')  # Render the home page if logged in
    return render_template('login.html')  # Otherwise, show the login page

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users:
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('register'))
        
        users[username] = password  # Store the username and password
        flash('Registration successful! You can now log in.')
        return redirect(url_for('home_page'))  # Updated to match the new function name
    
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    if username in users and users[username] == password:
        session['username'] = username
        return redirect(url_for('upload'))
    
    flash('Invalid credentials. Please try again.')
    return redirect(url_for('home_page'))  # Updated to match the new function name

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('home_page'))

    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part', 400
        file = request.files['file']
        if file.filename == '':
            return 'No selected file', 400
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            # Install required modules if requirements.txt exists
            requirements_path = os.path.join(app.config['UPLOAD_FOLDER'], 'requirements.txt')
            if os.path.exists(requirements_path):
                subprocess.run(['pip', 'install', '-r', requirements_path])

            # Start the bot script in a separate thread
            process = subprocess.Popen(['python', filepath])
            bot_processes[file.filename] = process
            bot_states[file.filename] = 'running'

            return redirect(url_for('manage_bots'))

    return render_template('upload.html')

@app.route('/manage_bots')
def manage_bots():
    if 'username' not in session:
        return redirect(url_for('home_page'))

    return render_template('manage_bots.html', bots=bot_processes.keys(), states=bot_states)

@app.route('/stop_bot/<bot_name>')
def stop_bot(bot_name):
    if bot_name in bot_processes:
        bot_processes[bot_name].terminate()  # Stop the bot process
        bot_states[bot_name] = 'stopped'
    return redirect(url_for('manage_bots'))

@app.route('/restart_bot/<bot_name>')
def restart_bot(bot_name):
    if bot_name in bot_processes:
        bot_processes[bot_name].terminate()  # Stop the bot process
        bot_states[bot_name] = 'stopped'
        
        # Restart the bot
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], bot_name)
        process = subprocess.Popen(['python', filepath])
        bot_processes[bot_name] = process
        bot_states[bot_name] = 'running'
    return redirect(url_for('manage_bots'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home_page'))

@app.route('/owner_panel', methods=['GET', 'POST'])
def owner_panel():
    if request.method == 'POST':
        password = request.form['password']
        if password == OWNER_PASSWORD:
            # Fetch user statistics
            user_count = len(users)  # Assuming 'users' is a dictionary storing registered users
            return render_template('owner_panel.html', user_count=user_count, users=users)
        else:
            flash('Incorrect password. Access denied.')
            return redirect(url_for('home_page'))

    return render_template('owner_login.html')

@app.route('/delete_user/<username>')
def delete_user(username):
    if username in users:
        del users[username]  # Remove user from the dictionary
        flash(f'User  {username} has been deleted.')
    else:
        flash('User  not found.')
    return redirect(url_for('owner_panel'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)  # Set host and port
