import os
from flask import Flask, request, render_template, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from utils.pdf_parser import extract_text
from utils.ats_checker import check_ats_compatibility


# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_mb(file_size):
    """Convert file size to MB"""
    return round(file_size / (1024 * 1024), 2)

@app.route('/')
def index():
    """Main upload page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        # Check if file was uploaded
        if 'resume' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        file = request.files['resume']
        job_description = request.form.get('job_description', '').strip()
        
        # Check if filename is empty
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        # Validate job description
        if not job_description:
            flash('Job description is required', 'error')
            return redirect(url_for('index'))
        
        # Check file type
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload PDF or DOCX files only.', 'error')
            return redirect(url_for('index'))
        
        # Check file size
        file.seek(0, 2)  # Seek to end of file
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > MAX_FILE_SIZE:
            flash(f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB', 'error')
            return redirect(url_for('index'))
        
        if file_size == 0:
            flash('Empty file uploaded', 'error')
            return redirect(url_for('index'))
        
        # Save file
        filename = secure_filename(file.filename)
        # Add timestamp to avoid filename conflicts
        import time
        timestamp = str(int(time.time()))
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}{ext}"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # 1. Extract text from the resume
        resume_text = extract_text(filepath, unique_filename)
        if not resume_text:
            flash('Could not extract text from the file. It may be empty or corrupted.', 'error')
            return redirect(url_for('index'))
            
        # 2. Perform the ATS analysis
        ats_report = check_ats_compatibility(resume_text, job_description)
        
        # 3. Keep your original file_info dictionary
        file_info = {
            'original_filename': file.filename,
            'saved_filename': unique_filename,
            'file_size_mb': get_file_size_mb(file_size),
            'file_type': filename.rsplit('.', 1)[1].lower()
        }
        
        flash('File uploaded successfully!', 'success')
        
        # 4. Pass ALL data (ats_report and file_info) to the results page
        return render_template('results.html', 
                               report=ats_report,
                               file_info=file_info, 
                               job_description=job_description)
        
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Resume ATS Checker is running'})

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash(f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Development settings
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)