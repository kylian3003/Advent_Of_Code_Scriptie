import re
import ast
from radon.complexity import cc_visit, average_complexity
from cognitive_complexity.api import get_cognitive_complexity as get_cognitive_complexity_for_function


def get_part(filename):
    """Try to figure out if this file is part 1 or 2 based on the filename.
    Returns None if it can't be determined."""
    if re.search(r"part[_\-]?1|p1\b|[_\-]1\.|[_\-]?a\.py", filename, re.IGNORECASE):
        return 1
    if re.search(r"part[_\-]?2|p2\b|[_\-]2\.|[_\-]?b\.py", filename, re.IGNORECASE):
        return 2
    return None


def get_cyclomatic_complexity(source):
    """Compute the average cyclomatic complexity of all functions in the file.
    Returns None if the file can't be parsed."""
    try:
        results = cc_visit(source)
        if not results:
            return None
        return round(average_complexity(results), 2)
    except Exception:
        return None
    
    
def get_cognitive_complexity(source):
    """Compute the average cognitive complexity across all top-level functions in the file.
    Cognitive complexity measures how hard code is to understand, rather than
    just counting paths like cyclomatic complexity does.
    Returns None if the file can't be parsed."""
    try:
        tree = ast.parse(source)
        scores = []
        # only iterate top-level nodes to avoid double-counting nested functions
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                score = get_cognitive_complexity_for_function(node)
                scores.append(score)
        if not scores:
            return None
        return round(sum(scores) / len(scores), 2)
    except Exception:
        return None
    
    
def get_file_status(source):
    """Check whether a file has functions and whether it parses successfully.
    Returns one of: 'ok', 'no_functions', 'parse_error'"""
    try: 
        tree = ast.parse(source)
        has_functions = any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            for node in tree.body
        )
        if not has_functions:
            return "no_functions"
        return "ok"
    except Exception:
        return "parse_error"
    
    

def extract_features(py_file):
    """Extract all features from a single solution file.
    Metadata comes from the folder structure: corpus/username/year/dayNN/file.py"""
    parts = py_file.parts
    username = parts[-4]
    year = int(parts[-3])
    day = int(parts[-2].replace("day", ""))
    part = get_part(py_file.name)
    
    source = py_file.read_text(encoding="utf-8", errors="replace")
    
    return {
        "username": username,
        "year": year,
        "day": day,
        "part": part,
        "cyclomatic_complexity": get_cyclomatic_complexity(source),
        "cognitive_complexity": get_cognitive_complexity(source),
        # status is used for the summary in main.py, not written to the csv
        "_status": get_file_status(source),
    }
