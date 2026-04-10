from jinja2 import Environment, FileSystemLoader
import sys

env = Environment(loader=FileSystemLoader('/home/aseps/MCP/korespondensi-server/templates'))

try:
    template = env.get_template('internal.html')
    template.render(rows=[], query='')
    print("Template internal.html parsed and rendered successfully!")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
