import re
import csv
from pathlib import Path
from radon.complexity import cc_visit, average_complexity

CORPUS_DIR = r"C:\Users\kylia\Documents\uni\Advent_Of_Code_Sctiptie\corpus"
OUTPUT_CSV = r"C:\Users\kylia\Documents\uni\Advent_Of_Code_Sctiptie\dataset.csv"

# column names for the csv
FIELDNAMES = ["username", "year", "day", "part", "cyclomatic_complexity"]


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


def extract_features(py_file):
    """Extract all features from a single solution file.
    Metadata comes from the folder structure: corpus/username/year/dayNN/file.py"""
    parts = py_file.parts
    username = parts[-4]
    year = int(parts[-3])
    day = int(parts[-2].replace("day", ""))
    part = get_part(py_file.name)

    source = py_file.read_text(encoding="utf-8", errors="replace")
    complexity = get_cyclomatic_complexity(source)

    return {
        "username": username,
        "year": year,
        "day": day,
        "part": part,
        "cyclomatic_complexity": complexity,
    }


def main():
    corpus = Path(CORPUS_DIR)

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

        for py_file in sorted(corpus.rglob("*.py")):
            features = extract_features(py_file)
            writer.writerow(features)
            print(features)


if __name__ == "__main__":
    main()