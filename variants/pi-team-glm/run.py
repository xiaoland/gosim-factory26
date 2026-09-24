"""Own the complete Pi/Braid generation flow for this variant."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import time
import uuid

from agent_support import (save, phase, hashes, digest, logged, cleanup_workspace,
                           copy_application, copy_skill, deliver)
from braid_runtime import initialize_repository, load_delivery, export_delivery, archive_state
from core import archive_sessions
from browser import browser_wrapper

HERE = Path(__file__).resolve().parent
VARIANT = 'pi-team-glm'
DEFAULTS = {'issue': 'pi-glm-fast', 'pr': 'pi-glm-fast'}


def native_files(work, runtime, skills, base_url, visual_url):
    """返回供 Braid 使用的 profiles/bindings，并写出 Pi 消费的原生材料。

    成员主模型归 profile，内部角色归原生 agents Markdown。
    本次运行只替换连接与路径；包内有哪些技能和会话启用哪些技能分别选择。
    """
    profiles, bindings = [], {}
    browser_wrapper(work, work.parent.name, runtime)
    for source in sorted((HERE/'agents').iterdir()):
        profile = json.loads((source/'profile.json').read_text())
        folder = work/'capabilities'/profile['id']
        template = folder/'native-template'
        shutil.copytree(source, template)
        (template/'profile.json').unlink()
        (template/'instructions.md').unlink()
        profile.update(user_instructions=(source/'instructions.md').read_text(),
                       workspace=str(work/'application'))
        providers = json.loads((template/'models.json').read_text())
        providers['providers']['factory26']['baseUrl'] = base_url
        providers['providers']['factory26-visual'].update(
            baseUrl=visual_url or base_url,
            apiKey='$FACTORY26_VISUAL_API_KEY' if visual_url else '$FACTORY26_API_KEY')
        save(template/'models.json', providers)
        for role in (template/'agents').glob('*.md'):
            role.write_text(role.read_text().replace('@SKILLS@', json.dumps(str(skills))[1:-1]))
        observer = folder/'factory-subagent-observer.ts'
        shutil.copy2(HERE/'extensions/factory-subagent-observer.ts', observer)
        import shlex
        pi = runtime/'bin/pi' if (runtime/'bin/pi').is_file() else runtime/'node_modules/.bin/pi'
        flags = [str(pi), '--no-extensions', '--no-skills', '--no-prompt-templates', '--no-themes',
                 '--extension', str(runtime/'node_modules/pi-subagents/index.ts'),
                 '--extension', str(observer)]
        for skill in ('svc', 'ponytail', 'impeccable'):
            flags += ['--skill', str(skills/skill/'SKILL.md')]
        launcher = folder/'pi'
        launcher.write_text('#!/bin/sh\nexec '+shlex.join(flags)+' "$@"\n')
        launcher.chmod(0o755)
        bindings[profile['id']] = dict(adapter_type='pi', executable=str(launcher),
            api_key_environment='FACTORY26_API_KEY', native_template=str(template),
            native_home={'root':str(work/'native-homes')})
        profiles.append(profile)
    return profiles, bindings


def generate(args):
    """从本次 Braid 交付 commit 导出应用，并记录生成及辅助归档结果。

    prepare-only 只准备材料，不产生交付；进入生成后的失败保留工作现场。
    辅助归档异常单独记入 diagnostic_error，不能冒充外部评分或覆盖生成错误。
    """
    if not args.prepare_only and not (os.environ.get('OPENAI_API_KEY') or os.environ.get('FACTORY26_API_KEY')):
        raise ValueError('需要 OPENAI_API_KEY 或 FACTORY26_API_KEY')
    if bool(os.environ.get('VISUAL_BASE_URL')) != bool(os.environ.get('VISUAL_API_KEY')):
        raise ValueError('视觉 URL 与 key 必须同时提供')
    requirements = args.requirements_dir.resolve(strict=True)
    if not (requirements/'requirements.yaml').is_file():
        raise ValueError('需求目录缺少 requirements.yaml')
    runtime = args.runtime.resolve(strict=True)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    run = output/'.factory26'/(time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8])
    run.mkdir(parents=True)
    work = run/'work'; work.mkdir()
    app = work/'application'; app.mkdir()
    native = work/'home/.pi/agent'; native.mkdir(parents=True)
    (work/'tmp').mkdir()
    (work/'bin').mkdir()
    skills = work/'skills'
    for name in ('svc', 'ponytail', 'impeccable', 'agent-browser'):
        copy_skill(args.skills_root.resolve(strict=True)/name, skills/name)
    source_braid = (args.braid or runtime/'bin/braid').resolve(strict=True)
    shutil.copy2(source_braid, work/'bin/braid')
    (work/'bin/braid').chmod(0o755)
    inputs = run/'input'; shutil.copytree(requirements, inputs)
    base_url = args.base_url or os.environ.get('OPENAI_BASE_URL') or os.environ.get('FACTORY26_BASE_URL')
    if not base_url:
        raise ValueError('需要 --base-url 或 OPENAI_BASE_URL')
    visual_url = os.environ.get('VISUAL_BASE_URL')
    profiles, bindings = native_files(work, runtime, skills, base_url, visual_url)
    root_profile = next(p for p in profiles if p['id']==DEFAULTS['issue'])
    if os.environ.get('MODEL') and os.environ['MODEL'] != root_profile['model']:
        raise ValueError('平台主模型与此 variant 不一致')
    if visual_url and os.environ.get('VISUAL_MODEL') != 'deepseek-v4-flash-vision-exp':
        raise ValueError('平台视觉模型与此 variant 不一致')
    config = dict(variant=VARIANT, backend='pi', workflow='braid', svc=True,
                  task='platform', model=root_profile['model'], thinking=root_profile['reasoning'],
                  deployment='arcbench', benchmark_revision=None)
    save(run/'config.json', config)
    save(run/'input-hashes.json', hashes(inputs))
    code_files = [*HERE.glob('*.py'), *(HERE/'agents').rglob('*'), *(HERE/'extensions').rglob('*')]
    save(run/'implementation-hashes.json', {str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in code_files if p.is_file()})
    save(run/'materials.json', {'agents':hashes(HERE/'agents'), 'skills':hashes(skills),
                               'runtime':str(runtime), 'braid':str(source_braid)})
    prompt = f'''请根据 {inputs} 中完整需求包独立实现 Web 应用。使用当前工作项分配的 Git worktree。
阅读 requirements.md、requirements.yaml 和参考图片；格式错误或图片缺失时使用可读需求语义并记录问题。覆盖全部需求、场景和明确指定的初始数据，保留界面文字，使用可访问控件。
交付 frontend/package.json 和 backend/package.json。平台先在 frontend 执行 npm install、npm run build，再在 backend 执行 npm install、HOST=0.0.0.0 PORT=3000 npm run start。目标应用兼容 Node.js 20.19.3；后端必须通过 HOST/PORT 提供构建后的前端与 API，首页可访问；启动须在 120 秒内完成。禁止依赖根 npm start 或 deploy.sh；不要交付 requirements、.arc、.git、.factory26 等平台保留目录。
本任务授权在本次临时工作区内设计、实现、安装依赖、自检及本地 Git commit/merge。无人类中途介入；依据需求处理常规歧义，记录重要假设；遇到真实阻塞则报告，不等待用户。禁止 push、发布和修改外部系统或开发源码仓库。
可以编写运行自己的检查，完成后停止服务。不得读取、搜索或下载外部验收测试、benchmark 实现、参考应用或先前实验结果。只依据需求生成，自检后中文说明结果并结束。'''
    (run/'prompt.txt').write_text(prompt)
    state = run/'braid-state'
    pi = runtime/'bin/pi' if (runtime/'bin/pi').is_file() else runtime/'node_modules/.bin/pi'
    request = dict(profiles=profiles, defaults=DEFAULTS, bindings=bindings,
                   prompt=prompt, state=str(state), run_id=run.name,
                   delivery_ref='refs/heads/braid-delivery', codex=None,
                   pi=dict(executable=str(pi), home=str(native), api_key_environment='FACTORY26_API_KEY'))
    save(run/'braid-request.json', request)
    metadata = dict(config, started_at=time.time(), status='prepared' if args.prepare_only else 'generating')
    phase(run/'run.json', metadata, 'prepared')
    print(run, flush=True)
    if args.prepare_only:
        return run
    key = os.environ.get('OPENAI_API_KEY') or os.environ.get('FACTORY26_API_KEY')
    env = dict(os.environ, HOME=str(work/'home'), TMPDIR=str(work/'tmp'),
               XDG_CONFIG_HOME=str(work/'home/.config'), PI_CODING_AGENT_DIR=str(native),
               PI_TELEMETRY='0', PI_OFFLINE='1', FACTORY26_API_KEY=key,
               PATH=str(work/'bin')+os.pathsep+str(runtime/'bin')+os.pathsep+os.environ.get('PATH',''))
    if visual_url:
        env['FACTORY26_VISUAL_API_KEY'] = os.environ['VISUAL_API_KEY']
    begin = time.monotonic()
    error = None
    try:
        initialize_repository(app)
        phase(run/'run.json', metadata, 'braid', 'braid.log')
        code = logged([str(work/'bin/braid'), 'local', str(run/'braid-request.json')],
                      app, env, run/'braid.log', metadata.setdefault('cleanup_errors', []))
        metadata['process_exit_code'] = code
        if code:
            raise RuntimeError(f'braid local 退出 {code}；见 braid.log')
        delivery = load_delivery(state, app, work, request)
        metadata['delivery'] = delivery
        export_delivery(app, delivery['delivery_commit'], run/'application')
        deliver(run/'application', output)
        metadata['status'] = 'generated'
        save(run/'application-hashes.json', hashes(run/'application'))
        save(run/'delivery.json', {'status':'delivered', 'application_sha256':digest(hashes(run/'application'))})
    except BaseException as exc:
        error = exc
        metadata.update(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'generation_failed',
                        error=str(exc) or type(exc).__name__, failed_phase=metadata.get('phase'))
        save(run/'delivery.json', {'status':'failed','error':metadata['error']})
    finally:
        # Evidence failures stay separate from the generating process's original error.
        try:
            metadata['cleanup_pids'] = cleanup_workspace(work)
            entries = archive_state(state, run) if state.exists() else []
            archive_sessions(run, native, work, entries)
            shutil.copytree(work/'capabilities', run/'native-config')
        except Exception as exc:
            metadata['diagnostic_error'] = str(exc)
        metadata.update(generation_seconds=time.monotonic()-begin, generation_finished_at=time.time())
        phase(run/'run.json', metadata, 'frozen' if metadata['status']=='generated' else 'failed', 'braid.log')
    if error is not None:
        save(run/'recovery-workspace.json', {'path':str(work), 'request':str(run/'braid-request.json')})
        raise error
    shutil.rmtree(work)
    return run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('requirements_dir', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--type', choices=['web'], default='web')
    parser.add_argument('--runtime', type=Path, default=HERE/'runtime')
    parser.add_argument('--braid', type=Path)
    parser.add_argument('--skills-root', type=Path, default=HERE/'skills')
    parser.add_argument('--base-url')
    parser.add_argument('--prepare-only', action='store_true', help='写出真实原生材料和 Braid 请求，不调用模型')
    args = parser.parse_args()
    def interrupted(signum, frame):
        raise KeyboardInterrupt('运行终止信号')
    signal.signal(signal.SIGTERM, interrupted)
    generate(args)
