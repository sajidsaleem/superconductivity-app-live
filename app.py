import os
import psycopg
import math
from flask import Flask, render_template, request
from dotenv import load_dotenv

# This loads the .env file for local development.
# On Render, the environment variables are set in the dashboard.
load_dotenv()

# --- App Configuration ---
PAPERS_PER_PAGE = 10

# --- Database Connection ---
# This will get the DATABASE_URL from Render's environment variables when deployed,
# and from your .env file when run locally.
DATABASE_URL = os.environ.get('DATABASE_URL')

# --- Initialize the Flask App ---
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    papers = []
    query = ""
    page = request.args.get('page', 1, type=int)

    if request.method == 'POST':
        query = request.form.get('query', '')
        page = 1
    else:
        query = request.args.get('query', '')

    offset = (page - 1) * PAPERS_PER_PAGE
    total_papers = 0
    try:
        # Connect using the DATABASE_URL from the environment
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                base_query = "FROM papers"
                count_query = "SELECT COUNT(*) " + base_query
                main_query = "SELECT id, title, author, published_date, summary, pdf_url " + base_query
                
                params = []
                where_clauses = []

                if query:
                    where_clauses.append("(title ILIKE %s OR summary ILIKE %s)")
                    search_term = f"%{query}%"
                    params.extend([search_term, search_term])
                
                if where_clauses:
                    main_query += " WHERE " + " AND ".join(where_clauses)
                    count_query += " WHERE " + " AND ".join(where_clauses)
                
                cur.execute(count_query, params)
                total_papers = cur.fetchone()[0]

                main_query += " ORDER BY published_date DESC LIMIT %s OFFSET %s"
                params.extend([PAPERS_PER_PAGE, offset])
                
                cur.execute(main_query, params)
                db_papers = cur.fetchall()
                
                for paper in db_papers:
                    papers.append({
                        'id': paper[0],
                        'title': paper[1],
                        'author': paper[2],
                        'published_date': paper[3].strftime('%B %d, %Y'),
                        'summary': paper[4],
                        'pdf_url': paper[5]
                    })
    except Exception as e:
        print(f"Database error: {e}")

    total_pages = math.ceil(total_papers / PAPERS_PER_PAGE)

    return render_template('index.html', 
                           papers=papers, 
                           query=query,
                           page=page,
                           total_pages=total_pages,
                           page_title="Superconductivity Papers") # Added a default title
