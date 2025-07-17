import logging
import json
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

def readLines(filePath: str) -> List[str]:
    """
    Read lines from a file and return them as a list of strings.
    """
    with open(filePath, 'r', encoding='utf-8') as file:
        lines: List[str] = [
            line.strip() for line in file if line.strip('\n')
        ]
        return lines

def readJsonFile(filePath: str) -> Optional[str]:
    """
    Read a JSON file and return its content as a string.
    """
    try:
        with open(filePath, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.warning(f"File '{filePath}' not found.")
        return None

def writeJsonFile(
    filePath: str, 
    data: Dict[str, List[Dict[str, str]]]
) -> None:
    """
    Dump the data to a JSON file.
    """
    with open(filePath, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)