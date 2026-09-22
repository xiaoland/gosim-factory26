"""Materialize the selected capabilities into isolated native-core templates."""
import hashlib
import json
import os
import platform
from pathlib import Path
import shlex
import shutil
import subprocess

from profiles import ROOT, digest


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def runtime_cache(root=ROOT):
    packaged = root/'runtime'
    if (packaged/'bin/pi').is_file():
        return packaged
    fingerprint = hashlib.sha256((root/'harness/npm/package-lock.json').read_bytes()).hexdigest()[:16]
    return Path.home()/'.cache/factory26'/('runtime-'+fingerprint)


def bootstrap(root=ROOT):
    cache = runtime_cache(root)
    lock = root/'harness/npm/package-lock.json'
    if any(not (cache/'node_modules/.bin'/name).is_file() for name in ('pi', 'codex', 'agent-browser')) or not (cache/'package-lock.json').is_file() or (cache/'package-lock.json').read_bytes()!=lock.read_bytes():
        cache.mkdir(parents=True, exist_ok=True)
        for name in ('package.json', 'package-lock.json'):
            shutil.copy2(root/'harness/npm'/name, cache/name)
        subprocess.run(['npm', 'ci', '--prefix', str(cache)], check=True)
    # The CLI owns Chromium's version and download cache. It skips existing artifacts.
    subprocess.run([str(cache/'node_modules/.bin/agent-browser'), 'install'], env=dict(os.environ, HOME=str(cache)), check=True)
    return cache


def executable(core):
    cache = runtime_cache()
    path = cache/'bin'/core if (cache/'bin'/core).is_file() else cache/'node_modules/.bin'/core
    if not path.is_file():
        raise RuntimeError(f'{core} runtime unavailable; run bootstrap')
    return str(path)


def browser_wrapper(work, run_id, cache):
    """Native thread identity is per invocation, unlike HOME shared by children."""
    packaged_browser = cache/'bin/chromium'
    if packaged_browser.is_file():
        chrome = packaged_browser
    else:
        browsers = cache/'.agent-browser/browsers'
        pattern = 'chrome-*/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing' if platform.system()=='Darwin' else 'chrome-*/chrome'
        binaries = list(browsers.glob(pattern))
        if len(binaries) != 1:
            raise RuntimeError('locked browser executable is missing or ambiguous; run bootstrap')
        chrome = binaries[0]
    binary = cache/'bin/agent-browser' if (cache/'bin/agent-browser').is_file() else cache/'node_modules/.bin/agent-browser'
    target = work/'bin/agent-browser'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('''#!/usr/bin/env python3
import hashlib, json, os, sys
from pathlib import Path
identity = os.environ.get('PI_SESSION_ID') or os.environ.get('CODEX_THREAD_ID')
if not identity:
    raise SystemExit('agent-browser requires PI_SESSION_ID or CODEX_THREAD_ID')
args = sys.argv[1:]
if any(a in ('--session', '--session-name', '--profile', '--connect', '--cdp', '--all') or a.startswith(('--session=', '--session-name=', '--profile=', '--cdp=')) for a in args):
    raise SystemExit('Factory owns browser session isolation; use tab commands within this session')
name = hashlib.sha256((RUN_ID+':'+identity).encode()).hexdigest()[:16]
state = Path(STATE)/name
state.mkdir(parents=True, exist_ok=True)
(state/'identity.json').write_text(json.dumps({'run_id':RUN_ID,'native_session_id':identity}))
env = dict(os.environ, AGENT_BROWSER_SESSION=name, HOME=str(state), AGENT_BROWSER_EXECUTABLE_PATH=CHROME, AGENT_BROWSER_SOCKET_DIR=SOCKETS)
os.execve(BINARY, [BINARY, '--session', name, *args], env)
'''.replace('RUN_ID', repr(run_id)).replace('STATE', repr(str(work/'browser'))).replace('BINARY', repr(str(binary))).replace('CHROME', repr(str(chrome))).replace('SOCKETS', repr(str(work/'b'))))
    target.chmod(0o755)


