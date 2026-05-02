import csv
from pathlib import Path
from extract_features import extract_features

CORPUS_DIR = r"C:\Users\kylia\Documents\uni\Scriptie\corpus"
OUTPUT_CSV = r"C:\Users\kylia\Documents\uni\Scriptie\dataset.csv"

FIELDNAMES = ["username", "year", "day", "part", "cyclomatic_complexity", "cognitive_complexity"]


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