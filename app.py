import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
from fpdf import FPDF
import hashlib
import json
import os
import sanic
from sanic import Sanic
from sanic.response import file
from sanic_jinja2 import SanicJinja2

import time
from typing import Dict, List

import json as json_lib
from sanic.response import redirect, text

import urllib.parse
from urllib.parse import urlparse, urlencode

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

from youtube_functions import get_subtitle, is_youtube_url

# =================================================================
#      ==================== Google-Login =====================
# =================================================================

# Load Google OAuth credentials
# In production, you'd load this from a secure location
# For this example, we'll define it directly (replace with your actual credentials)
GOOGLE_CLIENT_CONFIG = {
    'client_id': os.environ.get('client_id'),
    'project_id': os.environ.get('project_id'),
    'auth_uri': os.environ.get('auth_uri'),
    'token_uri': os.environ.get('token_uri'),
    'auth_provider_x509_cert_url': os.environ.get('auth_provider_x509_cert_url'),
    'client_secret': os.environ.get('client_secret'),
    'redirect_uris': [os.environ.get('redirect_uris')],
    'javascript_origins': [os.environ.get('javascript_origins')],
}

# OAuth settings
SCOPES = ['openid', 'email', 'profile']
REDIRECT_URI = 'http://localhost:5000/callback'

# Session settings
SESSION_COOKIE_NAME = "session_id"
SESSION_EXPIRY = 3600  # Session expires after 1 hour
DB_NAME = "oauth_app"

# Initialize MongoDB connection
@app.listener('before_server_start')
async def setup_mongo(app, loop):
    # app.ctx.mongo_client = mongo
    app.ctx.mongo = mongo

@app.listener('after_server_stop')
async def close_mongo(app, loop):
    # app.ctx.mongo_client.close()
    pass

# Helper functions for session management
def generate_session_id(user_info):
    """Generate a unique session ID based on user info and timestamp"""
    session_data = str(user_info) + str(time.time())
    return hashlib.sha256(session_data.encode()).hexdigest()

async def create_session(request, user_info):
    """Create a new session for a user in MongoDB"""
    session_id = generate_session_id(user_info)
    expires = time.time() + SESSION_EXPIRY
    
    # Store session in MongoDB
    request.app.ctx.mongo.session_collection.insert_one({
        "session_id": session_id,
        "user_info": user_info,
        "expires": expires,
        # Store expires as a timestamp that MongoDB can use for TTL index
        "expires_at": {"$date": int(expires * 1000)}
    })
    
    return session_id

async def get_session(request, session_id):
    """Get and validate a session from MongoDB"""
    if not session_id:
        return None
    
    # Find session in MongoDB
    session = request.app.ctx.mongo.session_collection.find_one({
        "session_id": session_id
    })
    
    if not session:
        return None
        
    # Check if session has expired
    if session["expires"] < time.time():
        await delete_session(request, session_id)
        return None
        
    return session

async def delete_session(request, session_id):
    """Delete a session from MongoDB"""
    request.app.ctx.mongo.session_collection.delete_one({
        "session_id": session_id
    })

# Middleware to check for authenticated sessions
@app.middleware('request')
async def check_session(request):
    # require authentication for /canvas, /data, /questions
    if request.path in ['/dashboard','/canvas', '/data', '/questions']:
        # return
        # Check for session cookie
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        session = await get_session(request, session_id)
        
        if not session:
            return redirect('/login')

@app.route('/login')
async def login(request):
    """Redirect to Google's OAuth 2.0 authorization page"""
    auth_params = {
        'client_id': GOOGLE_CLIENT_CONFIG['client_id'],
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',
        'include_granted_scopes': 'true'
    }
    
    auth_url = f"{GOOGLE_CLIENT_CONFIG['auth_uri']}?{urlencode(auth_params)}"
    return redirect(auth_url)


