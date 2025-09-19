import spacy
import os

# Load the small English model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model... (this will only happen once)")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def get_keywords(text):
    """Extracts relevant keywords (nouns, proper nouns, adjectives) from text."""
    doc = nlp(text.lower())
    keywords = [
        token.lemma_ for token in doc 
        if not token.is_stop and not token.is_punct and 
        (token.pos_ in ["NOUN", "PROPN", "ADJ"])
    ]
    return set(keywords)

def analyze_resume(resume_text, job_description, filename):
    """
    Analyzes the resume based on a multi-criteria scoring system.
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
    # Checks if the text is substantial enough to be considered a valid resume.
    if resume_text and len(resume_text) > 150:
        scores['extractability'] = 40
        details['extractability'] = 'Text was successfully and cleanly extracted.'
    else:
        # If no text, we cannot proceed with other checks.
        total_score = sum(scores.values())
        return {
            "total_score": total_score, "scores": scores, "details": details,
            "matched_keywords": [], "missing_keywords": []
        }

    # --- 2. Standard Formatting (30%) ---
    # Checks for the presence of common resume section headers.
    standard_sections = [
        'summary', 'objective', 'experience', 'education', 'skills', 
        'projects', 'certifications', 'awards', 'references', 'work history'
    ]
    found_sections = 0
    resume_lower = resume_text.lower()
    for section in standard_sections:
        if section in resume_lower:
            found_sections += 1
    
    if found_sections >= 4:
        scores['formatting'] = 30
        details['formatting'] = f'Excellent structure with {found_sections} standard sections found.'
    elif found_sections >= 2:
        scores['formatting'] = 20
        details['formatting'] = f'Good structure with {found_sections} standard sections found.'
    elif found_sections >= 1:
        scores['formatting'] = 10
        details['formatting'] = f'Basic structure with only {found_sections} standard section found.'


    # --- 3. Keyword Density & Matching (20%) ---
    # Re-purposed to be the keyword match score, scaled to 20 points.
    resume_tokens = set([token.lemma_ for token in nlp(resume_lower) if not token.is_stop and not token.is_punct])
    jd_keywords = get_keywords(job_description)
    
    if not jd_keywords:
        match_percentage = 0
        details['keywords'] = 'Could not extract any keywords from the job description.'
        matched_keywords = []
        missing_keywords = []
    else:
        matched_keywords = jd_keywords.intersection(resume_tokens)
        missing_keywords = jd_keywords - matched_keywords
        match_percentage = (len(matched_keywords) / len(jd_keywords)) * 100
        scores['keywords'] = round((match_percentage / 100) * 20)
        details['keywords'] = f'Matched {len(matched_keywords)} of {len(jd_keywords)} keywords ({round(match_percentage)}%).'


    # --- 4. File Format (10%) ---
    # Prefers PDF over other formats.
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.pdf':
        scores['file_format'] = 10
        details['file_format'] = 'PDF format used (Preferred).'
    elif ext in ['.docx', '.doc']:
        scores['file_format'] = 5
        details['file_format'] = 'DOCX/DOC format used (Acceptable).'
    else:
        scores['file_format'] = 0
        details['file_format'] = 'Unsupported file format.'

    # --- Final Calculation ---
    total_score = sum(scores.values())
    
    report = {
        "total_score": total_score,
        "scores": scores,
        "details": details,
        "matched_keywords": sorted(list(matched_keywords)),
        "missing_keywords": sorted(list(missing_keywords)),
    }
    
    return report