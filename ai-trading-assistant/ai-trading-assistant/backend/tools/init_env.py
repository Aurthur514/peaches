"""Initialize .env from config.example.env if .env does not exist."""
from pathlib import Path
import shutil

here = Path(__file__).resolve().parents[1]
example = here / 'config.example.env'
dotenv = here / '.env'

if not dotenv.exists() and example.exists():
    shutil.copy(example, dotenv)
    print('Copied', example, '->', dotenv)
else:
    print('.env already exists or example not found')
