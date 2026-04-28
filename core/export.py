1from pathlib import Path
import json
from datetime import datetime
from core.palace.reader import read_palace
from core.metrics.system_metrics import get_system_metrics  # assume exists
import glob

def export_memory(path='export_memory.json'):
    entries = read_palace()
    data = {'timestamp': datetime.now().isoformat(), 'entries': entries}
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f'Memory exported to {path} ({len(entries)} entries)')

def export_logs(path='export_logs.json'):
    logs = []
    for log_file in glob.glob('**/*.log', recursive=True):
        try:
            logs.append({'file': log_file, 'content': Path(log_file).read_text()})
        except:
            pass
    data = {'timestamp': datetime.now().isoformat(), 'logs': logs}
    Path(path).write_text(json.dumps(data, indent=2))
    print(f'Logs exported to {path}')

def export_metrics(path='export_metrics.json'):
    metrics = get_system_metrics() if 'get_system_metrics' in globals() else {'status': 'stub'}
    data = {'timestamp': datetime.now().isoformat(), 'metrics': metrics}
    Path(path).write_text(json.dumps(data, indent=2))
    print(f'Metrics exported to {path}')

def export_all(prefix='aletheia_export'):
    export_memory(f'{prefix}_memory.json')
    export_logs(f'{prefix}_logs.json')
    export_metrics(f'{prefix}_metrics.json')
    print('Full export complete.')
