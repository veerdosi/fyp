"""Send a recorded policy handoff to the running simulator. Root uses this tool."""
import argparse
import json
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('request_file')
parser.add_argument('--port', type=int, default=8765)
args = parser.parse_args()
data = Path(args.request_file).read_bytes()
json.loads(data)
request = urllib.request.Request(f'http://127.0.0.1:{args.port}/command', data=data,
                                 headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(request, timeout=180) as response:
    result = response.read().decode()
Path(args.request_file).with_suffix('.result.json').write_text(result)
print(result)
