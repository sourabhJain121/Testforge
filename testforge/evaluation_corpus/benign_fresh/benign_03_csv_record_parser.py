import csv
import io
from typing import List, Dict

def parse_user_csv(data: str) -> List[Dict[str, str]]:
    stream = io.StringIO(data)
    reader = csv.DictReader(stream)
    return [dict(row) for row in reader if row.get('id')]
