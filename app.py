import os, json, random
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
load_dotenv(override=True)
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'local-dev-key-change-before-deploy')
LEVELS = ['Beginner', 'Medium', 'Advanced']
QUESTION_COUNTS = [5, 10]
# Separate question banks ensure difficulty selection actually changes the questions.
QUESTION_BANK = {
'Python Developer': {
'Beginner': [
'What is the difference between a list and a tuple in Python?', 'What are Python variables and how do you assign a value?', 'Explain the difference between == and is.', 'How does a for loop work? Give a simple example.', 'What is a dictionary and when would you use one?', 'What is the purpose of if, elif, and else?', 'How do you define and call a function in Python?', 'What is the difference between int, float, str, and bool?', 'How do you handle an exception using try and except?', 'What is a Python module and how do you import one?'],
'Medium': [
'What is a decorator and when would you use one?', 'Explain the difference between shallow copy and deep copy.', 'What are list comprehensions? Give an example.', 'Explain *args and **kwargs.', 'What is the difference between an instance method, class method, and static method?', 'How do generators work and when are they useful?', 'What is a context manager and how does the with statement help?', 'How would you read a large text file without loading it all into memory?', 'Explain Python mutability with an example involving a list passed to a function.', 'How would you write unit tests for a function?'],
'Advanced': [
'Explain Python method resolution order (MRO) and how super() uses it.', 'How does the Global Interpreter Lock affect CPU-bound Python threads?', 'Compare multiprocessing, threading, and asyncio for different workloads.', 'How would you diagnose and reduce memory usage in a long-running Python service?', 'Explain descriptors and give a practical use case.', 'How do Python generators help build memory-efficient data pipelines?', 'How would you design a robust retry mechanism with exponential backoff?', 'Explain the trade-offs of using a metaclass.', 'How would you profile a slow Python application before optimizing it?', 'Design a thread-safe cache and explain its synchronization strategy.']},
'Data Analyst': {
'Beginner': [
'What is the difference between a row and a column in a table?', 'What is the difference between Excel and a database?', 'Explain mean, median, and mode.', 'What is a missing value and how can you identify one?', 'When would you use a bar chart instead of a line chart?', 'What does GROUP BY do in SQL?', 'What is the difference between INNER JOIN and LEFT JOIN?', 'What is a KPI? Give a business example.', 'What is the difference between categorical and numerical data?', 'Why should you check data for duplicates?'],
'Medium': [
'How would you decide whether to impute or remove missing values?', 'Write a SQL approach to find the second-highest salary.', 'Explain window functions and give a use case for ROW_NUMBER.', 'How would you investigate a sudden drop in weekly sales?', 'What is the difference between correlation and causation?', 'How would you detect and handle outliers in a dataset?', 'Explain the difference between a pivot table and GROUP BY aggregation.', 'How would you validate a dashboard before sharing it?', 'What is cohort analysis and when is it useful?', 'How would you combine data from multiple sources with inconsistent keys?'],
'Advanced': [
'Design an experiment to measure whether a new checkout flow improves conversion.', 'How would you explain a statistically significant result that has a tiny business impact?', 'Describe how Simpson’s paradox can mislead a business analysis.', 'How would you investigate a metric change caused by a possible tracking issue?', 'Design a data-quality monitoring plan for a daily sales pipeline.', 'How would you choose between a time-series model and a simple seasonal baseline?', 'Explain selection bias and how it could affect a customer-retention study.', 'How would you define and validate a north-star metric for a marketplace?', 'Describe a robust approach to measuring customer lifetime value.', 'How would you communicate uncertainty in a forecast to senior stakeholders?']},
'Machine Learning Engineer': {
'Beginner': [
'What is the difference between supervised and unsupervised learning?', 'What is the difference between classification and regression?', 'Why do we split data into training and test sets?', 'What is overfitting in machine learning?', 'What is a feature and what is a label?', 'Explain the purpose of a confusion matrix.', 'What is the difference between accuracy and precision?', 'Why do some models need feature scaling?', 'What is a decision tree in simple terms?', 'What is the purpose of a validation set?'],
'Medium': [
'Explain the bias-variance trade-off.', 'When would you choose F1-score over accuracy?', 'How does k-nearest neighbors make a prediction?', 'Explain how the elbow method helps choose K in K-means.', 'How does one-hot encoding work and when is it appropriate?', 'Why can data leakage produce misleading evaluation scores?', 'Compare random forest with a single decision tree.', 'How would you handle class imbalance?', 'What is cross-validation and why is it useful?', 'Explain gradient descent in the context of model training.'],
'Advanced': [
'How would you design a leakage-safe training and evaluation pipeline for time-dependent data?', 'Explain how calibration differs from ranking performance and why it matters.', 'How would you select a decision threshold when false negatives are more costly?', 'Describe strategies for monitoring model drift after deployment.', 'How would you debug a model that performs well offline but poorly in production?', 'Compare batch inference with online inference in terms of latency and reliability.', 'How would you build reproducible ML training with versioned data and artifacts?', 'Explain the trade-offs between target encoding and one-hot encoding for high-cardinality features.', 'How would you evaluate a model when labels arrive weeks after predictions?', 'Describe a safe deployment strategy for a new model, including rollback criteria.']}}

# Keep a small in-memory history to discourage Gemini from repeating recent questions.
RECENT_QUESTIONS = {}

