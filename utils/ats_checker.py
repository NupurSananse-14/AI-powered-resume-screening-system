import os
import re
import spacy
from collections import Counter

# Load the spaCy model. This is now essential for dynamic extraction.
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model... (this will only happen once)")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Our trusted database of known skills.
SKILLS_DB = [
    'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'swift', 'kotlin', 'go', 
    'typescript', 'sql', 'r', 'perl', 'scala', 'rust', 'dart', 'lua', 'html', 'css', 'react', 
    'angular', 'vue', 'django', 'flask', 'ruby on rails', 'spring', 'express.js', 'asp.net', 
    'laravel', 'node.js', 'svelte', 'next.js', 'gatsby', 'mysql', 'postgresql', 'mongodb', 
    'sqlite', 'redis', 'oracle', 'sql server', 'mariadb', 'cassandra', 'dynamodb', 'firebase',
    'aws', 'azure', 'google cloud', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'terraform',
    'ansible', 'aws lambda', 'aws ec2', 'aws s3', 'ci/cd', 'devops', 'numpy', 'pandas', 
    'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'matplotlib', 'seaborn', 'jupyter', 
    'machine learning', 'data analysis', 'deep learning', 'nlp', 'natural language processing', 
    'data visualization', 'statistics', 'big data', 'spark', 'hadoop', 'opencv', 'ios', 
    'android', 'react native', 'flutter', 'xamarin', 'api', 'rest', 'graphql', 'json', 'xml', 
    'agile', 'scrum', 'jira', 'linux', 'unix', 'shell scripting', 'powershell', 'cybersecurity', 
    'blockchain', 'testing', 'selenium'
]

# Common non-skill words to filter out from dynamic extraction.
# This list has been expanded to be more effective.
COMMON_BUSINESS_WORDS = [
    'experience', 'team', 'work', 'project', 'role', 'responsibilities', 'company', 'candidate',
    'skill', 'skills', 'ability', 'knowledge', 'understanding', 'requirement', 'requirements',
    'degree', 'equivalent', 'solution', 'solutions', 'system', 'systems', 'application', 'applications',
    'development', 'design', 'management', 'analysis', 'business', 'communication',
    # Added from user feedback to filter more noise
    'intern', 'position', 'benefits', 'perks', 'stipend', 'day', 'lookout', 'outputs',
    'space', 'we', 'you', 'cv', 'intro', 'familiarity', 'good', 'strong', 'debugging skills',
    'problem-solving', 'insights', 'workflows', 'refinement', 'bonus', 'wherever', 'perks'
]

def extract_skills_from_db(text):
    """Extracts skills found in our curated SKILLS_DB."""
    found_skills = set()
    text_lower = text.lower()
    for skill in SKILLS_DB:
        pattern = r'(?<![a-zA-Z])' + re.escape(skill) + r'(?![a-zA-Z])'
        if re.search(pattern, text_lower):
            found_skills.add(skill)
    return found_skills

def extract_dynamic_skills(text):
    """
    Dynamically extracts potential skills (nouns and noun phrases) from text.
    This version includes stricter filtering to remove noise.
    """
    doc = nlp(text)
    potential_skills = set()
    
    # We look for "noun chunks" - sequences of nouns and adjectives.
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower().strip()

        # --- Stricter Filtering Logic ---
        # 1. Skip if the exact phrase is a common business term
        if chunk_text in COMMON_BUSINESS_WORDS:
            continue
        
        # 2. Skip if it's too long (likely a full sentence fragment)
        if len(chunk_text.split()) > 4:
            continue

        # 3. Skip if it doesn't contain any letters (e.g., just numbers or symbols)
        if not any(char.isalpha() for char in chunk_text):
            continue

        # 4. Skip if the core of the chunk (the "root" word) is a common business word
        if chunk.root.text.lower() in COMMON_BUSINESS_WORDS:
            continue

        potential_skills.add(chunk_text)
                
    return potential_skills

def analyze_resume(resume_text, job_description, filename):
    """
    Analyzes the resume using a hybrid approach:
    1. Dynamically finds skills in the JD.
    2. Matches those skills against the resume.
    """
    scores = {'extractability': 0, 'formatting': 0, 'keywords': 0, 'file_format': 0}
    details = {
        'extractability': 'Could not extract text or text was too short.',
        'formatting': 'No standard sections found.',
        'keywords': 'Keyword analysis not performed.',
        'file_format': 'File format not recognized.'
    }

    # --- 1. Text Extractability (40%) ---
    if not resume_text or len(resume_text) < 150:
        return {"total_score": 0, "scores": scores, "details": details, "matched_keywords": [], "missing_keywords": []}
    
    scores['extractability'] = 40
    details['extractability'] = 'Text was successfully and cleanly extracted.'
    resume_lower = resume_text.lower()

    # --- 2. Standard Formatting (30%) ---
    standard_sections = ['summary', 'objective', 'experience', 'education', 'skills', 'projects']
    found_sections = sum(1 for section in standard_sections if section in resume_lower)
    if found_sections >= 3:
        scores['formatting'] = 30
        details['formatting'] = f'Excellent structure with {found_sections} standard sections found.'
    elif found_sections >= 1:
        scores['formatting'] = 15
        details['formatting'] = f'Good structure with {found_sections} standard sections found.'

    # --- 3. HYBRID SKILL ANALYSIS (20%) ---
    # Step 3.1: Get high-confidence skills from our DB
    jd_skills_from_db = extract_skills_from_db(job_description)
    
    # Step 3.2: Dynamically discover other potential skills from the JD
    jd_dynamic_skills = extract_dynamic_skills(job_description)
    
    # Step 3.3: Combine them into a final list of required skills
    required_skills = jd_skills_from_db.union(jd_dynamic_skills)

    if not required_skills:
        details['keywords'] = 'Could not identify any relevant skills in the job description.'
        matched_skills, missing_skills = set(), set()
    else:
        # Step 3.4: Now, we check the RESUME for this complete list of skills
        resume_skills_from_db = extract_skills_from_db(resume_text)
        # We also extract dynamically from the resume to catch variations
        resume_dynamic_skills = extract_dynamic_skills(resume_text)
        total_resume_skills = resume_skills_from_db.union(resume_dynamic_skills)
        
        matched_skills = required_skills.intersection(total_resume_skills)
        missing_skills = required_skills - matched_skills
        
        # Avoid division by zero
        if len(required_skills) == 0:
            match_percentage = 0
        else:
            match_percentage = (len(matched_skills) / len(required_skills)) * 100

        scores['keywords'] = round((match_percentage / 100) * 20)
        details['keywords'] = f'Matched {len(matched_skills)} of {len(required_skills)} required skills ({round(match_percentage)}%).'

    # --- 4. File Format (10%) ---
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.pdf': scores['file_format'] = 10; details['file_format'] = 'PDF format used (Preferred).'
    elif ext in ['.docx', '.doc']: scores['file_format'] = 5; details['file_format'] = 'DOCX/DOC format used (Acceptable).'

    # --- Final Calculation ---
    total_score = sum(scores.values())
    report = {
        "total_score": total_score, "scores": scores, "details": details,
        "matched_keywords": sorted(list(matched_skills)),
        "missing_keywords": sorted(list(missing_skills)),
    }
    return report

