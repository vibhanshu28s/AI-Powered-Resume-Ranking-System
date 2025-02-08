
from flask import Flask, request, render_template
import os
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
import re
import PyPDF2
import docx

app = Flask(__name__)


# Function to preprocess text
def preprocess_text(text):
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = text.lower()
    tokens = nltk.word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    return ' '.join(tokens)


# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + " "
    return text


# Function to extract text from DOCX
def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + " "
    return text


# Function to rank resumes
def rank_resumes(job_description, resumes):
    job_description = preprocess_text(job_description)
    processed_resumes = []
    for resume in resumes:
        resume_path = os.path.join('uploads', resume.filename)
        resume.save(resume_path)
        if resume.filename.endswith('.pdf'):
            text = extract_text_from_pdf(resume_path)
        elif resume.filename.endswith('.docx'):
            text = extract_text_from_docx(resume_path)
        else:
            continue
        processed_resumes.append(preprocess_text(text))

    documents = [job_description] + processed_resumes
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    ranked_indices = np.argsort(cosine_similarities)[::-1]
    ranked_resumes = [os.path.basename(resumes[i].filename) for i in ranked_indices]
    ranked_scores = cosine_similarities[ranked_indices]

    # Create a list of tuples (resume, score)
    ranked_results = list(zip(ranked_resumes, ranked_scores))

    # Clean up uploaded files
    for resume in resumes:
        resume_path = os.path.join('uploads', resume.filename)
        if os.path.exists(resume_path):
            os.remove(resume_path)

    return ranked_results


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    job_description = request.form['job_description']
    resumes = request.files.getlist('resumes')
    ranked_results = rank_resumes(job_description, resumes)
    return render_template('results.html', ranked_results=ranked_results)


if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)