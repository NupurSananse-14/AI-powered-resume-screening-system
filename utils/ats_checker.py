# utils/ats_checker.py

import spacy
from collections import Counter

# Load the small English model.
# Make sure you have run: python -m spacy download en_core_web_sm
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model... (this will only happen once)")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def preprocess_text(text):
    """
    Cleans and preprocesses the text:
    - Converts to lowercase
    - Removes stopwords and punctuation
    - Lemmatizes words (reduces them to their root form)
    """
    doc = nlp(text.lower())
    processed_tokens = [
        token.lemma_ for token in doc 
        if not token.is_stop and not token.is_punct and not token.is_space
    ]
    return processed_tokens

def get_keywords(text):
    """
    Extracts relevant keywords (nouns, proper nouns, adjectives) from text.
    """
    doc = nlp(text.lower())
    keywords = [
        token.lemma_ for token in doc 
        if not token.is_stop and not token.is_punct and 
        (token.pos_ in ["NOUN", "PROPN", "ADJ"])
    ]
    return set(keywords)

def check_ats_compatibility(resume_text, job_description):
    """
    Compares the resume to the job description and returns a compatibility report.
    """
    # Preprocess both texts
    resume_tokens = preprocess_text(resume_text)

    # Extract keywords from the job description
    jd_keywords = get_keywords(job_description)

    # Find which keywords from the job description are present in the resume
    matched_keywords = jd_keywords.intersection(resume_tokens)

    # Calculate the score
    if not jd_keywords:
        score = 0
    else:
        score = round((len(matched_keywords) / len(jd_keywords)) * 100)

    missing_keywords = jd_keywords - matched_keywords

    # Create a report
    report = {
        "score": score,
        "matched_keywords": sorted(list(matched_keywords)),
        "missing_keywords": sorted(list(missing_keywords)),
        "jd_keyword_count": len(jd_keywords),
        "matched_keyword_count": len(matched_keywords)
    }

    return report