"""Own the complete Pi/Braid generation flow for this variant."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid

from agent_support import (save, phase, hashes, digest, logged, cleanup_workspace,
                           copy_application, copy_skill, deliver, browser_executable, budgeted_pi)
from braid_runtime import (initialize_repository, read_runtime_result, load_delivery,
                           export_delivery, archive_state)
from core import archive_sessions

HERE = Path(__file__).resolve().parent
VARIANT = 'pi-braid-review'
ROOT_PROFILE_ID = 'pi-glm-fast'
MAIN_SKILLS = ('svc-task-packet', 'svc-investigation', 'svc-design', 'svc-implementation',
               'svc-verification', 'hyperformula', 'handsontable', 'better-auth-best-practices',
               'organization-best-practices', 'fixing-accessibility', 'ponytail', 'impeccable',
               'exploration-tools')
BACKGROUND_COMPLETION_RULE = ('后台命令若承担当前工作项的交付或验收，取得其完成结果和退出码后才报告完成；'
                              '需要常驻的服务在使用结束后主动停止。')

UI_CONDITIONS = '''新建应用的UI使用适合所选框架的成熟组件库和图标库，样式统一使用Tailwind CSS；接续既有应用时沿用基线技术栈，不为样式工具偏好迁移。按需求组合、定制已有控件，核对实际role、可访问名称、状态、键盘和焦点行为。统一少量视觉变量，图标随应用打包；动态样式采用所选Tailwind CSS版本可静态提取的完整类名映射或适当的CSS变量。
采用Tailwind CSS时，按所选版本的官方方式配置构建集成和CSS导入，确认应用入口实际加载该CSS。使用正式构建产物和正式启动路径，在实际页面核对代表性布局、颜色和字体的计算样式；不能仅凭构建成功声明样式生效。'''


def native_files(work, runtime, skills, base_url, visual_url):
    """返回供 Braid 使用的 profiles/bindings，并写出 Pi 消费的原生材料。

    成员主模型归 profile，内部角色归原生 agents Markdown。
    本次运行只替换连接与路径；包内有哪些技能和会话启用哪些技能分别选择。
    """
    background_bash = runtime/'node_modules/pi-background-bash/index.ts'
    if not background_bash.is_file():
        raise FileNotFoundError(f'后台执行扩展缺失：{background_bash}')
    profiles, bindings = [], {}
    for source in sorted((HERE/'agents').iterdir()):
        profile = json.loads((source/'profile.json').read_text())
        folder = work/'capabilities'/profile['id']
        template = folder/'native-template'
        shutil.copytree(source, template)
        (template/'profile.json').unlink()
        (template/'instructions.md').unlink()
        profile.update(user_instructions=(source/'instructions.md').read_text().rstrip() +
                       '\n\n' + BACKGROUND_COMPLETION_RULE + '\n\n' + UI_CONDITIONS + '\n',
                       workspace=str(work/'application'))
        providers = json.loads((template/'models.json').read_text())
        providers['providers']['factory26']['baseUrl'] = base_url
        providers['providers']['factory26-visual'].update(
            baseUrl=visual_url or base_url,
            apiKey='$FACTORY26_VISUAL_API_KEY' if visual_url else '$FACTORY26_API_KEY')
        save(template/'models.json', providers)
        methods = {'explorer': 'svc-investigation', 'executor': 'svc-implementation',
                   'specialist': 'svc-design'}
        for role in (template/'agents').glob('*.md'):
            instruction = role.read_text().replace('@SKILLS@', json.dumps(str(skills))[1:-1])
            if role.stem != 'vision':
                marker = 'extensions: ""'
                if marker not in instruction:
                    raise ValueError(f'内部角色扩展配置已变化：{role}')
                instruction = instruction.replace(marker, f'extensions: "{background_bash}"', 1)
                instruction += '\n' + BACKGROUND_COMPLETION_RULE + '\n'
            sources = []
            if role.stem in methods:
                sources += [skills/methods[role.stem]/'references/workflow.md',
                            skills/'exploration-tools/SKILL.md']
            if role.stem in ('executor', 'browser-operator'):
                sources.append(skills/'agent-browser/SKILL.md')
            # Keep methods authoritative in the frozen skill, not copied into role sources.
            for material in sources:
                instruction += f'\n方法或工具来源：{material}（相对链接基于 {material.parent}）。\n{material.read_text()}'
            role.write_text(instruction)
        observer = folder/'factory-subagent-observer.ts'
        shutil.copy2(HERE/'extensions/factory-subagent-observer.ts', observer)
        pi = budgeted_pi(runtime, work.parent)
        flags = [str(pi), '--no-extensions', '--no-skills', '--no-prompt-templates', '--no-themes',
                 '--extension', str(runtime/'node_modules/pi-subagents/index.ts'),
                 '--extension', str(background_bash),
                 '--extension', str(observer)]
        for skill in MAIN_SKILLS:
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
    """从选定集成分支的确切 commit 导出应用，分别记录运行与产物结果。

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
    pbb = runtime/'node_modules/pi-background-bash/bin/pbb.js'
    pil = runtime/'node_modules/pi-lane/bin/pil.js'
    if not pbb.is_file() or not pil.is_file():
        raise FileNotFoundError(f'后台任务 CLI 缺失：{pbb} 或 {pil}')
    pbb_launcher = work/'bin/pbb'
    pbb_launcher.write_text('#!/bin/sh\nexec ' + shlex.join((str(runtime/'bin/node'), str(pbb))) + ' "$@"\n')
    pbb_launcher.chmod(0o755)
    skills = work/'skills'
    for name in (*MAIN_SKILLS, 'agent-browser'):
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
    root_profile = next(p for p in profiles if p['id']==ROOT_PROFILE_ID)
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
    prompt = f'''本次任务的需求来源是 {inputs} 中的完整需求包，最终交付是满足需求的 Web 应用。使用当前工作项分配的本地 Git 仓库，并通过本次运行的 origin 共享已发布提交。
阅读 requirements.md、requirements.yaml 和参考图片；格式错误或图片缺失时使用可读需求语义并记录问题。覆盖全部需求、场景和明确指定的初始数据，保留界面文字，使用可访问控件。
请先将本任务拆分为多个子 Issue。按可以相对独立完成、验证的需求组织 Issue；紧密相关、需要连续处理才能形成完整结果的需求，合并为一个 Issue。每个子 Issue 说明要交付的结果、覆盖的需求和必要的依赖，提供所需的需求内容或材料入口。共享基础由一个明确的负责人实现，其他 Agent 基于其合入的成果继续，不在不同分支重复搭建。按依赖分批 assign 给合适的 Agent：依赖共享基础的工作，待基础成果合入共同分支后再指派；可独立推进的工作并行开展。Runner 资源有限，根 Issue 之外同时最多指派三个 Agent（包括 Issue 和 PR 的负责人），已指派但暂时空闲的 Agent 仍占用资源；前一批完成后再指派下一批。根 Issue 统筹依赖、整合各项成果并完成整体交付。
交付 frontend/package.json 和 backend/package.json。平台先在 frontend 执行 npm install、npm run build，再在 backend 执行 npm install、HOST=0.0.0.0 PORT=3000 npm run start。目标应用兼容 Node.js 20.19.3；后端必须通过 HOST/PORT 提供构建后的前端与 API，首页可访问；启动须在 120 秒内完成。禁止依赖根 npm start 或 deploy.sh；不要交付 requirements、.arc、.git、.factory26 等平台保留目录。
本任务授权在本次临时工作区及本次运行的 origin 内设计、实现、安装依赖、自检及 Git commit/merge/push/fetch。无人类中途介入；依据需求处理常规歧义，记录重要假设；遇到真实阻塞则报告，不等待用户。禁止向本次 origin 之外的外部系统或开发源码仓库 push、发布和修改。
可以编写运行自己的检查，完成后停止服务。不得读取、搜索或下载外部验收测试、benchmark 实现、参考应用或先前实验结果。只依据需求生成，最终交付时用中文说明结果。'''
    (run/'prompt.txt').write_text(prompt)
    state = run/'braid-state'
    pi = budgeted_pi(runtime, work.parent)
    request = dict(profiles=profiles, root_profile_id=ROOT_PROFILE_ID, bindings=bindings,
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
               PBB_PIL_BIN=str(pil),
               AGENT_BROWSER_EXECUTABLE_PATH=str(browser_executable(runtime)),
               AGENT_BROWSER_SOCKET_DIR=str(work/'b'),
               MCPORTER_CONFIG=str(skills/'exploration-tools/assets/mcporter.json'),
               PATH=os.pathsep.join((str(work/'bin'), str(runtime/'bin'),
                                     str(runtime/'node_modules/.bin'), os.environ.get('PATH',''))))
    if visual_url:
        env['FACTORY26_VISUAL_API_KEY'] = os.environ['VISUAL_API_KEY']
    begin = time.monotonic()
    error = None
    history = {'status': 'not_started'}
    history_stop = threading.Event()
    history_tool = HERE/'arc-runtime.pyz'
    if not history_tool.is_file():
        history_tool = HERE.parents[1]/'lab/arc_bench/agent_runtime/__main__.py'

    origin = state/'origin.git'

    def history_source_state():
        if not origin.is_dir():
            return 'waiting'
        repository = subprocess.run(['git', '-C', str(origin), 'rev-parse', '--git-dir'],
                                    capture_output=True, text=True)
        if repository.returncode:
            return 'error'
        ref = subprocess.run(['git', '-C', str(origin), 'rev-parse', '--verify',
                               '--end-of-options', request['delivery_ref']+'^{commit}'],
                              capture_output=True, text=True)
        return 'ready' if ref.returncode == 0 else 'waiting'

    def publish_history(*, preview=False, ref=None, source=None):
        if not history_tool.is_file():
            history.clear()
            history.update(status='unavailable', error=f'ARC runtime tool missing: {history_tool}')
            return
        if not preview and history_source_state() == 'waiting':
            history.clear()
            history.update(status='waiting')
            return
        history.clear()
        command = [sys.executable, str(history_tool), 'publish-history',
                   '--source-repo', str(source or origin), '--ref', ref or request['delivery_ref'],
                   '--output-dir', str(output), '--json']
        if preview:
            command.append('--preview')
        result = None
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            value = json.loads(result.stdout)
            if value['api_version'] != 1 or value['operation'] != 'publish-history':
                raise ValueError('unsupported ARC history result')
            history.update(status=value['status'], commit=value['result'].get('selected_commit'),
                           result=value['result'], error=value.get('error'),
                           diagnostic_error=value.get('diagnostic_error'),
                           exit_code=result.returncode, stderr=result.stderr)
            if result.returncode != (0 if value['status'] == 'completed' else 1):
                history.update(status='failed', protocol_error='ARC history exit code disagrees with result')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            history.update(status='failed', error={'type': type(exc).__name__, 'message': str(exc)},
                           stdout=result.stdout if result is not None else None,
                           stderr=result.stderr if result is not None else None,
                           exit_code=result.returncode if result is not None else None)

    def watch_history():
        # The selected delivery ref changes on merges, independently of the blocking Braid call.
        while not history_stop.is_set():
            publish_history()
            history_stop.wait(5)

    try:
        initialize_repository(app)
        phase(run/'run.json', metadata, 'braid', 'braid.log')
        history_thread = threading.Thread(target=watch_history, name='arc-history', daemon=True)
        history_thread.start()
        try:
            code = logged([str(work/'bin/braid'), 'local', str(run/'braid-request.json')],
                          app, env, run/'braid.log', metadata.setdefault('cleanup_errors', []))
        finally:
            history_stop.set()
            history_thread.join()
        metadata['process_exit_code'] = code
        metadata['braid'] = read_runtime_result(state)
        repository = Path(metadata['braid']['repository']).resolve(strict=True)
        delivery = load_delivery(repository, request)
        metadata['delivery'] = delivery
        export_delivery(repository, delivery['delivery_commit'], run/'application')
        deliver(run/'application', output)
        publish_history(preview=True, ref=delivery['delivery_commit'], source=repository)
        metadata['status'] = 'generated'
        save(run/'application-hashes.json', hashes(run/'application'))
        save(run/'delivery.json', {'status':'delivered', 'application_sha256':digest(hashes(run/'application'))})
    except BaseException as exc:
        error = exc
        metadata.update(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'generation_failed',
                        error=str(exc) or type(exc).__name__, failed_phase=metadata.get('phase'))
        save(run/'delivery.json', {'status':'failed','error':metadata['error']})
    finally:
        try:
            save(run/'history-publication.json', history)
        except OSError as exc:
            metadata['history_diagnostic_error'] = str(exc)
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
    if (error is not None or metadata.get('process_exit_code') != 0 or
            metadata.get('braid', {}).get('status') != 'quiescent' or
            history.get('status') != 'completed'):
        save(run/'recovery-workspace.json', {'path':str(work), 'request':str(run/'braid-request.json')})
    else:
        shutil.rmtree(work)
    if error is not None:
        raise error
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
