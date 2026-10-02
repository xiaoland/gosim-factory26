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
import tempfile
import time
import uuid

from agent_support import (save, phase, hashes, digest, logged, cleanup_workspace,
                           copy_application, copy_skill, deliver, browser_executable, budgeted_pi,
                           start_local_telemetry, telemetry_environment, stop_local_telemetry)
from braid_runtime import (initialize_repository, read_runtime_result, load_delivery,
                           export_delivery, archive_state)
from core import archive_sessions

HERE = Path(__file__).resolve().parent
VARIANT = 'pi-braid'
ROOT_PROFILE_ID = 'pi-glm-fast'
MAIN_SKILLS = ('svc-sub-agents', 'svc-task-packet', 'svc-investigation', 'svc-design', 'svc-implementation',
               'svc-verification', 'hyperformula', 'handsontable', 'better-auth-best-practices',
               'organization-best-practices', 'fixing-accessibility', 'ponytail', 'impeccable',
               'agent-browser')
BACKGROUND_COMPLETION_RULE = ('后台检查或构建使用普通 background 任务，取得完成结果和退出码后才报告完成；'
                              '开发服务器或watcher使用 bash 的 service:true，使其作为常驻服务运行，使用结束后主动停止。'
                              '普通后台任务会参与原生完成等待；没有独立工作可做时结束当前回应，由完成消息继续会话，不另启sleep轮询。')


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
                       '\n\n' + BACKGROUND_COMPLETION_RULE + '\n',
                       workspace=str(work/'application'))
        providers = json.loads((template/'models.json').read_text())
        providers['providers']['factory26']['baseUrl'] = base_url
        providers['providers']['factory26-visual'].update(
            baseUrl=visual_url or base_url,
            apiKey='$FACTORY26_VISUAL_API_KEY' if visual_url else '$FACTORY26_API_KEY')
        save(template/'models.json', providers)
        methods = {'explorer': 'svc-investigation', 'executor': 'svc-implementation',
                   'advisor': 'svc-design'}
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
                sources.append(skills/methods[role.stem]/'references/workflow.md')
            if role.stem == 'browser-operator':
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
    for name in MAIN_SKILLS:
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
    code_files = [*HERE.glob('*.py'), *(HERE/'agents').rglob('*'), *(HERE/'extensions').rglob('*'),
                  *(HERE/'tools').rglob('*')]
    save(run/'implementation-hashes.json', {str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in code_files if p.is_file()})
    save(run/'materials.json', {'agents':hashes(HERE/'agents'), 'skills':hashes(skills),
                               'runtime':str(runtime), 'braid':str(source_braid)})
    prompt = f'''本次任务的需求来源是 {inputs} 中的完整需求包，最终交付是满足需求的 Web 应用。使用当前工作项分配的本地 Git 仓库，并通过本次运行的 origin 共享已发布提交。
阅读 requirements.md、requirements.yaml 和参考图片；格式错误或图片缺失时使用可读需求语义并记录问题。覆盖全部需求、场景和明确指定的初始数据，保留界面文字，使用可访问控件。
先在根 Issue 完成足以支撑分工的产品、技术与验收方案：结合原始需求、场景和参考图，明确关键用户路径、并列对象的范围、初始状态的归属、跨任务接口与共用视觉/交互约定，保留重要假设和未决问题。只记录影响分工或验收的决定，不以整理后的摘要替代原需求。
根 Issue 直接负责共享架构、脚手架与开发反馈设施的设计和交付；创建关联根 Issue 的基础 PR 并指派独立负责人实施，不再把整套基础责任转为子 Issue，也不在 Issue 工作区先完成应用实现。基础 PR 要发布可消费的接口与最小真实使用结果，根负责人核实后合入共同分支。
将业务需求拆分为多个子 Issue：按可相对独立交付、验证的结果组织，紧密相关、需要连续处理的需求合为一项。每个子 Issue 自包含相关原需求和场景入口、要交付的结果、前置数据/状态、共享决定及依赖；父 Issue 正文不会自动成为子项上下文。按依赖分批 assign 给合适的 Agent，消费基础成果的业务项在基础可用后启动，可独立工作并行开展。基础回归问题出现时根据受影响边界调整分派，不把曾经合并当作当前仍可用的证明。根 Issue 统筹依赖与整合，并通过最终整合 PR 完成整体交付。
交付 frontend/package.json 和 backend/package.json。平台先在 frontend 执行 npm install、npm run build，再在 backend 执行 npm install、HOST=0.0.0.0 PORT=3000 npm run start。目标应用兼容 Node.js 20.19.3；后端必须通过 HOST/PORT 提供构建后的前端与 API，首页可访问；启动须在 120 秒内完成。禁止依赖根 npm start 或 deploy.sh；不要交付 requirements、.arc、.git、.factory26 等平台保留目录。
本任务授权在本次临时工作区及本次运行的 origin 内设计、实现、安装依赖、自检及 Git commit/merge/push/fetch。无人类中途介入；依据需求处理常规歧义，记录重要假设；遇到真实阻塞则报告，不等待用户。禁止向本次 origin 之外的外部系统或开发源码仓库 push、发布和修改。
生成、自检与后续评测共用环境。3000 端口留给官方评测，自检时显式设置其它空闲端口，并为并行服务分别选端口。自检数据库、缓存、上传文件和浏览器状态使用临时位置，不改变交付应用的初始状态。交付应用仍按平台提供的 HOST/PORT 启动，并通过正常启动准备需求所需初始数据。完成自检后停止自己启动的服务，交接时告知后续负责人这些约定。
可以编写运行自己的检查，完成后停止服务。不得读取、搜索或下载外部验收测试、benchmark 实现、参考应用或先前实验结果。只依据需求生成，最终交付时用中文说明结果。'''
    (run/'prompt.txt').write_text(prompt)
    state = run/'braid-state'
    pi = budgeted_pi(runtime, work.parent)
    request = dict(profiles=profiles, root_profile_id=ROOT_PROFILE_ID, bindings=bindings,
                   prompt=prompt, state=str(state), run_id=run.name,
                   delivery_ref='refs/heads/main', codex=None,
                   pi=dict(executable=str(pi), home=str(native), api_key_environment='FACTORY26_API_KEY'))
    save(run/'braid-request.json', request)
    metadata = dict(config, started_at=time.time(), status='prepared' if args.prepare_only else 'generating')
    phase(run/'run.json', metadata, 'prepared')
    print(run, flush=True)
    if args.prepare_only:
        return run
    key = os.environ.get('OPENAI_API_KEY') or os.environ.get('FACTORY26_API_KEY')
    browser = str(browser_executable(runtime))
    # Chromium sockets require a short path; retain Pi's durable async state separately.
    env = dict(os.environ, HOME=str(work/'home'), TMPDIR=tempfile.mkdtemp(prefix='f26-', dir='/tmp'),
               PI_SUBAGENTS_TEMP_ROOT=str(work/'tmp'/f'pi-subagents-uid-{os.getuid()}'),
               XDG_CONFIG_HOME=str(work/'home/.config'), PI_CODING_AGENT_DIR=str(native),
               PI_TELEMETRY='0', PI_OFFLINE='1', FACTORY26_API_KEY=key,
               FACTORY26_PI_TIMING_EXTENSION=str(HERE/'extensions/factory-pi-timing.ts'),
               FACTORY26_PI_TIMING_FILE=str(run/'pi-timing.jsonl'),
               PBB_PIL_BIN=str(pil),
               AGENT_BROWSER_EXECUTABLE_PATH=browser,
               BROWSER_EXECUTABLE_PATH=browser,
               BROWSER_CHECK_NODE_MODULES=str(runtime/'node_modules'),
               AGENT_BROWSER_SOCKET_DIR=str(work/'b'),
               MCPORTER_CONFIG=str(HERE/'tools/mcporter.json'),
               PATH=os.pathsep.join((str(work/'bin'), str(runtime/'bin'),
                                     str(runtime/'node_modules/.bin'), os.environ.get('PATH',''))))
    collector = None
    try:
        collector, binding = start_local_telemetry(run)
        env.update(telemetry_environment(binding))
    except Exception as exc:
        metadata['telemetry_diagnostic_error'] = f'{type(exc).__name__}: {exc}'
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
        metadata['cleanup_pids'] = cleanup_workspace(run)
        # Quiescence describes the scheduler. The root's state is the team's completion report.
        result = metadata['braid']
        if code != 0 or result.get('status') != 'quiescent':
            raise RuntimeError(f'Braid 未正常结束：exit={code}；result={json.dumps(result, ensure_ascii=False)}')
        if result.get('root_issue', {}).get('state') != 'CLOSED':
            raise RuntimeError(f'当前无可执行工作，但根任务未关闭：{result.get("root_issue")}')
        repository = Path(result['repository']).resolve(strict=True)
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
        try:
            metadata.setdefault('cleanup_pids', []).extend(cleanup_workspace(run))
        except Exception as exc:
            metadata['cleanup_error'] = str(exc)
            if error is None:
                error = exc
                metadata.update(status='generation_failed', error=str(exc), failed_phase='cleanup')
        # Evidence failures stay separate from the generating process's original error.
        try:
            entries = archive_state(state, run) if state.exists() else []
            archive_sessions(run, native, work, entries, telemetry_env=env)
            shutil.copytree(work/'capabilities', run/'native-config')
        except Exception as exc:
            metadata['diagnostic_error'] = str(exc)
        if collector is not None:
            try:
                stop_local_telemetry(collector)
            except Exception as exc:
                metadata['telemetry_diagnostic_error'] = f'{type(exc).__name__}: {exc}'
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
