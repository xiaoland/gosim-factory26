"""Bind immutable Harness definitions separately from one writable run.

The runner supplies verified input references. A delivered package can instead
describe its own identity; checkpoint publication still requires actual retained
artifact references, rather than inventing a store on the hosted platform.
"""
import hashlib
import json
import os
from pathlib import Path


def _read(path):
    return json.loads(path.read_text())


def _identity(root, definition_root, bindings):
    matches = []
    for value in bindings.values():
        source = Path(value['root']).resolve(strict=True)
        if root == source or source.is_dir() and root.is_relative_to(source):
            matches.append((source, value))
    if matches:
        source, value = max(matches, key=lambda row: len(row[0].parts))
        member = root.relative_to(source).as_posix()
        binding = {'reference': value['reference'], 'store': value['store'], 'member': member}
        return {'kind': 'artifact-member', 'reference': value['reference'], 'member': member}, binding
    package = definition_root / 'package-manifest.json'
    material = definition_root.parent / 'material.json'
    if root == definition_root or root.is_relative_to(definition_root):
        member = root.relative_to(definition_root).as_posix()
        if package.is_file():
            value = _read(package)
            return {'kind': 'package-member', 'manifest_sha256': hashlib.sha256(package.read_bytes()).hexdigest(),
                    'material_id': value.get('capabilities', {}).get('material_id'), 'member': member}, None
        if material.is_file():
            value = _read(material)
            if value.get('kind') != 'factory26.harness.material' or Path(value['root']).resolve() != definition_root:
                raise ValueError('material receipt does not bind this definition root')
            return {'kind': 'material-member', 'material_id': value['material_id'],
                    'manifest_sha256': hashlib.sha256(material.read_bytes()).hexdigest(), 'member': member}, None
    raise ValueError('Harness definition is not a frozen input or delivered material: ' + str(root))


def bind_layout(run, *, variant, definition_root, runtime, skills_root, braid=None,
                derived_inputs=(), extra_definitions=None):
    """Record fixed definitions and local derived inputs without copying assets.

Mutable source checkouts must first go through the material producer. Local
consumers use the existing verified-read contract; Docker enforces read-only
asset mounts. This record does not claim kernel isolation on a local host.
"""
    run = Path(run).resolve(strict=True)
    definition_root = Path(definition_root).resolve(strict=True)
    bindings = json.loads(os.environ.get('FACTORY26_EXP_INPUT_BINDINGS', '{}'))
    if not isinstance(bindings, dict):
        raise ValueError('runner input bindings must be an object')
    roots = {'agent': definition_root, 'runtime': Path(runtime).resolve(strict=True),
             'skills': Path(skills_root).resolve(strict=True)}
    if braid is not None:
        roots['braid'] = Path(braid).resolve(strict=True)
    for name, root in (extra_definitions or {}).items():
        if name in roots:
            raise ValueError('duplicate Harness definition role: ' + name)
        roots[name] = Path(root).resolve(strict=True)
    definitions = []
    for name, root in roots.items():
        if root == run or root.is_relative_to(run) or run.is_relative_to(root):
            raise ValueError('Harness definition and writable state overlap: ' + str(root))
        identity, binding = _identity(root, definition_root, bindings)
        row = {'name': name, 'logical_root': str(root), 'identity': identity}
        if binding is not None:
            row['artifact'] = binding
        definitions.append(row)
    members = []
    for value in derived_inputs:
        member = Path(value)
        if member.is_absolute() or '..' in member.parts or member == Path('.'):
            raise ValueError('derived input must be a bounded state-relative member')
        members.append(member.as_posix())
    value = {'kind': 'factory26.harness.layout', 'schema_version': 1, 'variant': variant,
             'state_root': str(run), 'application_root': str(run / 'work/application'),
             'definitions': definitions, 'derived_inputs': members}
    target = run / 'harness-layout.json'
    temporary = target.with_suffix('.partial')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    with temporary.open('rb') as stream:
        os.fsync(stream.fileno())
    temporary.replace(target)
    descriptor = os.open(run, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return value