@app.route('/callback')
async def callback(request):
    """Handle the OAuth callback from Google"""
    # Get authorization code from the callback
    code = request.args.get('code')
    if not code:
        return text("Authorization code not received", status=400)
    
    # Exchange authorization code for tokens
    token_data = {
        'code': code,
        'client_id': GOOGLE_CLIENT_CONFIG['client_id'],
        'client_secret': GOOGLE_CLIENT_CONFIG['client_secret'],
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(GOOGLE_CLIENT_CONFIG['token_uri'], data=token_data) as resp:
            if resp.status != 200:
                error_msg = await resp.text()
                return text(f"Token exchange failed: {error_msg}", status=400)
            
            token_response = await resp.json()
            access_token = token_response.get('access_token')
            id_token = token_response.get('id_token')
            
    # Use the access token to get user info
    async with aiohttp.ClientSession() as session:
        async with session.get('https://www.googleapis.com/oauth2/v1/userinfo', 
                               headers={'Authorization': f'Bearer {access_token}'}) as resp:
            if resp.status != 200:
                error_msg = await resp.text()
                return text(f"Failed to get user info: {error_msg}", status=400)
            
            user_info = await resp.json()
    
    # Create a session for the user in MongoDB
    session_id = await create_session(request, user_info)
    
    # Redirect to dashboard with the session cookie
    response = redirect('/dashboard')
    response.add_cookie(
        SESSION_COOKIE_NAME,
        session_id,
        httponly=True,
        max_age=SESSION_EXPIRY
    )
    
    return response

@app.route('/session-info')
async def session_info(request):
    """Display session information from MongoDB"""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    session = await get_session(request, session_id)
    
    if not session:
        return redirect('/login')
    
    # Get all active sessions for demo purposes (in production, you might want to limit this)
    active_sessions = request.app.ctx.mongo.session_collection.find({}).to_list(length=10)
    
    # Format session data for display
    formatted_sessions = []
    for sess in active_sessions:
        # Convert ObjectId to string for JSON serialization
        sess['_id'] = str(sess['_id'])
        # Format expires timestamp to readable date
        if 'expires' in sess:
            sess['expires_human'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(sess['expires']))
        formatted_sessions.append(sess)
    
    return sanic.response.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Session Information</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            .session-data {{ background-color: #f5f5f5; padding: 20px; border-radius: 4px; overflow: auto; }}
            .current-session {{ border-left: 4px solid #4CAF50; }}
            .buttons {{ margin-top: 20px; }}
            .btn {{
                display: inline-block;
                background-color: #4285F4;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 4px;
                margin-right: 10px;
                transition: background-color 0.3s;
            }}
            .btn:hover {{ background-color: #3367D6; }}
            .logout-btn {{ background-color: #f44336; }}
            .logout-btn:hover {{ background-color: #d32f2f; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Session Information</h1>
            
            <h2>Your Current Session</h2>
            <p>Session ID: <strong>{session_id}</strong></p>
            <div class="session-data current-session">
                <pre>{json_lib.dumps(session, indent=2, default=str)}</pre>
            </div>
            
            <h2>All Active Sessions in MongoDB ({len(formatted_sessions)})</h2>
            <p>This is for demonstration purposes. In a production app, you would not display all sessions.</p>
            <div class="session-data">
                <pre>{json_lib.dumps(formatted_sessions, indent=2)}</pre>
            </div>
            
            <div class="buttons">
                <a href="/dashboard" class="btn">Back to Dashboard</a>
                <a href="/" class="btn">Home</a>
                <a href="/logout" class="btn logout-btn">Logout</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.route('/logout')
async def logout(request):
    """Log the user out and redirect to the homepage"""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    
    # Delete the session from MongoDB if it exists
    if session_id:
        await delete_session(request, session_id)
    
    # Clear the session cookie
    response = redirect('/')
    response.delete_cookie(SESSION_COOKIE_NAME)
    
    return response

# =================================================================


# Initialize our DocumentQA system
qa_system = DocumentQA(
    api_token=ATOMA_BEARER,
    mongo=mongo,
    chunk_size=1000,
    overlap=100
)


# url = "https://example.com"
# asyncio.run(crawl_text_content(url))

async def crawl_text_content(url: str) -> str:
    """Async function to crawl text content from URL"""
    print(f' crawling url: {url}')
    if is_youtube_url(url):
        return get_subtitle(url)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text()
            # Parse the HTML content with BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")
            # Extract and return the text content
            # print(f"crawled:: {soup.get_text(strip=True)[:100]}")
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

def get_lean_canvas_questions(user_id):
    # get_lean_canvas_questions
    questions = mongo.canvas_question_collection.find_one({'user_id':user_id}, projection={'_id': False, 'user_id':False})
    
    if not questions:
        print(f'getting questions from template')
        questions = {}
        
        # Get questions templates
        for key, value in qa_system.questions.items():
            # Save to mongo for next time
            mongo.add_canvas_question_field(user_id=user_id, field=key, value=value)
            
            questions[key] = value.format(source='\<this-product\>')
            
    return questions

# @app.route("/")
# @jinja.template("home.html")
# async def home(request):
#     """Home page listing all sources"""
#     # sources = mongo.summary_collection.distinct("source")
#     sources = list(mongo.summary_collection.aggregate([
#             {"$group": {"_id": "$source", "tagline": {"$first": "$tagline"}}},
#             {"$project": {"_id": 0, "source": "$_id", "tagline": 1}}
#         ]))
#     return {"sources": sources}

@app.route("/dashboard")
@jinja.template("dashboard.html")
async def dashboard(request):
    """Home page listing all sources"""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    session = await get_session(request, session_id)

    if not session:
        return redirect('/login')
    
    user_info = session['user_info']
    print(f'\n\n user_info: {user_info} \n\n')

    sources = mongo.get_users_with_specific_ids([0, user_info['id']])
    
    # Get questions
    source = "`your_product`"
    questions = get_lean_canvas_questions(user_id=user_info['id'])
    
    print(f'questions: {questions}')

    download_files = [filename.split('_')[0] for filename in os.listdir('summaries')]
    
    return {"sources": sources, "questions":questions, "download_files":download_files, "user_info":user_info}

@app.route("/")
@jinja.template("landing.html")
async def landing(request):
    """Home page listing all sources"""
    # sources = mongo.summary_collection.distinct("source")
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    session = await get_session(request, session_id)

    if session:
        user_info = session['user_info']
    else:
        user_info=None
       
    print(f"\n\nuser_info:{user_info}\n\n")
    sources = list(mongo.summary_collection.aggregate([
            {"$group": {"_id": "$source", "tagline": {"$first": "$tagline"}}},
            {"$project": {"_id": 0, "source": "$_id", "tagline": 1}}
        ]))
    return {"sources": sources, "user_info":user_info}

@app.route("/add_source", methods=["GET", "POST"])
@jinja.template("add_source.html")
async def add_source(request):
    '''
    * Previous version: User used to give list of sources
    '''

    if request.method == "GET":
        continue_without_source = request.args.get("continue_without_source", "false")  # Default to "no" if not provided
        display_source_form = continue_without_source.lower() == 'false' # display source if not continue_without_source

        print(f"display_source_form: {display_source_form}")

        return {"display_source_form": display_source_form}  # Pass it to the template

    # Handle POST request
    data = request.json
    source = data.get("source")
    urls = data.get("urls", [])
    print(f'source: {source}, urls:{urls}')
    
    if mongo.exists(source):
        print(f'source: {source} already exists. updating documents')
        return sanic.response.json({"status": "success", "redirect_url":f"/source/{source}"})

    summaries = {}
    tagline = ''
    if urls:
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
        
        questions = get_questions(source)

        # print(questions)

        # Generate summaries for each question
        print(f'completed crawling. started to generate summaries')
        for q_key, q_template in questions.items():
            print(f"{q_key}", end='')
            question = q_template.format(source=source)
            answer = qa_system.query_documents(
                query=question,
                source=source,
                n_docs=15,
                bullet_points=True,
                feed_message_history=False,
                full_text_search=True
            )
            summaries[q_key] = answer
            print(f': done!')

            tagline_prompt = "please provide a short, one sentence tagline strictly based on following information: "
            for key, value in summaries.items():
                tagline_prompt += f'\n\n ## {key}: \n{value}'
            tagline = qa_system.query_llm(tagline_prompt)
        
        # Generate PDF
        pdf_path = generate_pdf(source, summaries)
    else:
        # continue without sourc
        questions = get_questions(source)
        # print(questions)

        # Dummy summary data
        for q_key, q_template in questions.items():
            summaries[q_key] = "• Not enough information."
        
        

    # print(f'summaries: {summaries}')
    # Save summary to MongoDB
    summary_doc = {
        "source": source,
        "summaries": summaries,
        "tagline":tagline,
        "created_at": datetime.now()
    }
    mongo.summary_collection.insert_one(summary_doc)
        
    # /source/{source}
    print(f'redirecting to \"/source/{source}\"')
    return sanic.response.json({"status": "success", "redirect_url":f"/source/{source}"})


@app.route("/add_source_new", methods=["POST"])
async def add_source_new(request):
    # Handle POST request
    print('\n\nadding new source')
    data = request.json
    source = urllib.parse.unquote(data.get("projectName"))
    purpose = urllib.parse.unquote(data.get("projectPurpose"))
    user_id = data.get("user_id")
    print(f'\n\ngot user_id: {type(user_id)} {user_id}\n\n')
    user_id = urllib.parse.unquote(user_id)

    # To make source unique among different users
    source = source+"_source_"+user_id

    print(f'\n\n source: {source}, purpose:{purpose}, user_id:{user_id}')
    try:
        summaries = {}
        # questions = get_questions(source)
        # print(questions)

        # Dummy summary data
        summaries = get_lean_canvas_questions(user_id)
        
        # print(f'summaries: {summaries}')
        # Save summary to MongoDB
        summary_doc = {
            "source": source,
            "user_id": user_id,
            "summaries": summaries,
            "tagline":'',
            "purpose":purpose,  # purpose is either "brainstorm" or "due_diligence"
            "created_at": datetime.now()
        }
        mongo.summary_collection.insert_one(summary_doc)
        return sanic.response.json({"success":True})
    except Exception as ex:
        print(ex)
        return sanic.response.json({"success":False})

@app.route("/add_canvas_question_field", methods=["POST"])
async def add_canvas_question_field(request):
    # Handle POST request
    print('\n\nadding canvas question field')
    data = request.json
    user_id = urllib.parse.unquote(data.get("user_id"))
    field = urllib.parse.unquote(data.get("field"))
    value = urllib.parse.unquote(data.get("value"))
    
    print(f'\n\n user_id: {user_id}, field:{field}, value: {value}')
    try:
        mongo.add_canvas_question_field(user_id=user_id, field=field, value=value)
        return sanic.response.json({"success":True})
    except Exception as ex:
        print(ex)
        return sanic.response.json({"success":False})

@app.route("/delete_canvas_question_field", methods=["POST"])
async def delete_canvas_question_field(request):
    """
    Delete canvas question field
    """
        # Handle POST request
    print('\n\ndeleting canvas question field')
    data = request.json
    user_id = urllib.parse.unquote(data.get("user_id"))
    field = urllib.parse.unquote(data.get("field"))
    
    print(f'\n\n delete canvas question:  user_id: \"{user_id}\", field:\"{field}\"')
    try:
        deleted = mongo.delete_canvas_question_field(user_id=user_id, field=field)
        if deleted:
            return sanic.response.json({"success":True})
        else:
            return sanic.response.json({"success":False})
    except Exception as ex:
        print(ex)
        return sanic.response.json({"success":False})

@app.route("/source/<source>")
@jinja.template("source.html")
async def source_page(request, source):
    """Individual source page"""
    summary = mongo.summary_collection.find_one({"source": source})
    chat_history = mongo.brainstorm_collection.find({'source':source})
    
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
# Experimenting this function
@app.route("/canvas/<source>")
@jinja.template("canvas.html")
async def canvas(request, source):
    """Individual source page"""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    session = await get_session(request, session_id)

    if not session:
        return redirect('/login')

    user_info = session['user_info']
    print(f"\n\nuser_info: {user_info}\n\n")

    # summary = mongo.summary_collection.find_one({"source": source})
    pipeline = [
        {
            "$match": {"source": source}  # Your initial filter
        },
        {
            "$group": {
                "_id": "$url",  # Group by the 'url' field
                "source": {"$first": "$source"},  # Get the first 'source' for each unique URL
                # Include other fields if needed, using $first, $last, $max, etc.
                # Example: "other_field": {"$first": "$other_field"}
            }
        }
    ]

    summary = mongo.summary_collection.find_one({'source':source})
    if not summary or source=="your-project-name":
        summaries = {}
        questions = get_lean_canvas_questions(user_id=user_info['id'])
        # print(questions)

        # Dummy summary data
        for q_key, q_template in questions.items():
            summaries[q_key] = "• Not enough information."
        
        

        # print(f'summaries: {summaries}')
        # Save summary to MongoDB
        summary = {
            "source": source,
            "summaries": summaries,
            "tagline":'',
            "purpose":'brainstorm',  # purpose is either "brainstorm" or "due_diligence"
            "created_at": datetime.now()
        }
        # Create new questions here.
    
    if summary and 'purpose' in summary.keys():
        purpose = summary['purpose']
    else:
        purpose = 'brainstorm'

    data_sources = list(mongo.collection.aggregate(pipeline))
    chat_history = mongo.brainstorm_collection.find({'source':source})
    
    # Iterate through the cursor to get each document
    messages = []
    for message in chat_history:
        messages.extend(message['messages'])
    
    # Get questions
    questions = list(mongo.questions_collection.find({"source":source}, {'question':1}))

    print(f'source:{source}message: {messages}')
    
    return {
        "source": source,
        "summary": summary["summaries"] if summary else {},
        "chat_history": messages,
        "pdf_path": f"/download/{source}/summary.pdf",
        "data_sources": data_sources,
        "purpose": purpose,
        "questions": questions,
        "user_info": user_info
    }

@app.route("/regenerate_summary", methods=["GET", "POST"])
async def regenerate_summary(request):
    if request.method == "GET":
        return {}
    
    # Handle POST request
    data = request.json
    source = data.get("source")

    print(f'regenerating summary. source:{source}')

    questions = get_questions(source)

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
            feed_message_history=True,
            full_text_search=True
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
    return sanic.response.json({"status": "success", "redirect_url":f"/source/{source}"})

@app.route("/update_lean_canvas/<source>", methods=["POST"])
async def update_lean_canvas(request, source):
    """Chat endpoint"""
    # // todo: sanic app listening to this api call.
    # const selectedModel = document.getElementById('model_selector').value;
    data = request.json
    print(f'data:{data}')
    
    model_name = data.get("model")
    brainstorm = False
    if model_name and model_name.startswith('brainstorm'):
        # brainstorm prompt model (better responses while chatting)
        # ------------------------
        brainstorm = True

    model_name = model_name.split('chat-')[-1].split('brainstorm-')[-1]   # one of these values : "o1", "r1", "llama3-70B"
    print(f"Update lean canvas. source:{source}, model: {model_name}")
    
    # regenerate summary
    qa_system.regenerate_lean_canvas_v2(model_name, source)

    # tell user you have regenerated the lean canvas
    # ----------------------------------------------
    print('chat!')
    data = request.json
    # print(f'data:{data}')
    query = "<you have updated the lean canvas. please proceed your conversation with user>"
    
    summary = mongo.summary_collection.find_one({"source": source})
    summary = summary["summaries"] if summary else {}

    response = qa_system.query_documents(
        query=query,
        source=source,
        n_docs=100,
        feed_message_history=True,
        summary=summary,
        brainstorm=brainstorm,            # Added for brainstorming (True or False)
        model_name = model_name,    # one of these values : "o1", "r1", "llama3-70B"
        full_text_search=False,
        include_documents=False
        # use_r1=use_r1               # whether or not use r1 model
    )
        
    query="yes" # yes in the sense that user clicked on the checkbox saying update the lean canvas.
    # print(f'response: {response}')
    if brainstorm:
        mongo.append_brainstorm_message(source, query, response)
    else:
        mongo.append_message(source, query, response)
    
    print(f' query: {query}\n response: {response}')
    
    # ----------------------------------------------
    return sanic.response.json({})

# @app.route("/chat/<source>", methods=["POST"])
# async def chat(request, source):
#     """Chat endpoint"""
#     data = request.json
#     # print(f'data:{data}')
#     query = data.get("query")
#     model = data.get("model")
#     print(f'data:{data} \n model: {model} \nsource:{source}')

#     if model and model.startswith('brainstorm'):
#         # brainstorm with model
#         # ---------------------
#         use_r1=False
#         if model.endswith('-r1'):
#             use_r1=True
        
#         summary = mongo.summary_collection.find_one({"source": source})
#         summary = summary["summaries"] if summary else {}

#         response = qa_system.query_documents(
#             query=query,
#             source=source,
#             n_docs=100,
#             feed_message_history=True,
#             summary=summary,
#             brainstorm=True,    # Added for brainstorming (False by default)
#             use_r1=use_r1   # whether or not use r1 model
#         )
        
#         # update lean canvas checkbox
#         show_update_checkbox = qa_system.should_we_show_update_lean_canvas_checkbox(response)
#         # print(f'response: {response}')
#         mongo.append_brainstorm_message(source, query, response)
#     else:
#         # chat model
#         # -----------

#         use_r1=False
#         if model and model.endswith('-r1'):
#             use_r1=True
#         response = qa_system.query_documents(
#             query=query,
#             source=source,
#             n_docs=100,
#             feed_message_history=True,
#             use_r1=use_r1
#         )
#         # print(f'response: {response}')
#         show_update_checkbox = qa_system.should_we_show_update_lean_canvas_checkbox(response)
#         mongo.append_message(source, query, response)
    
#     print(f' query: {query}\n response: {response}')
#     return sanic.response.json({"response": response, "show_update_checkbox": show_update_checkbox})

@app.route("/chat/<source>", methods=["POST"])
async def chat(request, source):
    """Chat endpoint"""
    print('chat!')
    data = request.json
    # print(f'data:{data}')
    query = data.get("query")
    model = data.get("model")
    projectPurpose = data.get("projectPurpose", None)
    
    if projectPurpose:
        if projectPurpose == 'brainstorm':
            model = 'brainstorm-' + model
        else:
            model = "chat-" + model
    
    print(f'data:{data} \n model: {model} \nsource:{source}, projectPurpose: {projectPurpose}')
    brainstorm = False
    if model and model.startswith('brainstorm'):
        # brainstorm prompt model (better responses while chatting)
        # ------------------------
        brainstorm = True
    
    print(f'mode: {model}, brainstorm:{brainstorm} purpose:{projectPurpose}')
    model_name = model.split('chat-')[-1].split('brainstorm-')[-1]   # one of these values : "o1", "r1", "llama3-70B"
    print(f'\n\n model_name: {model_name}')
        
    summary = mongo.summary_collection.find_one({"source": source})
    summary = summary["summaries"] if summary else {}
    
    # Chat Response
    # --------------
    response = qa_system.query_documents(
        query=query,
        source=source,
        n_docs=100,
        feed_message_history=True,
        summary=summary,
        brainstorm=True,            #brainstorm Added for brainstorming (True or False)
        model_name = model_name,    # one of these values : "o1", "r1", "llama3-70B"
        full_text_search=True
        # use_r1=use_r1               # whether or not use r1 model
    )
        
    # update lean canvas checkbox
    # ----------------------------
    show_update_checkbox = qa_system.should_we_show_update_lean_canvas_checkbox(response)
    
    # update questions about the product
    # -----------------------------------
    previous_questions = mongo.questions_collection.find_one({'source':source})
    questions_list = qa_system.query_documents(
        query=query,
        source=source,
        n_docs=100,
        feed_message_history=True,
        summary=summary,
        brainstorm=False,            # Added for brainstorming (True or False)
        model_name = model_name,    # one of these values : "o1", "r1", "llama3-70B"
        full_text_search=True,
        previous_questions=previous_questions,
        generate_questions=True
    )

    # Update if the document with the given source exists, otherwise insert a new one
    # mongo.questions_collection.update_one(
    #     {"source": source},  # Search condition
    #     {"$set": {"questions": questions_list}},  # Update operation
    #     upsert=True  # Insert if not found
    # )
    for question in questions_list:
        mongo.create_question(source=source, question=question, answer='')
    
    with open('questions.txt','w') as f:
        f.write(str(questions_list))
        

    # update mongo with new questions

    
    # show_update_checkbox = qa_system.update_questions(response)

    print('show_update_checkbox: {show_update_checkbox}')
    # print(f'response: {response}')
    
    if brainstorm:
        print(f'saving brainstorm message')
        mongo.append_brainstorm_message(source, query, response)
    else:
        print(f'saving chat messages')
        mongo.append_message(source, query, response)
    
    
    print(f' query: {query}\n response: {response}')
    # print(f'full response: "response": {response}, "show_update_checkbox": {show_update_checkbox}, "questions":{questions_list}')
    return sanic.response.json({"response": response, "show_update_checkbox": show_update_checkbox, "questions":questions_list})

@app.route("/model_change", methods=["GET", "POST"])
async def model_change(request):
    # Parse JSON data from the request
    data = request.json
    if not data:
        return sanic.response.json({"status": "error", "message": "No data provided"}, status=400)
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
            print('brainstorm model')
            # brainstorm messages
            chat_history = mongo.brainstorm_collection.find({'source':source})
        
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
            return sanic.response.json({"status": "error", "message": "Missing model or source"}, status=400)
        print(f'messages:{messages}')
        # Return the result as JSON.
        print(f'\n\n normal return')
        return sanic.response.json({"status": "success", "messages": messages}, status=200)
    except Exception as ex:
        print(f'error2: {ex}')
        return sanic.response.json({"status": f"error: {ex}", "message": "No data provided"}, status=400)
    
@app.route("/download/<source>/summary.pdf")
async def download_pdf(request, source):
    """Download PDF endpoint"""
    # Find the latest PDF for this source
    pdf_files = [f for f in os.listdir('summaries') if f.startswith(source.replace('/', '_'))]
    if not pdf_files:
        return sanic.response.text("PDF not found", status=404)
    
    latest_pdf = sorted(pdf_files)[-1]
    return await file(f'summaries/{latest_pdf}')

@app.post("/update_summary")
async def update_text(request):
    data = request.json
    title = data.get("title")
    text = data.get("text")
    source = data.get("source")
    print(f'\nsource:{source}\ntitle: {title} \ntext: {text[:100]}...')
    
    print(f"Type of mongo: {type(mongo)}") # Add this line
    mongo.update_summary(source, title, text)
    
    return sanic.response.json({"status": "success"})

@app.route("/delete_source/<source>", methods=["POST"])
async def delete_source(request, source):
    """Delete source
    
    # decode text
    source = new%20project  # source given by front end
    urllib.parse.unquote(source) = "new project"
    
    """
    source = urllib.parse.unquote(source)
    print(f'\n\ndeleting source: {source}')

    # delete chunks of crawled data from mongo collection
    mongo.collection.delete_many({'source':source})

    # delete summary collection
    mongo.summary_collection.delete_many({'source':source})
    
    # Delete messages collection
    mongo.messages_collection.delete_many({'source':source})

    # Delete brainstorm collection
    mongo.brainstorm_collection.delete_many({'source':source})

    # Delete pdf files generated
    pdf_files = [f for f in os.listdir('summaries') if f.startswith(source+'_')]
    for file in pdf_files:
        os.remove(os.path.join('summaries', file))

    return sanic.response.json({"status": "success"})
    
@app.route("/download_conversation/<source>", methods=["POST"])
async def download_conversation(request, source):
    """Download conversation"""
    data = request.json
    model_name = data.get("model")
    
    # get conversation json file
    conversations = mongo.get_messages(source, model_name, exclude_timestamp=False)
    
    # Return the JSON directly with proper headers
    return sanic.response.json(
        conversations,
        headers={
            "Content-Disposition": f'attachment; filename="{source}_conversation.json"',
            "Content-Type": "application/json"
        }
    )



# View data for specific source
# -------------------------------

@app.route("/data/<source>", methods=["GET"])
@jinja.template("data_preview.html")
async def get_data(request, source):
    '''
    * Get all chunks for given source
    * return chunks
    '''
    source = urllib.parse.unquote(source)
    print(f'data-preview. source: {source}')
    try:
        # Aggregate to group chunks by URL
        pipeline = [
            {"$match": {"source": source}},
            {"$sort": {"chunk_index": 1}},
            {
                "$group": {
                    "_id": "$url",
                    "chunks": {
                        "$push": {
                            "text_content": "$text_content",
                            "chunk_index": "$chunk_index"
                        }
                    }
                }
            }
        ]
        
        cursor = mongo.collection.aggregate(pipeline)
        # results = await cursor.to_list(length=None)
        results = list(cursor.to_list(length=None))
        
        # Convert to JSON-serializable format
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "url": doc["_id"],
                "chunks": sorted(doc["chunks"], key=lambda x: x["chunk_index"])
            })
        return {"success": True, "data": formatted_results, "source": source}
    except Exception as e:
        print(e)
        return {"success": False, "error": str(e)}

@app.route("/update-source", methods=["POST"])
async def update_data(request, source):
    try:
        data = request.json
        url = data.get("url")
        chunks = data.get("chunks")
        
        if not url or not chunks:
            return json({"success": False, "error": "Missing required fields"}, status=400)
        
        # Delete existing chunks for this URL
        await app.ctx.collection.delete_many({"source": source, "url": url})
        
        # Insert new chunks
        documents = []
        for idx, chunk in enumerate(chunks):
            documents.append({
                "source": source,
                "url": url,
                "text_content": chunk,
                "chunk_index": idx
            })
        
        if documents:
            await app.ctx.collection.insert_many(documents)
        
        return json({"success": True})
    except Exception as e:
        return json({"success": False, "error": str(e)}, status=500)

# update chunk of crawled data
@app.post("/update-chunk")
async def update_chunk(request):
    data = request.json
    source = urllib.parse.unquote(data.get("source", None))
    url = urllib.parse.unquote(data.get("url", None))
    chunk_index = data.get("chunk_index", None)
    text_content = urllib.parse.unquote(data.get("text_content", None))

    print(f"data:{data}\n\n, source:\"{source}\", url:\"{url}\", chunk_index:\"{chunk_index}\", text_content:\"{text_content}\"")

    # if not all([source, url, chunk_index, text_content]):
    #     return sanic.response.json({"success": False, "error": "Missing data"}, status=400)

    # update
    result = mongo.collection.update_one(
        {"source": source, "url": url, "chunk_index": chunk_index},
        {"$set": {"text_content": text_content}}
    )
    
    if result.matched_count > 0:
        print("Update successful")
        return sanic.response.json({"success": True})
    else:
        print("No matching document found")
        return sanic.response.json({"success": False, "error": "No matching document found"})

# delete chunk of crawled data
@app.delete("/delete-chunk")
async def delete_chunk(request):
    data = request.json
    source = urllib.parse.unquote(data.get("source", None))
    url = urllib.parse.unquote(data.get("url", None))
    chunk_index = data.get("chunk_index", None)

    print(f"Deleting - source:\"{source}\", url:\"{url}\", chunk_index:\"{chunk_index}\"")

    # Delete from MongoDB
    result = mongo.collection.delete_one({
        "source": source,
        "url": url,
        "chunk_index": chunk_index
    })
    
    if result.deleted_count > 0:
        print("Delete successful")
        return sanic.response.json({"success": True})
    else:
        print("No matching document found")
        return sanic.response.json({"success": False, "error": "No matching document found"})

@app.delete("/delete-url")
async def delete_url(request):
    data = request.json
    source = urllib.parse.unquote(data.get("source", None))
    url = urllib.parse.unquote(data.get("url", None))

    if not all([source, url]):
        return sanic.response.json({"success": False, "error": "Missing required data"}, status=400)

    print(f"Deleting all chunks for - source:\"{source}\", url:\"{url}\"")

    try:
        # Delete all chunks for this URL from MongoDB
        result = mongo.collection.delete_many({
            "source": source,
            "url": url
        })
        
        if result.deleted_count > 0:
            print(f"Delete successful - removed {result.deleted_count} chunks")
            return sanic.response.json({
                "success": True,
                "message": f"Deleted {result.deleted_count} chunks"
            })
        else:
            print("No matching documents found")
            return sanic.response.json({
                "success": False, 
                "error": "No matching documents found"
            })
    except Exception as e:
        print(f"Error deleting URL: {str(e)}")
        return sanic.response.json({
            "success": False,
            "error": f"Database error: {str(e)}"
        }, status=500)


def is_url(text):
    """
    Checks if the given text is a valid URL.

    Args:
        text: The string to check.

    Returns:
        True if the text is a valid URL, False otherwise.
    """
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc])
    except:
        return False

# add new url or data to existing knowledge base
@app.post("/add-data")
async def add_data(request):
    '''
    * new version: user gives one source link at a time (from lean canvas page)
    '''
    data = request.json
    source = urllib.parse.unquote(data.get("source", None))
    new_input = urllib.parse.unquote(data.get("new_input", None))
    
    print(f"source:{source}\n\n, new_input:\"{new_input}\"")
    
    try:
        if is_url(new_input):
            # new input is url
            print(f'new_input is url')
            text_content = await crawl_text_content(new_input)
            documents = [{
                "source": source,
                "url": new_input,
                "text_content": text_content
            }]
            
            # print(f"documents:{documents}")
            
            # Save documents
            qa_system.save_documents(documents)

            print(f'saved to documents qa')
            return sanic.response.json({"success": True})
        else:
            print(f'new_input is text')
            document = {
                    'source': source,
                    'url': "mannual_input",
                    'text_content': new_input,
                    'chunk_index': mongo.collection.count_documents({"source":source, "url": "mannual_input"})  # count of Existing documents with source, url': "mannual_input"
                }
            mongo.collection.insert_one(document)

            # Re-generate lean canvas
            model_name = "gpt-4o"    # atoma models are not working right now.
            qa_system.regenerate_lean_canvas_v2(model_name, source)

        return sanic.response.json({"success": True})
    except Exception as ex:
        print(f' error adding new data: {ex}')
        return sanic.response.json({"success": False, "error": "No matching document found"})

# add new url or data to existing knowledge base
@app.post("/update-source-new")
async def update_source_new(request):
    data = request.json
    source = urllib.parse.unquote(data.get("source", None))
    new_name = urllib.parse.unquote(data.get("newName", None))
    if new_name:
        new_purpose = urllib.parse.unquote(data.get("newPurpose", None))
        
        
        print(f"source:{source}\n\n, new_name:\"{new_name}\" new_purpose:\"{new_purpose}\"")
        
        try:
            '''
            update in mongo collection
            find by source
                update:
                    source -> new_name
                    purpose -> new_purpose
            '''
            update_params = {
                "$set": {
                    "source": new_name,
                    "purpose": new_purpose
                }
            }
            mongo.collection.update_many({"source": source}, update_params)
            mongo.summary_collection.update_many({"source": source}, update_params)
            mongo.messages_collection.update_many({"source": source}, update_params)
            mongo.brainstorm_collection.update_many({"source": source}, update_params)
            
            return sanic.response.json({"success": True})
        except Exception as ex:
            print(f' error adding new data: {ex}')
            return sanic.response.json({"success": False, "error": "No matching document found"})
    else:
        return sanic.response.json({"success": False, "error": "Name can't be empty"})


# Questions
# -----------

@app.route("/questions/<source>", methods=["GET"])
@jinja.template("questions.html")
async def get_questions(request, source):
    '''
    * Get all chunks for given source
    * return chunks
    '''
    source = urllib.parse.unquote(source)
    print(f'data-preview. source: {source}')
    try:
        # Aggregate to group chunks by URL
        pipeline = [
            {"$match": {}},
        ]

        cursor = mongo.questions_collection.aggregate(pipeline)
        # results = await cursor.to_list(length=None)
        questions = list(cursor.to_list(length=None))
        
        return {"success": True, "questions": questions, "source": source}
    except Exception as e:
        print(e)
        return {"success": False, "error": str(e)}


@app.post("/update-qa")
async def update_qa(request):
    '''
    * new version: user gives one source link at a time (from lean canvas page)
    '''
    data = request.json
    source = urllib.parse.unquote(data.get("source", None))
    question_id = urllib.parse.unquote(data.get("question_id", None))
    answer = urllib.parse.unquote(data.get("answer", None))
    
    print(f"source:{source}\n\n, question_id:\"{question_id}\" answer: {answer}")
    
    try:
        mongo.update_question(question_id=question_id, updated_data={"answer": answer})
        
        return sanic.response.json({"success": True})
    except Exception as ex:
        print(f' error adding new data: {ex}')
        return sanic.response.json({"success": False, "error": "No matching document found"})


@app.post("/add-qa")
async def add_qa(request):
    '''
    Add a new question and answer pair
    '''
    data = request.json
    source = urllib.parse.unquote(data.get("source", None))
    question = urllib.parse.unquote(data.get("question", None))
    answer = urllib.parse.unquote(data.get("answer", None))
    
    print(f"Adding new Q&A - source: {source}, question: {question}, answer: {answer}")
    
    if not all([source, question, answer]):
        print("Missing required fields (source, question, or answer)")
        # return sanic.response.json({
        #     "success": False, 
        #     "error": "Missing required fields (source, question, or answer)"
        # })
    
    try:
        mongo.create_question(source=source, question=question, answer=answer)
        return sanic.response.json({"success": True})
    except Exception as ex:
        print(f'Error adding new Q&A: {ex}')
        return sanic.response.json({
            "success": False, 
            "error": str(ex)
        })

@app.delete("/delete-qa")
async def delete_qa(request):
    '''
    Delete a question and its associated answer
    '''
    data = request.json
    question_id = urllib.parse.unquote(data.get("question_id", None))
    
    print(f"Deleting Q&A with question_id: {question_id}")
    
    if not question_id:
        return sanic.response.json({
            "success": False, 
            "error": "Missing question_id"
        })
    
    try:
        mongo.delete_question(question_id=question_id)
        return sanic.response.json({"success": True})
    except Exception as ex:
        print(f'Error deleting Q&A: {ex}')
        return sanic.response.json({
            "success": False, 
            "error": str(ex)
        })



if __name__ == "__main__":
    os.makedirs('summaries', exist_ok=True)
    os.makedirs('conversations', exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)