"""Build and export this variant's frozen Linux e2e addon."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from lab.docker_endpoint import freeze, environment, confirm

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--docker-context')
args = parser.parse_args()
output = args.output.resolve()
if output.exists():
    raise FileExistsError(output)
source = Path(__file__).resolve().parent/'e2e'
inputs = {file.name: hashlib.sha256(file.read_bytes()).hexdigest()
          for file in source.iterdir() if file.is_file()}
endpoint = freeze(args.docker_context)
docker = endpoint['argv']
docker_env = environment(endpoint)
name = 'factory26-i14-e2e-'+uuid.uuid4().hex
created = False
try:
    subprocess.run(docker+['build', '--platform', 'linux/amd64', '-t', name, str(source)], check=True, env=docker_env)
    confirm(endpoint)
    subprocess.run(docker+['create', '--name', name, name], check=True, env=docker_env)
    created = True
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(docker+['cp', name+':/e2e', str(output)], check=True, env=docker_env)
finally:
    confirm(endpoint)
    if created:
        subprocess.run(docker+['rm', name], check=True, env=docker_env)
    subprocess.run(docker+['image', 'rm', '--no-prune', name], check=False, env=docker_env)
(output/'addon-source.json').write_text(json.dumps({
    'platform': 'linux-x86_64',
    'docker_endpoint': endpoint,
    'inputs': inputs,
}, indent=2)+'\n')
print(output)
