# Cloze Flashcard Generator

A Python application that generates optimal cloze flashcards from sentences using various algorithms to select the most effective sentences for language learning.

## Overview

This application processes a file of sentences and generates cloze flashcards (fill-in-the-blank style) by intelligently selecting the most useful sentences for each word. It supports two different algorithms for choosing sentences and can prioritize shorter sentences for better learning effectiveness.

## Features

- **Two selection algorithms**:
  - `mostDifferent`: Selects sentences that are most semantically different from each other
- **Configurable parameters**:
  - Number of flashcards per word (n)
  - Option to benefit shorter sentences
  - Preserves existing "in-use" flashcards
- **JSON output format** for easy integration with flashcard applications
- **Performance profiling** with optional cProfile integration
- **Comprehensive logging** with configurable levels

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

The main script can be run with default parameters:

```bash
python clozeFlashcardGenerator.py
```

### Configuration

By default, the application uses:
- **Input file**: `sentences.txt`
- **Output file**: `clozeFlashcards.json`
- **Algorithm**: `mostDifferent`
- **Flashcards per word**: 3
- **Benefit shorter sentences**: True

To modify these settings, edit the parameters in the `__main__` section of `clozeFlashcardGenerator.py`:

```python
inputFilePath: str = 'sentences.txt'
outputFilePath: str = 'clozeFlashcards.json'
clozeChoosingAlgorithm: str = "mostDifferent"
n: int = 3
benefitShorterSentences: bool = True
```

## Input Format

### sentences.txt

The input file should contain one sentence per line. Sentences should:
- Use single spaces between words
- Not have leading or trailing whitespace
- Only contain letters, spaces, and the following punctuation: `,`, `.`, `?`, `_`
- `_` indicates multi-word expressions (e.g., ")

Example:
```
jak mogę dostać_1 się_1 do apteki?
możesz pojechać autobusem
możesz pojechać samochodem
```

## Output Format

The application generates a JSON file with the following structure:

```json
{
    "word": [
        {
            "beforeCloze": "text before the blank",
            "midCloze": "text in the middle of the blank which isn't blank (optional)",
            "afterCloze": "text after the blank",
            "clozeWordPart1": "first part of word to fill",
            "closeWordPart2": "second part of word if the word is a multi-word expression",
            "inUse": "True/False"
        }
    ]
}
```

## Algorithms

### Most Different Algorithm

Selects sentences that are most semantically different from each other using:
- **Cosine dissimilarity**: Measures how different sentence word vectors are
- **Combinatorial optimization**: Finds the combination of sentences with maximum total dissimilarity

## File Structure

- `clozeFlashcardGenerator.py` - Main application entry point
- `models.py` - Core data classes (RawLine, RawWord, ClozeFlashcard, etc.)
- `algorithms.py` - Implementation of selection algorithms
- `utils.py` - Utility functions for data processing and validation
- `readWrite.py` - File I/O operations
- `sentences.txt` - Input file with sentences
- `clozeFlashcards.json` - Generated flashcards output

## Logging

The application supports different logging levels. To change the logging level, modify this line in `clozeFlashcardGenerator.py`:

```python
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG, WARNING, ERROR, or CRITICAL
    format='%(levelname)s: %(message)s'
)
```

When set to DEBUG level, the application will also generate performance profiling data.

## Performance Profiling

When logging is set to DEBUG level, the application automatically:
- Runs cProfile during execution
- Outputs performance statistics to console
- Saves detailed profiling data to `profile_results.prof`

## Requirements

- Python 3.7+
- NumPy (for vector operations and cosine similarity calculations)

## Contributing

1. Ensure all sentences in your input file follow the specified format
2. Test with both algorithms to compare results
3. Use appropriate logging levels for debugging vs. production use

## License

This project is provided as-is for educational and personal use.
