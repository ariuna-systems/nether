import os
from pathlib import Path

from radon.raw import analyze


def compute_sloc(directory: Path):
  total_sloc = 0
  for root, _, files in os.walk(directory):
    for file in files:
      if file.endswith(".py"):
        file_path = Path(root) / file
        with Path.open(file_path, encoding="utf-8") as f:
          code = f.read()
          analysis = analyze(code)
          total_sloc += analysis.sloc
  return total_sloc


if __name__ == "__main__":
  project_directory = Path("src")
  total_sloc = compute_sloc(project_directory)
  print(f"Total SLOC: {total_sloc}")
