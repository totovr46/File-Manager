from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
import os
import psutil
import time 


app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ROOT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database')

def get_files_and_directories(path):
    files = []
    directories = []
    for file_or_dir in os.listdir(path):
        if os.path.isfile(os.path.join(path, file_or_dir)):
            files.append(file_or_dir)
        else:
            directories.append(file_or_dir)
    return files, directories

def get_resource_usage():
    # Cpu Usage
    cpu_percent = psutil.cpu_percent(interval=1)

    # RAM Usage
    ram_percent = psutil.virtual_memory().percent
    
    # Network Usage (in byte)
    net_io_counters = psutil.net_io_counters()
    net_sent = net_io_counters.bytes_sent
    net_recv = net_io_counters.bytes_recv
    time.sleep(1)
    net_io_counters = psutil.net_io_counters()
    net_sent_now = net_io_counters.bytes_sent
    net_recv_now = net_io_counters.bytes_recv

    # Mbit/s
    net_sent_speed = round(((net_sent_now - net_sent) * 8) / (1024 * 1024), 2)
    net_recv_speed = round(((net_recv_now - net_recv) * 8) / (1024 * 1024), 2)
    
    # Disk Usage
    disk_usage = psutil.disk_usage('/')
    disk_total = round(disk_usage.total / (1024 ** 3), 2)
    disk_used = round(disk_usage.used / (1024 ** 3), 2)  
    return cpu_percent, ram_percent, net_sent_speed, net_recv_speed, disk_total, disk_used

@app.route('/')
def login():
    if 'username' in session:
        return redirect(url_for('file_browser'))
    return render_template('login.html')

@app.route('/auth', methods=['POST'])
def auth():
    if request.form['username'] == 'admin' and request.form['password'] == 'admin': #MODIFY USERNAME AND PASSWORD!!!
        session['username'] = request.form['username']
        return redirect(url_for('file_browser'))
    else:
        return render_template('login.html', error='Credenziali errate')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/file_browser')
def file_browser():
    if 'username' not in session:
        return redirect(url_for('login'))
    path = os.path.join(ROOT_FOLDER, request.args.get('path', ''))
    # Prevent navigation to folders behind root folder
    if not os.path.realpath(path).startswith(os.path.realpath(ROOT_FOLDER)):
        return redirect(url_for('file_browser'))
    if not os.path.exists(path):
        os.makedirs(path)
    files, directories = get_files_and_directories(path)
    return render_template('file_browser.html', files=files, directories=directories, path=path, root=ROOT_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = file.filename
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], request.form['path'], filename)
            file.save(upload_path)
    return redirect(url_for('file_browser', path=request.form['path']))

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    path = os.path.join(ROOT_FOLDER, request.args.get('path', ''))
    return send_from_directory(path, filename, as_attachment=True)

@app.route('/create_folder', methods=['POST'])
def create_folder():
    if 'username' not in session:
        return redirect(url_for('login'))
    path = os.path.join(ROOT_FOLDER, request.form['path'], request.form['folder_name'])
    os.makedirs(path)
    return redirect(url_for('file_browser', path=request.form['path']))

@app.route('/delete', methods=['POST'])
def delete_file():
    if 'username' not in session:
        return redirect(url_for('login'))
    filename = request.form['filename']
    path = os.path.join(ROOT_FOLDER, request.form['path'], filename)
    os.remove(path)
    return redirect(url_for('file_browser', path=request.form['path']))

@app.route('/monitor')
def monitor():
    cpu_percent, ram_percent, net_sent_speed, net_recv_speed, disk_total, disk_used = get_resource_usage()
    return render_template('monitor.html', cpu_percent=cpu_percent, ram_percent=ram_percent, net_sent_speed=net_sent_speed, net_recv_speed=net_recv_speed, disk_total=disk_total, disk_used=disk_used)

if __name__ == '__main__':
    app.run(host='yourip', port=5000, debug=True) #MODIFY WITH YOUR PC PRIVATE IP!!!!!!
