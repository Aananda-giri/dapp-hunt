from sanic import Sanic, response
from sanic.response import json, html, file
from sanic_jinja2 import SanicJinja2
import aiohttp
import asyncio
from datetime import datetime
from fpdf import FPDF
import os
from typing import Dict, List

from bs4 import BeautifulSoup

# Example usage
import asyncio



# Initialize Sanic app
app = Sanic("DocumentQA")
jinja = SanicJinja2(app)


from document_qa import DocumentQA

from mongo import Mongo
mongo = Mongo()

from dotenv import load_dotenv
import os
load_dotenv()
ATOMA_BEARER = os.environ.get("ATOMA_BEARER")
assert ATOMA_BEARER != None, "atoma api key is none"

# Initialize our DocumentQA system
qa_system = DocumentQA(
    api_token=ATOMA_BEARER,
    mongo=mongo,
    chunk_size=1000,
    overlap=100
)


# url = "https://example.com"
# asyncio.run(crawl_text_content(url))

def is_youtube_url(url:str) -> bool:
    return url.startswith('https://www.youtube.com') or url.startswith('https://www.m.youtube.com') or url.startswith('https://youtu.be') or url.startswith('https://m.youtube.com') or url.startswith('https://youtube.com')

async def crawl_text_content(url: str) -> str:
    """Async function to crawl text content from URL"""
    if is_youtube_url(url):
        return ''

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text()
            # Parse the HTML content with BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")
            # Extract and return the text content
            return soup.get_text(strip=True)
# async def crawl_text_content(url: str) -> str:
#     """Async function to crawl text content from URL"""
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url) as response:
#             return await response.text()

