import os
import sys
import csv
import json
import time
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

CORPUS_DIR = r'C:\Users\kylia\Documents\uni\Advent_Of_Code_Sctiptie\corpus'
DATASET_CSV = r'C:\Users\kylia\Documents\uni\Advent_Of_Code_Sctiptie\dataset.csv'
OUTPUT_CSV  = r'C:\Users\kylia\Documents\uni\Advent_Of_Code_Sctiptie\dataset_readability.csv'

READABILITY_FIELDS = [
    'username', 'year', 'day', 'filename',
    'readability_score',
    'naming', 'modularity', 'control_flow', 'comments_docs', 'pythonic_style'
]

PROMPT = '''You are an expert software engineer and code reviewer specializing in Python.
Your task is to evaluate the human readability of the Python script provided below.
Act as a strict, consistent zero-shot annotator. Do NOT consider runtime efficiency.
Focus solely on how easy it is for a human developer to read, understand, and maintain this script.

Evaluate the script across these five dimensions:
1. Variable & function naming - Are identifiers descriptive and consistent?
   Penalise single-letter names, cryptic abbreviations, or misleading names.
2. Modularity & structure - Is the code broken into logical, reusable units?
   Penalise monolithic blocks or deeply nested logic.
3. Control flow clarity - Are conditionals and loops straightforward to follow?
   Penalise deeply nested conditions or overly clever one-liners.
4. Comments & documentation - Are non-obvious sections explained?
   Penalise the complete absence of comments on complex logic.
5. Pythonic style & consistency - Does the code follow PEP 8 and idiomatic Python?
   Penalise inconsistent formatting or anti-patterns.

Scoring scale (1-10):
  1-2  : Nearly unreadable. Extremely cryptic, no structure, no naming conventions.
  3-4  : Poor readability. Some structure but major clarity issues throughout.
  5-6  : Average readability. Readable with effort, a mix of good and poor practices.
  7-8  : Good readability. Mostly clear, minor issues only.
  9-10 : Excellent readability. Clean, well-named, well-structured, immediately understandable.

PYTHON SCRIPT TO ANNOTATE:
{code}

Respond with ONLY a valid JSON object, no markdown, no preamble, no extra text.
Use this exact schema:
{{
  "readability_score": <integer 1-10>,
  "naming": <integer 1-10>,
  "modularity": <integer 1-10>,
  "control_flow": <integer 1-10>,
  "comments_docs": <integer 1-10>,
  "pythonic_style": <integer 1-10>
}}'''


def load_csv(filepath):
    '''
    This function loads dataset.csv and returns the rows and fieldnames.
    '''
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def load_completed(filepath):
    '''
    This function loads already completed rows from the output csv as a set of keys.
    '''
    completed = set()
    if not os.path.isfile(filepath):
        return completed
    with open(filepath, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            completed.add((row['username'], row['year'], row['day'], row['filename']))
    return completed


def append_row(filepath, row):
    '''
    This function appends a single result row to the output csv.
    '''
    file_exists = os.path.isfile(filepath)
    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=READABILITY_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def read_file(filepath):
    '''
    This function reads a Python file and returns its contents as a string.
    '''
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def call_gemini(code, client):
    '''
    This function sends the code to the Gemini API and returns the parsed JSON result.
    Retries up to 5 times on rate limit or server errors, waiting 60 seconds between attempts.
    '''
    max_retries = 5
    wait_seconds = 60

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=PROMPT.format(code=code),
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type='application/json'
                )
            )
            return json.loads(response.text.strip())
        except Exception as e:
            error = str(e)
            if '429' in error or '500' in error or '503' in error:
                if attempt < max_retries:
                    print('\nRate limit or server error, retrying in {}s ({}/{})...'.format(
                        wait_seconds, attempt, max_retries), file=sys.stderr)
                    time.sleep(wait_seconds)
                else:
                    raise
            else:
                raise


def find_file(corpus_dir, username, year, day, filename):
    '''
    This function reconstructs the path to a Python file from its metadata.
    '''
    return Path(corpus_dir) / username / str(year) / 'day{:02d}'.format(int(day)) / filename


def main():
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print('No API key found. Add GEMINI_API_KEY to your .env file.', file=sys.stderr)
        exit(-1)

    client = genai.Client(api_key=api_key)
    rows = load_csv(DATASET_CSV)
    completed = load_completed(OUTPUT_CSV)
    total = len(rows)

    for i, row in enumerate(rows, 1):
        key = (row['username'], row['year'], row['day'], row['filename'])

        # skip rows that were already annotated in a previous run
        if key in completed:
            print('Already annotated: {}/{}'.format(i, total), end='\r', flush=True)
            continue

        print('Annotating: {}/{}'.format(i, total), end='\r', flush=True)

        try:
            py_file = find_file(
                CORPUS_DIR,
                row['username'], row['year'], row['day'], row['filename']
            )
            code = read_file(py_file)
            result = call_gemini(code, client)

            append_row(OUTPUT_CSV, {
                'username':         row['username'],
                'year':             row['year'],
                'day':              row['day'],
                'filename':         row['filename'],
                'readability_score': result['readability_score'],
                'naming':           result['naming'],
                'modularity':       result['modularity'],
                'control_flow':     result['control_flow'],
                'comments_docs':    result['comments_docs'],
                'pythonic_style':   result['pythonic_style']
            })

        except Exception as e:
            print('\nSkipped {} {}/{} {}: {}'.format(
                row['username'], row['year'], row['day'], row.get('filename', '?'), e), file=sys.stderr)
            continue

    print('\nDone. Results saved to {}'.format(OUTPUT_CSV))


if __name__ == '__main__':
    main()