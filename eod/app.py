from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_apscheduler import APScheduler
import pandas as pd
import os
import smtplib
import zipfile
import uuid
from email.message import EmailMessage
from datetime import datetime
from werkzeug.utils import secure_filename
from pdf_generator import generate_pdf_for_employee

app = Flask(__name__)
app.secret_key = 'your-secret-key'
UPLOAD_FOLDER = 'uploads'
PDF_FOLDER = 'generated_reports'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PDF_FOLDER'] = PDF_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

scheduler = APScheduler()
scheduler.api_enabled = True
scheduler.init_app(app)
scheduler.start()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['csv', 'xls', 'xlsx']

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password or len(password) != 16:
        flash("Invalid credentials format.", "danger")
        return redirect(url_for('home'))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls()
            server.login(email, password)
    except smtplib.SMTPAuthenticationError:
        flash("Invalid email or app password.", "danger")
        return redirect(url_for('home'))
    except (smtplib.SMTPConnectError, TimeoutError) as e:
        flash("Could not connect to Gmail SMTP. Please check internet or firewall.", "danger")
        return redirect(url_for('home'))
    except Exception as e:
        flash(f"Unexpected error: {e}", "danger")
        return redirect(url_for('home'))

    session['email'] = email
    session['app_password'] = password
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('home'))
    table_html = session.get('table_html')
    return render_template('dashboard.html', email=session['email'], table_html=table_html)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash("No file uploaded.", "danger")
        return redirect(url_for('dashboard'))
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        flash("Invalid file format.", "danger")
        return redirect(url_for('dashboard'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    session['uploaded_file'] = filepath

    df = pd.read_excel(filepath) if filename.endswith(('xls', 'xlsx')) else pd.read_csv(filepath)
    session['data'] = df.to_dict()
    session['table_html'] = df.to_html(classes='table table-bordered text-sm')
    flash("File uploaded and preview ready.", "success")
    return redirect(url_for('dashboard'))

@app.route('/generate_reports')
def generate_reports():
    if 'data' not in session:
        flash("No data to generate report.", "danger")
        return redirect(url_for('dashboard'))

    df = pd.DataFrame(session['data'])
    session['pdf_files'] = []

    for emp_id in df['EmployeeID'].unique():
        emp_data = df[df['EmployeeID'] == emp_id]
        filename = f"{emp_id}_{uuid.uuid4().hex[:6]}.pdf"
        filepath = os.path.join(app.config['PDF_FOLDER'], filename)
        generate_pdf_for_employee(emp_data, filepath)
        session['pdf_files'].append(filepath)

    flash("Reports generated successfully.", "success")
    return redirect(url_for('dashboard'))

@app.route('/send_reports', methods=['POST'])
def send_reports():
    receiver = request.form.get('receiver')
    send_option = request.form.get('send_option')

    if not receiver or 'pdf_files' not in session:
        flash("Missing receiver email or reports.", "danger")
        return redirect(url_for('dashboard'))

    try:
        msg = EmailMessage()
        msg['Subject'] = 'EOD Reports'
        msg['From'] = session['email']
        msg['To'] = receiver

        if send_option == 'zip':
            zip_path = os.path.join(PDF_FOLDER, f"EOD_Reports_{uuid.uuid4().hex[:5]}.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for pdf in session['pdf_files']:
                    zipf.write(pdf, os.path.basename(pdf))
            with open(zip_path, 'rb') as f:
                msg.add_attachment(f.read(), maintype='application', subtype='zip', filename=os.path.basename(zip_path))
        else:
            for pdf in session['pdf_files']:
                with open(pdf, 'rb') as f:
                    msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=os.path.basename(pdf))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(session['email'], session['app_password'])
            server.send_message(msg)

        flash("Reports sent successfully.", "success")
    except Exception as e:
        flash(f"Failed to send email: {e}", "danger")

    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

def auto_generate_and_send():
    # dummy function for future scheduler logic
    pass

scheduler.add_job(id='daily_job', func=auto_generate_and_send, trigger='cron', hour=18, minute=0)

if __name__ == '__main__':
    app.run(debug=True)