def generate_pdf(source: str, qa_results: Dict[str, str]) -> str:
    """Generate PDF from QA results"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, f"Summary Report: {source}", ln=True, align='C')
    pdf.ln(10)
    
    # Add content
    pdf.set_font("Arial", size=12)
    for question, answer in qa_results.items():
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(0, 10, question)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, answer)
        pdf.ln(5)
    
    # Save PDF
    filename = f"summaries/{source.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    os.makedirs('summaries', exist_ok=True)
    pdf.output(filename)
    return filename

@app.route("/")
@jinja.template("home.html")
async def home(request):
    """Home page listing all sources"""
    # sources = mongo.summary_collection.distinct("source")
    sources = list(mongo.summary_collection.aggregate([
            {"$group": {"_id": "$source", "tagline": {"$first": "$tagline"}}},
            {"$project": {"_id": 0, "source": "$_id", "tagline": 1}}
        ]))
    return {"sources": sources}

@app.route("/add_source", methods=["GET", "POST"])
@jinja.template("add_source.html")
async def add_source(request):
    if request.method == "GET":
        return {}
    
    # Handle POST request
    data = request.json
    source = data.get("source")
    urls = data.get("urls", [])
    print(f'source: {source}, urls:{urls}')
    
    if mongo.exists(source):
        print(f'source: {source} already exists. updating documents')
        return json({"status": "success", "redirect_url":f"/source/{source}"})

    # Crawl URLs and save documents
    documents = []
    for url in urls:
        text_content = await crawl_text_content(url)
        documents.append({
            "source": source,
            "url": url,
            "text_content": text_content
        })
    
    # print(f"documents:{documents}")
    
    # Save documents
    qa_system.save_documents(documents)
    
    questions = {}
    for key, value in qa_system.questions.items():
        questions[key] = value.format(source=source)

    # print(questions)

    # Generate summaries for each question
    print(f'completed crawling. started to generate summaries')
    summaries = {}
    for q_key, q_template in questions.items():
        print(f"{q_key}", end='')
        question = q_template.format(source=source)
        answer = qa_system.query_documents(
            query=question,
            source=source,
            n_docs=15,
            bullet_points=True,
            feed_message_history=False,
            use_r1=True   # Use deepseek-r1 model
        )
        summaries[q_key] = answer
        print(f': done!')

        tagline_prompt = "please provide a short, one sentence tagline strictly based on following information: "
        for key, value in summaries.items():
            tagline_prompt += f'\n\n ## {key}: \n{value}'
        tagline = qa_system.query_llm(tagline_prompt)
    # print(f'summaries: {summaries}')
    # Save summary to MongoDB
    summary_doc = {
        "source": source,
        "summaries": summaries,
        "tagline":tagline,
        "created_at": datetime.now()
    }
    mongo.summary_collection.insert_one(summary_doc)
    
    # Generate PDF
    pdf_path = generate_pdf(source, summaries)
    
    # /source/{source}
    print(f'redirecting to \"/source/{source}\"')
    return json({"status": "success", "redirect_url":f"/source/{source}"})


@app.route("/source/<source>")
@jinja.template("source.html")
async def source_page(request, source):
    """Individual source page"""
    summary = mongo.summary_collection.find_one({"source": source})
    chat_history = mongo.brainstrom_collection.find({'source':source})
    
    # Iterate through the cursor to get each document
    messages = []
    for message in chat_history:
        messages.extend(message['messages'])
    
    return {
        "source": source,
        "summary": summary["summaries"] if summary else {},
        "chat_history": messages,
        "pdf_path": f"/download/{source}/summary.pdf"
    }

@app.route("/regenerate_summary", methods=["GET", "POST"])
async def regenerate_summary(request):
    if request.method == "GET":
        return {}
    
    # Handle POST request
    data = request.json
    source = data.get("source")

    print(f'regenerating summary. source:{source}')

    questions = {}
    for key, value in qa_system.questions.items():
        questions[key] = value.format(source=source)

    # print(questions)

    # Generate summaries for each question
    summaries = {}
    for q_key, q_template in questions.items():
        print(f"{q_key}", end='')
        question = q_template.format(source=source)
        answer = qa_system.query_documents(
            query=question,
            source=source,
            n_docs=15,
            bullet_points=True,
            feed_message_history=True
        )
        summaries[q_key] = answer
        print(f': done!')
    
    # print(f'summaries: {summaries}')
    # replace this code with mongo functin: update_summary
    # Save summary to MongoDB
    summary_doc = {
        "source": source,
        "summaries": summaries,
        "created_at": datetime.now()
    }
    
    # update if exists, create new otherwise
    query = {"source": summary_doc["source"]}
    
    # Define the update operation
    update = {
        "$set": {
            "summaries": summary_doc["summaries"],
            "created_at": summary_doc["created_at"]
        }
    }

    # Use update_one with upsert=True
    mongo.summary_collection.update_one(query, update, upsert=True)
    
    # Generate PDF
    pdf_path = generate_pdf(source, summaries)
    
    # /source/{source}
    print(f'redirecting to \"/source/{source}\"')
    return json({"status": "success", "redirect_url":f"/source/{source}"})

@app.route("/update_lean_canvas/<source>", methods=["POST"])
async def update_lean_canvas(request, source):
    """Chat endpoint"""
    # // todo: sanic app listening to this api call.
    # const selectedModel = document.getElementById('model_selector').value;
    data = request.json
    print(f'data:{data}')
    
    model_name = data.get("model")
    print(f"Update lean canvas. source:{source}, model: {model_name}")
    
    # regenerate summary
    qa_system.regenerate_lean_canvas_v2(model_name, source)

    return json({})

@app.route("/chat/<source>", methods=["POST"])
async def chat(request, source):
    """Chat endpoint"""
    data = request.json
    # print(f'data:{data}')
    query = data.get("query")
    model = data.get("model")
    print(f'data:{data} \n model: {model} \nsource:{source}')

    if model and model.startswith('brainstrom'):
        # brainstrom with model
        # ---------------------
        use_r1=False
        if model.endswith('-r1'):
            use_r1=True
        
        summary = mongo.summary_collection.find_one({"source": source})
        summary = summary["summaries"] if summary else {}

        response = qa_system.query_documents(
            query=query,
            source=source,
            n_docs=100,
            feed_message_history=True,
            summary=summary,
            brainstrom=True,    # Added for brainstroming (False by default)
            use_r1=use_r1   # whether or not use r1 model
        )
        
        # update lean canvas checkbox
        show_update_checkbox = qa_system.should_we_show_update_lean_canvas_checkbox(response)
        # print(f'response: {response}')
        mongo.append_brainstrom_message(source, query, response)
    else:
        # chat model
        # -----------

        use_r1=False
        if model and model.endswith('-r1'):
            use_r1=True
        response = qa_system.query_documents(
            query=query,
            source=source,
            n_docs=100,
            feed_message_history=True,
            use_r1=use_r1
        )
        # print(f'response: {response}')
        show_update_checkbox = qa_system.should_we_show_update_lean_canvas_checkbox(response)
        mongo.append_message(source, query, response)
    
    print(f' query: {query}\n response: {response}')
    return json({"response": response, "show_update_checkbox": show_update_checkbox})

@app.route("/model_change", methods=["GET", "POST"])
async def model_change(request):
    # Parse JSON data from the request
    data = request.json
    if not data:
        return json({"status": "error", "message": "No data provided"}, status=400)
    try:

        # Extract new model name and source from the payload
        model_name = data.get("model")
        source = data.get("source")
        print(f' model change \n model_name: {model_name}\n source:{source} ')

        if model_name.startswith('chat'):
            print('chat model')
            # chat messeges
            chat_history = mongo.messages_collection.find({'source':source})
        
            # Iterate through the cursor to get each document
            messages = []
            for message in chat_history:
                messages.extend(message['messages'])
            # to solve error: datetime.datetime(2025, 1, 28, 16, 10, 58, 583000) is not JSON serializable
            messages_new = []
            for message in messages:
                message['timestamp'] = str(message['timestamp'])
                messages_new.append({
                    'query':message['query'],
                    'response':message['response']
                })
            messages = messages_new
        else:
            print('brainstrom model')
            # brainstrom messages
            chat_history = mongo.brainstrom_collection.find({'source':source})
        
            # Iterate through the cursor to get each document
            messages = []
            for message in chat_history:
                print(f' \n\n message: {messages}')
                messages.extend(message['messages'])

            
            # to solve error: datetime.datetime(2025, 1, 28, 16, 10, 58, 583000) is not JSON serializable
            messages_new = []
            for message in messages:
                message['timestamp'] = str(message['timestamp'])
                messages_new.append({
                    'query':message['query'],
                    'response':message['response']
                })
            messages = messages_new
        if not model_name or not source:
            print(f'\n\n error1')
            return json({"status": "error", "message": "Missing model or source"}, status=400)
        print(f'messages:{messages}')
        # Return the result as JSON.
        print(f'\n\n normal return')
        return json({"status": "success", "messages": messages}, status=200)
    except Exception as ex:
        print(f'error2: {ex}')
        return json({"status": f"error: {ex}", "message": "No data provided"}, status=400)
    
@app.route("/download/<source>/summary.pdf")
async def download_pdf(request, source):
    """Download PDF endpoint"""
    # Find the latest PDF for this source
    pdf_files = [f for f in os.listdir('summaries') if f.startswith(source.replace('/', '_'))]
    if not pdf_files:
        return response.text("PDF not found", status=404)
    
    latest_pdf = sorted(pdf_files)[-1]
    return await file(f'summaries/{latest_pdf}')

@app.post("/update_summary")
async def update_text(request):
    data = request.json
    title = data.get("title")
    text = data.get("text")
    source = data.get("source")
    print(f'title: {title} \n text: {text[:100]} \nsource:{source}')
    
    mongo.update_summary(source, title, text)
    
    return response.json({"status": "success"})

if __name__ == "__main__":
    os.makedirs('summaries', exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)