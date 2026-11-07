import configparser
import io
from typing import Dict

def parse_ini_string(ini_text: str) -> Dict[str, Dict[str, str]]:
    parser = configparser.ConfigParser()
    parser.read_file(io.StringIO(ini_text))
    return {section: dict(parser.items(section)) for section in parser.sections()}