def generate_questions_with_gemini(role, level, count):
    key = os.getenv('GEMINI_API_KEY')
    if not key:
        return None, 'Gemini API key is not configured. Add it to your .env file, then restart the app.'
    try:
        from google import genai
        client = genai.Client(api_key=key)
        model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        history_key = (role, level)
        recent = RECENT_QUESTIONS.get(history_key, [])[-25:]
        prompt = f'''You are an experienced technical interviewer creating a realistic practice interview.
Role: {role}
Difficulty: {level}
Required number of questions: exactly {count}

Create a fresh, varied set of technically accurate interview questions relevant to this role.
Difficulty rules:
- Beginner: fundamentals, definitions, simple examples.
- Medium: practical application, debugging, comparisons, and moderate problem solving.
- Advanced: system/design trade-offs, edge cases, optimization, evaluation, and real-world scenarios.
Avoid repeating or merely rewording these recent questions: {json.dumps(recent, ensure_ascii=False)}
Make every question distinct within this set. Do not include answers, numbering, markdown, or explanations.
Return valid JSON only in this exact shape: {{"questions": ["question 1", "question 2"]}}'''
        response = client.models.generate_content(model=model, contents=prompt)
        raw = (response.text or '').strip()
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[-1]
            if raw.endswith('```'):
                raw = raw[:-3].strip()
        data = json.loads(raw)
        questions = data.get('questions') if isinstance(data, dict) else None
        if not isinstance(questions, list):
            raise ValueError('Gemini returned an unexpected question format. Please try again.')
        clean = []
        for q in questions:
            if isinstance(q, str):
                q = ' '.join(q.split()).strip()
                if q and q not in clean:
                    clean.append(q)
        if len(clean) < count:
            raise ValueError(f'Gemini returned only {len(clean)} unique questions; please try again.')
        clean = clean[:count]
        RECENT_QUESTIONS[history_key] = (recent + clean)[-25:]
        return clean, None
    except Exception as exc:
        return None, f'Could not generate fresh questions with Gemini: {exc}. Please try again in a moment and check GEMINI_MODEL in your .env file.'

def evaluate_with_gemini(role, level, question, answer):
    key = os.getenv('GEMINI_API_KEY')
    if not key: return None, 'Gemini API key is not configured. Add it to your .env file, then restart the app.'
    try:
        from google import genai
        client = genai.Client(api_key=key)
        model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        prompt = f'''You are a constructive technical interview coach. Evaluate for practice, not hiring. Role: {role}. Difficulty: {level}. Question: {question}. Candidate answer: {answer}. Return valid JSON only with score (integer 0-100), summary (string), strengths (array of strings), improvements (array of strings), sample_answer (string), topics_to_review (array of strings). Be fair, accurate, supportive, and concise. Match expectations to the selected difficulty level.'''
        text = (client.models.generate_content(model=model, contents=prompt).text or '').strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[-1]
            if text.endswith('```'): text = text[:-3].strip()
        data = json.loads(text)
        data['score'] = max(0, min(100, int(data.get('score', 0))))
        return data, None
    except Exception as exc: return None, f'Gemini evaluation failed: {exc}'

@app.route('/')
def home(): return render_template('index.html', roles=QUESTION_BANK, levels=LEVELS, question_counts=QUESTION_COUNTS)
@app.route('/health')
def health(): return jsonify(status='ok', app='InterviewIQ')
@app.route('/api/start', methods=['POST'])
def start():
    d = request.get_json(silent=True) or {}; role, level = d.get('role'), d.get('level')
    try: count = int(d.get('count', 5))
    except (TypeError, ValueError): count = 5
    if role not in QUESTION_BANK or level not in LEVELS or count not in QUESTION_COUNTS: return jsonify(error='Choose a valid role, difficulty, and question count.'), 400
    questions, err = generate_questions_with_gemini(role, level, count)
    if err:
        return jsonify(error=err), 503
    session['interview'] = {'role': role, 'level': level, 'questions': questions, 'results': []}
    return jsonify(role=role, level=level, total=len(questions), index=0, question=questions[0])
@app.route('/api/question', methods=['POST'])
def question():
    d = request.get_json(silent=True) or {}; it = session.get('interview')
    if not it: return jsonify(error='Start an interview first.'), 400
    try: i = int(d.get('index', -1))
    except (TypeError, ValueError): return jsonify(error='Invalid question number.'), 400
    if i < 0 or i >= len(it['questions']): return jsonify(error='Question not found.'), 400
    return jsonify(index=i, question=it['questions'][i], total=len(it['questions']))
@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    d = request.get_json(silent=True) or {}; it = session.get('interview')
    if not it: return jsonify(error='Start an interview first.'), 400
    role, level, q = d.get('role'), d.get('level'), d.get('question'); a = (d.get('answer') or '').strip()
    if role != it['role'] or level != it['level'] or q not in it['questions']: return jsonify(error='Invalid interview details.'), 400
    if len(a) < 10: return jsonify(error='Please write at least 10 characters for useful feedback.'), 400
    if len(a) > 8000: return jsonify(error='Please keep your answer under 8,000 characters.'), 400
    result, err = evaluate_with_gemini(role, level, q, a)
    if err: return jsonify(error=err), 503
    it.setdefault('results', []).append({'question': q, 'answer': a, **result}); session['interview'] = it; session.modified = True
    return jsonify(result)
@app.route('/api/finish', methods=['POST'])
def finish():
    it = session.get('interview')
    if not it: return jsonify(error='No active interview. Start one first.'), 400
    results = it.get('results', []); avg = round(sum(x['score'] for x in results)/len(results)) if results else 0
    return jsonify(role=it['role'], level=it['level'], answered=len(results), total=len(it['questions']), average=avg, results=results)
if __name__ == '__main__': app.run(debug=False)