def materialize(effective, work, responses_url, run_id, visual_base_url=None):
    cache = runtime_cache()
    if not Path(executable('pi')).is_file():
        raise RuntimeError('frozen native dependencies unavailable; run bootstrap')
    browser_wrapper(work, run_id, cache)
    materials = work/'capabilities'
    materials.mkdir()
    profiles, bindings = [], {}
    for profile_id, expanded in effective['profiles'].items():
        profile = expanded['profile']
        core = profile['core']
        folder = materials/profile_id
        template = folder/'native-template'
        template.mkdir(parents=True)
        (template/'AGENTS.md').write_text(expanded['common']['navigation'])
        # Roles have explicit skill roots. Parent sees only its selected catalog.
        skill_root = folder/'skills'
        for name, files in expanded['skills'].items():
            for relative, body in files.items():
                path = skill_root/name/relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body)
        versions = {'pi':expanded['core_version'], 'codex':expanded['core_version']}
        preload = ''.join(f'\n\nSVC 方法 `{item["path"]}`：\n\n{item["content"]}'
                          for item in expanded['svc_preload'])
        profiles.append(dict(id=profile_id, display_name=profile_id,
                             assignee_login=profile['assignee_login'],
                             assignee_description=profile['assignee_description'],
                             tags=[], adapter_type=core,
                             adapter_version=versions[core], provider='factory26', model=profile['model'],
                             reasoning=profile['reasoning'], user_instructions=expanded['instructions']+preload,
                             workspace=str(work/'application'),
                             context_soft_ratio=profile['context']['soft_ratio'],
                             context_hard_bytes=profile['context']['hard_bytes']))
        launcher = folder/core
        if core=='pi':
            consumers = [profile, *expanded['roles'].values()]
            providers = {}
            for kind, name, url, key in (
                    ('text', 'factory26', responses_url, '$FACTORY26_API_KEY'),
                    ('visual', 'factory26-visual', visual_base_url or responses_url,
                     '$FACTORY26_VISUAL_API_KEY' if visual_base_url else '$FACTORY26_API_KEY')):
                models = {consumer['model'] for consumer in consumers if consumer['provider'] == kind}
                if models:
                    providers[name] = dict(baseUrl=url, api='openai-completions', apiKey=key,
                                           models=[expanded['models'][model]['descriptor']
                                                   for model in sorted(models)])
            write_json(template/'models.json', {'providers':providers})
            write_json(template/'settings.json', {'packages':[], 'subagents':{'disableBuiltins':True}})
            observer = folder/'factory-subagent-observer.ts'
            observer.write_text(expanded['observer_extension'])
            extension = cache/'node_modules/pi-subagents/index.ts'
            for name, role in expanded['roles'].items():
                fields = dict(name=name, description=role['instructions'].split('。',1)[0],
                              model=('factory26-visual/' if role['provider']=='visual' else 'factory26/')+role['model'],
                              thinking=role['reasoning'],
                              tools=', '.join(role['tools']), systemPromptMode='append',
                              inheritProjectContext=False, inheritSkills=False,
                              defaultContext=role['context']['mode'],
                              skills=', '.join(role['skills']), skillPath=str(skill_root), extensions='')
                # JSON scalar values are valid YAML; no runtime YAML writer dependency.
                front = '\n'.join(f'{k}: {json.dumps(v, ensure_ascii=False)}' for k,v in fields.items())
                path = template/'agents'/f'{name}.md'
                path.parent.mkdir(exist_ok=True)
                path.write_text('---\n'+front+'\n---\n\n'+expanded['common']['navigation']+'\n'+role['instructions']+'\n')
            flags = ['--no-extensions','--no-skills','--no-prompt-templates','--no-themes',
                     '--extension',str(extension),'--extension',str(observer)]
            for skill in profile['skills']:
                flags += ['--skill', str(skill_root/skill/'SKILL.md')]
            launcher.write_text('#!/bin/sh\nexec '+shlex.join([executable(core), *flags])+' "$@"\n')
        else:
            from core import codex_config
            codex_config(template, responses_url, profile['model'], expanded['models'][profile['model']]['descriptor']['contextWindow'])
            shutil.copytree(skill_root, template/'skills')
            def skill_config(selected):
                return '\n[skills.bundled]\nenabled = false\n' + ''.join(
                    f'\n[[skills.config]]\nname = {json.dumps(name)}\nenabled = {str(name in selected).lower()}\n'
                    for name in expanded['skills'])
            with (template/'config.toml').open('a') as config:
                config.write(skill_config(profile['skills']))
                config.write('\n[agents]\nenabled = true\n')
                for name, role in expanded['roles'].items():
                    role_file = folder/(name+'.toml')
                    instructions = expanded['common']['navigation']+'\n'+role['instructions']
                    for skill in role['skills']:
                        instructions += f'\n需要 {skill} 方法时读取 {skill_root/skill/"SKILL.md"}。'
                    window = expanded['models'][role['model']]['descriptor']['contextWindow']
                    role_file.write_text(f'model = {json.dumps(role["model"])}\nmodel_context_window = {window}\nmodel_reasoning_effort = {json.dumps(role["reasoning"])}\ndeveloper_instructions = {json.dumps(instructions, ensure_ascii=False)}\n' + skill_config(role['skills']))
                    config.write(f'\n[agents.{json.dumps(name)}]\ndescription = {json.dumps(role["instructions"].split("。",1)[0], ensure_ascii=False)}\nconfig_file = {json.dumps(str(role_file))}\n')
            launcher.write_text('#!/bin/sh\nexec '+shlex.quote(executable(core))+' "$@"\n')
        launcher.chmod(0o755)
        bindings[profile_id] = dict(adapter_type=core, executable=str(launcher),
             api_key_environment='FACTORY26_API_KEY', native_template=str(template),
             native_home={'root':str(work/'native-homes')},
             capabilities={'digest':expanded['effective_profile_digest']})
    return profiles, bindings
