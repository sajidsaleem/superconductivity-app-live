import os
import psycopg
import csv
import datetime
from dotenv import load_dotenv

# Load environment variables from .env file (for local use)
# On Render, the DATABASE_URL will be set in the environment directly.
load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

# The SQL command to create the table.
# "CREATE TABLE IF NOT EXISTS" will not cause an error if the table already exists.
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT,
    published_date DATE,
    summary TEXT,
    pdf_url TEXT
);
"""

def setup_and_load_data():
    if not DATABASE_URL:
        print("Error: DATABASE_URL is not set.")
        return

    print("Connecting to the database...")
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Step 1: Create the table if it doesn't exist
                print("Ensuring 'papers' table exists...")
                cur.execute(CREATE_TABLE_SQL)
                print("'papers' table is ready.")

                # Step 2: Load the data from the CSV file
                print("Reading data from 'arxiv_papers_2025-06-15.csv'...")
                inserted_count = 0
                csv_filename = 'arxiv_papers_2025-06-15.csv'
                with open(csv_filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        cur.execute(
                            """
                            INSERT INTO papers (id, title, author, published_date, summary, pdf_url)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING;
                            """,
                            (
                                row['id'], row['title'], row['author'],
                                row['published_date'], row['summary'], row['pdf_url']
                            )
                        )
                        inserted_count += cur.rowcount
                
                print(f"Successfully inserted {inserted_count} new papers.")
            
            # Commit all changes
            conn.commit()
            print("Transaction committed.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    setup_and_load_data()
