import os
import re

# This version uses a simple, reliable dictionary of skills.

# A curated list of relevant technical skills.
SKILLS_DB = [
    # Programming Languages
    'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'swift', 'kotlin', 'go', 
    'typescript', 'sql', 'r', 'perl', 'scala', 'rust', 'dart', 'lua', 'html', 'css',

    # Web Frameworks (Frontend & Backend)
    'react', 'angular', 'vue', 'django', 'flask', 'ruby on rails', 'spring', 'express.js', 
    'asp.net', 'laravel', 'node.js', 'svelte', 'next.js', 'gatsby',

    # Databases
    'mysql', 'postgresql', 'mongodb', 'sqlite', 'redis', 'oracle', 'sql server', 'mariadb',
    'cassandra', 'dynamodb', 'firebase',

    # Cloud & DevOps
    'aws', 'azure', 'google cloud', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git',
    'terraform', 'ansible', 'aws lambda', 'aws ec2', 'aws s3', 'ci/cd', 'devops',

    # Data Science & Machine Learning
    'numpy', 'pandas', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'matplotlib',
    'seaborn', 'jupyter', 'machine learning', 'data analysis', 'deep learning', 'nlp',
    'natural language processing', 'data visualization', 'statistics', 'big data', 'spark', 'hadoop',
    'opencv',
    
    # Mobile Development
    'ios', 'android', 'react native', 'flutter', 'xamarin',

    # Other Tools & Concepts
    'api', 'rest', 'graphql', 'json', 'xml', 'agile', 'scrum', 'jira', 'linux', 'unix',
    'shell scripting', 'powershell', 'cybersecurity', 'blockchain', 'testing', 'selenium'
]

def extract_skills(text):
    """Extracts skills from text based on our SKILLS_DB using robust regex."""
    found_skills = set()
    text_lower = text.lower()
    
    for skill in SKILLS_DB:
        # This pattern ensures we match whole words only, avoiding partial matches.
        pattern = r'(?<![a-zA-Z])' + re.escape(skill) + r'(?![a-zA-Z])'
        if re.search(pattern, text_lower):
            found_skills.add(skill)
            
    return found_skills

def analyze_resume(resume_text, job_description, filename):
    """
    Analyzes the resume based on the original multi-criteria scoring system.
    """
    scores = {
        'extractability': 0,
        'formatting': 0,
        'keywords': 0,
        'file_format': 0,
    }
    
    details = {
        'extractability': 'Could not extract text or text was too short.',
        'formatting': 'No standard sections like "Experience" or "Education" found.',
        'keywords': 'Keyword analysis was not performed.',
        'file_format': 'File format not recognized.',
    }

    # --- 1. Text Extractability (40%) ---
    if resume_text and len(resume_text) > 150:
        scores['extractability'] = 40
        details['extractability'] = 'Text was successfully and cleanly extracted.'
    else:
        # If no text, we cannot proceed.
        return {
            "total_score": 0, "scores": scores, "details": details,
            "matched_keywords": [], "missing_keywords": []
        }

    # --- 2. Standard Formatting (30%) ---
    standard_sections = [
        'summary', 'objective', 'experience', 'education', 'skills', 
        'projects', 'certifications', 'awards'
    ]
    found_sections = 0
    resume_lower = resume_text.lower()
    for section in standard_sections:
        if section in resume_lower:
            found_sections += 1
    
    if found_sections >= 3:
        scores['formatting'] = 30
        details['formatting'] = f'Excellent structure with {found_sections} standard sections found.'
    elif found_sections >= 1:
        scores['formatting'] = 15
        details['formatting'] = f'Good structure with {found_sections} standard sections found.'

    # --- 3. Keyword/Skill Matching (20%) ---
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(job_description)
    
    if not jd_skills:
        details['keywords'] = 'Could not identify any relevant skills in the job description.'
        matched_skills = []
        missing_skills = list(resume_skills)
    else:
        matched_skills = jd_skills.intersection(resume_skills)
        missing_skills = jd_skills - matched_skills
        match_percentage = (len(matched_skills) / len(jd_skills)) * 100
        scores['keywords'] = round((match_percentage / 100) * 20)
        details['keywords'] = f'Matched {len(matched_skills)} of {len(jd_skills)} required skills ({round(match_percentage)}%).'

    # --- 4. File Format (10%) ---
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.pdf':
        scores['file_format'] = 10
        details['file_format'] = 'PDF format used (Preferred).'
    elif ext in ['.docx', '.doc']:
        scores['file_format'] = 5
        details['file_format'] = 'DOCX/DOC format used (Acceptable).'

    # --- Final Calculation ---
    total_score = sum(scores.values())
    
    report = {
        "total_score": total_score,
        "scores": scores,
        "details": details,
        "matched_keywords": sorted(list(matched_skills)),
        "missing_keywords": sorted(list(missing_skills)),
    }
    
    return report

