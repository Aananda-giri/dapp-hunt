from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import json
import os
from src.framework_generator import framer, split_n_generate
from src.generate import generate_output
import pickle
from dotenv import load_dotenv
# Load in OpenAI API Key from .env
load_dotenv()



app = Flask(__name__)

# Ensure the required directories exist
os.makedirs("./framework_output", exist_ok=True)

@app.route('/')
def homepage():
    """Render the homepage with the 'Get Started' button."""
    return render_template('homepage.html')

@app.route('/get-started', methods=['GET', 'POST'])
def get_started():
    """Handle the information gathering page."""
    if request.method == 'POST':
        # Get form data
        product_name = request.form.get('product_name')
        news_urls = [url.strip() for url in request.form.getlist('news_urls') if url.strip()]
        youtube_urls = [url.strip() for url in request.form.getlist('youtube_urls') if url.strip()]
        
        # Save configuration to config.json
        config = {
            "product": product_name,
            "openai_model": "gpt-3.5-turbo",
            "news_urls": news_urls,
            "youtube_urls": youtube_urls,
            "prompt_template": "You are a research chatbot having a conversation with a human.\n\nGiven the following information about {product}, give a professional and detailed answer to the final question.\n\n{context}\n\n{chat_history}\nHuman: {human_input}\nChatbot:",
            "framework_questions": {
                "overall": "What is {product}? Give a description of what it does and why it exists.",
                "target_users": "Who is {product} intended for? These groups of people are called target users.",
                "problems": "What are the reasons for target users to seek out, and adopt, {product}?",
                "solutions": "How does {product} address each one of these reasons?",
                "unfair_advantage": "What makes {product} difficult to compete with?",
                "unique_value_proposition": "What makes {product} unique or special compared to others?",
                "channels": "Which channels does {product} use to reach its target users?",
                "costs": "What operating costs are incurred by {product}?",
                "revenue": "How does {product} generate revenue?"
            }
        }

        
        
        print(f'saving config')
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print('redirecting to processing')
        return redirect(url_for('processing'))
    
    return render_template('get_started.html')

@app.route('/processing')
def processing():
    """Show processing animation while crawling data."""
    print(f'rendering processing.html')
    return render_template('processing.html')

@app.route('/crawl-data')
def crawl_data():
    """Background task to crawl data from sources."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        news_urls = config["news_urls"]
        youtube_urls = config["youtube_urls"]
    
        framer(news_urls, youtube_urls)

        # Call the framer function to crawl data
        crawled_docs = framer(config['news_urls'], config['youtube_urls'])
        
        # Store crawled data in session or temporary file
        # For simplicity, we'll store it in a file
        with open('crawled_data.json', 'w') as f:
            json.dump([{
                'content': doc.page_content,
                'source': doc.metadata['source']
            } for doc in crawled_docs], f)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/verify')
def verify():
    """Show crawled data for verification."""
    try:
        with open('crawled_data.json', 'r') as f:
            crawled_data = json.load(f)
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        return render_template('verify.html', 
                             product_name=config['product'],
                             crawled_data=crawled_data)
    except FileNotFoundError:
        return redirect(url_for('get_started'))

@app.route('/generating')
def generating():
    """Show generation animation while creating the lean canvas."""
    return render_template('generating.html')




@app.route('/generate-output')
def generate_lean_canvas():
    """Background task to generate the lean canvas."""
    try:
        # with open('crawled_data.json', 'r') as f:
        #     crawled_data = json.load(f)
        
        # # Convert back to Document objects
        # docs = [Document(page_content=d['content'], 
        #                 metadata={'source': d['source']}) 
        #        for d in crawled_data]
        
        # Load in config variables from config.json
        with open('./config.json') as config_file:
            config = json.load(config_file)
        product = config["product"]
        openai_model = config["openai_model"]

        prompt_template = config["prompt_template"]

        framework_questions = config["framework_questions"]
        framework_questions_formatted = {key: value.format(product=product) for key, value in framework_questions.items()}

        results = split_n_generate(product, framework_questions_formatted, openai_model, prompt_template)
        
        with open('results.pickle','wb') as f:
            pickle.dump(results, f)

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/results')
def results():
    """Show the final results page."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        # with open('crawled_data.json', 'r') as f:
        #     crawled_data = json.load(f)
        with open('results.pickle','rb') as f:
            crawled_data = pickle.load(f)
            
        filename = f"./framework_output/{config['product']}_framework.csv"
        
        return render_template('results.html',
                             product_name=config['product'],
                             results=crawled_data,
                             download_filename=filename)
    except FileNotFoundError:
        return redirect(url_for('get_started'))

@app.route('/download/<path:filename>')
def download(filename):
    """Handle file downloads."""
    try:
        print(f'\n\n fucking download: {filename}')
        return send_file(filename.replace('/download/',''), as_attachment=True)
    except FileNotFoundError:
        return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)
