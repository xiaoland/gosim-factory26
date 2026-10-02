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
from agent_support import runtime_resource_environment, start_shared_proxy, stop_shared_proxy
from agent_support import model_bindings, bind_native_models, native_model_route, bind_native_role
from braid_runtime import (initialize_repository, read_runtime_result, load_delivery,
                           export_delivery, archive_state)
from core import archive_sessions, finalize_archive

HERE = Path(__file__).resolve().parent
VARIANT = 'pi-braid-i14-reviewer'
ROOT_PROFILE_ID = 'pi-glm-fast'
ROOT_CHECK_MESSAGES = (
    '请检查当前工作进展；没有新事实、决定或行动时结束处理，无需公开回执。',
    '请检查当前工作进展；仅在变化影响当前判断、下一步或交接时维护已有 task packet 与相关 Issue/PR 入口，无变化无需重复整理或公开回执。',
)
MAIN_SKILLS = ('svc-sub-agents', 'svc-task-packet','svc-documentation',
               'svc-verification', 'hyperformula', 'handsontable', 'better-auth-best-practices',
               'organization-best-practices', 'fixing-accessibility', 'ponytail', 'impeccable',
               'agent-browser', 'context7-docs', 'braid-collaboration', 'arc-bench')
# Braid member conditions stay in the parent profile; native children receive their own role and task.
RUN_CONDITIONS = '''交付条件
本次为人工介入研究运行；用户可通过Issue/PR评论提出澄清、纠正或工作请求，按对象中的明确输入协作。依据原始需求处理常规歧义并记录重要假设，遇到不可自行解决的阻塞时保留证据。当前工作项或委派决定你的职责和可修改范围，下列环境约定不扩大它。
代码和数据修改限于本次临时工作区；不得向其它外部系统或开发源码仓库push、发布或修改。可以查询公开库/API文档；不得读取、搜索或下载外部验收测试、benchmark实现、参考应用或先前实验结果。
JavaScript生态中的应用使用现代TypeScript，避免以JavaScript编写业务源码。按需求选择框架，使用所选框架的官方脚手架；SPA可优先评估Vite。选择并锁定兼容实际运行环境的依赖版本，不机械使用latest。

开发工具与反馈
开发时使用pnpm安装依赖、构建和运行脚本，提交pnpm-lock.yaml。预打包环境通过PATH提供pnpm、portless、agent-browser和Playwright；BROWSER_CHECK_NODE_MODULES指向已有Node工具依赖，BROWSER_EXECUTABLE_PATH指向配套浏览器入口。复用这些工具、浏览器和本次运行的包缓存。
应用检查使用Vitest，复杂组件按需使用Browser Mode；完整应用验收使用Playwright自动化测试或脚本。检查失败保留首次结果、trace、控制台和请求错误，依据需求设计判据，不以通过数量代替覆盖说明。依赖安装失败保留原始错误与首轮日志，不通过反复安装掩盖失败。
UI使用适合所选框架的成熟组件库和图标库，样式使用UnoCSS；按需求组合、定制已有控件，核对实际role、可访问名称、状态、键盘和焦点行为。统一少量视觉变量，图标随应用打包；动态样式采用可静态提取的类名映射、safelist或适当的CSS变量。
在真实跨模块边界统一请求、响应与错误格式，按需要使用运行时schema校验；不为此增加代码生成系统。

数据与服务状态
持久化优先评估SQLite，写入通过事务完成；迁移和原需求指定的种子数据可重复执行，正常启动准备所需初始数据，重启不覆盖已有用户数据。核实数据库驱动与正式安装、启动环境的兼容性。前端优先使用同源相对API，开发代理转发后端；正式验收使用构建产物与正式启动路径。
开发、自检服务使用portless，为每个工作项和服务取唯一名称（例如portless issue-2-api pnpm run dev），应用遵守其注入的HOST/PORT，通过命令输出的URL访问。服务已由portless管理时，用agent-browser技能的with-service --check-only包裹检查，不重复启动。使用结束后停止自己的常驻服务；共享代理仍被其它成员使用时不停止它。
自检数据库、缓存、上传文件和浏览器状态使用临时位置，不改变交付应用的初始状态。'''


def native_files(work, runtime, skills, base_url, visual_url):
    """返回供 Braid 使用的 profiles/bindings，并写出 Pi 消费的原生材料。

    成员主模型归 profile，内部角色归原生 agents Markdown。
    本次运行只替换连接与路径；包内有哪些技能和会话启用哪些技能分别选择。
    """
    routes, _ = model_bindings(base_url, visual_url, require_key=False)
    background_bash = runtime/'node_modules/pi-background-bash/index.ts'
    fff = runtime/'node_modules/@ff-labs/pi-fff/src/index.ts'
    context7 = runtime/'node_modules/@upstash/context7-pi/extensions/context7.ts'
    exa = HERE/'extensions/exa.ts'
    for extension in (background_bash, fff, context7, exa):
        if not extension.is_file():
            raise FileNotFoundError(f'原生工具扩展缺失：{extension}')
    profiles, bindings = [], {}
    for source in sorted((HERE/'agents').iterdir()):
        profile = json.loads((source/'profile.json').read_text())
        folder = work/'capabilities'/profile['id']
        template = folder/'native-template'
        shutil.copytree(source, template)
        (template/'profile.json').unlink()
        (template/'instructions.md').unlink()
        profile.update(user_instructions=(source/'instructions.md').read_text().rstrip() +
                       '\n\n' + RUN_CONDITIONS + '\n',
                       workspace=str(work/'application'))
        providers = json.loads((template/'models.json').read_text())
        model = next(m for m in providers['providers'][profile['provider']]['models']
                     if m['id'] == profile['model'])
        profile['context_window_tokens'] = model['contextWindow']
        profile['provider'], profile['model'], profile_route = native_model_route(profile['provider'], profile['model'], routes)
        bind_native_models(providers, routes)
        save(template/'models.json', providers)
        save(template/'pi-fff.json', {'mode':'tools-only'})
        for role in (template/'agents').glob('*.md'):
            instruction = bind_native_role(role.read_text(), routes).replace('@SKILLS@', json.dumps(str(skills))[1:-1])
            marker = 'extensions: ""'
            if marker not in instruction:
                raise ValueError(f'内部角色扩展配置已变化：{role}')
            extensions = [background_bash, fff]
            if role.stem in {'explorer', 'executor'}:
                extensions += [context7, exa]
                instruction = instruction.replace('skills: "', 'skills: "context7-docs, ', 1)
            instruction = instruction.replace(marker, 'extensions: '+json.dumps(', '.join(map(str,extensions))), 1)
            role.write_text(instruction)
        observer = folder/'factory-subagent-observer.ts'
        shutil.copy2(HERE/'extensions/factory-subagent-observer.ts', observer)
        pi = budgeted_pi(runtime, work.parent)
        flags = [str(pi), '--no-extensions', '--no-skills', '--no-prompt-templates', '--no-themes',
                 '--extension', str(runtime/'node_modules/pi-subagents/index.ts'),
                 '--extension', str(background_bash),
                 '--extension', str(observer),
                 '--extension', str(fff), '--fff-mode', 'tools-only',
                 '--extension', str(context7), '--extension', str(exa)]
        for skill in MAIN_SKILLS:
            flags += ['--skill', str(skills/skill/'SKILL.md')]
        launcher = folder/'pi'
        launcher.write_text('#!/bin/sh\nexec '+shlex.join(flags)+' "$@"\n')
        launcher.chmod(0o755)
        bindings[profile['id']] = dict(adapter_type='pi', executable=str(launcher),
            api_key_environment=profile_route['credential_env'], native_template=str(template),
            native_home={'root':str(work/'native-homes')})
        profiles.append(profile)
    return profiles, bindings


def tool_environment():
    """Package-local credentials are defaults; explicit run environment wins."""
    names = ('CONTEXT7_API_KEY', 'EXA_API_KEY')
    private = HERE/'.private/tool-env.json'
    values = json.loads(private.read_text()) if private.is_file() else {}
    if not isinstance(values, dict) or (private.is_file() and set(values) != set(names)) or any(
            not isinstance(value, str) or not value for value in values.values()):
        raise ValueError('包内工具凭据配置需要已知变量的非空字符串值')
    return {name:os.environ.get(name, values.get(name)) for name in names
            if name in os.environ or name in values}


def generate(args):
    """从选定集成分支的确切 commit 导出应用，分别记录运行与产物结果。

    prepare-only 只准备材料，不产生交付；进入生成后的失败保留工作现场。
    辅助归档异常单独记入 diagnostic_error，不能冒充外部评分或覆盖生成错误。
    """
    visual_url = os.environ.get('VISUAL_BASE_URL')
    routes, model_env = model_bindings(args.base_url, visual_url, require_key=not args.prepare_only)
    base_url = routes['factory26']['base_url']
    requirements = args.requirements_dir.resolve(strict=True)
    if not requirements.is_dir():
        raise NotADirectoryError(f'输入不是目录：{requirements}')
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
        source = (runtime/'node_modules/@upstash/context7-pi/skills/context7-docs'
                  if name == 'context7-docs' else args.skills_root.resolve(strict=True)/name)
        copy_skill(source, skills/name)
    source_braid = (args.braid or runtime/'bin/braid').resolve(strict=True)
    shutil.copy2(source_braid, work/'bin/braid')
    (work/'bin/braid').chmod(0o755)
    inputs = run/'input'; shutil.copytree(requirements, inputs)
    profiles, bindings = native_files(work, runtime, skills, base_url, visual_url)
    desired_model = os.environ.get('MODEL') or routes['factory26'].get('model')
    root_profile_id = 'pi-glm-root' if desired_model == 'glm-5.3' else ROOT_PROFILE_ID
    root_profile = next(p for p in profiles if p['id']==root_profile_id)
    if desired_model and desired_model != root_profile['model']:
        raise ValueError('平台主模型与此 variant 不一致')
    if visual_url and os.environ.get('VISUAL_MODEL') != 'glm-5.3-flash':
        raise ValueError('平台视觉模型与此 variant 不一致')
    config = dict(variant=VARIANT, backend='pi', workflow='braid', svc=True,
                  task='platform', model=root_profile['model'], thinking=root_profile['reasoning'],
                  deployment='arcbench', benchmark_revision=None)
    save(run/'config.json', config)
    save(run/'model-connection.json', {'bindings': routes, 'credential_values_recorded': False})
    save(run/'input-hashes.json', hashes(inputs))
    code_files = [*HERE.glob('*.py'), *(HERE/'agents').rglob('*'), *(HERE/'extensions').rglob('*'),
                  *(HERE/'tools').rglob('*')]
    save(run/'implementation-hashes.json', {str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in code_files if p.is_file()})
    save(run/'materials.json', {'agents':hashes(HERE/'agents'), 'skills':hashes(skills),
                               'runtime':str(runtime), 'braid':str(source_braid)})
    prompt = f'''本次任务来自 ARC Bench，需求来源是 {inputs} 中的完整允许需求包，最终交付是满足需求的 Web 应用。
处理本次需求、设计、实现和交付时，读取独立技能 arc-bench：{skills/'arc-bench/SKILL.md'}，按当前问题读取其适用reference。
JavaScript生态中的应用使用现代TypeScript，避免以JavaScript编写业务源码。
最终交付时用中文说明结果。'''
    (run/'prompt.txt').write_text(prompt)
    state = run/'braid-state'
    pi = budgeted_pi(runtime, work.parent)
    request = dict(profiles=profiles, root_profile_id=root_profile_id, bindings=bindings,
                   root_check_messages=ROOT_CHECK_MESSAGES,
                   prompt=prompt, state=str(state), run_id=run.name,
                   delivery_ref='refs/heads/main', codex=None,
                   pi=dict(executable=str(pi), home=str(native), api_key_environment=bindings[root_profile_id]['api_key_environment']))
    save(run/'braid-request.json', request)
    metadata = dict(config, started_at=time.time(), status='prepared' if args.prepare_only else 'generating')
    phase(run/'run.json', metadata, 'prepared')
    print(run, flush=True)
    if args.prepare_only:
        return run
    browser = str(browser_executable(runtime))
    # Chromium sockets require a short path; retain Pi's durable async state separately.
    env = dict(model_env, **tool_environment(), PORTLESS_PORT='1355', PORTLESS_HTTPS='0',
               PI_FFF_MODE='tools-only', PI_FFF_MULTIGREP='0',
               PORTLESS_SYNC_HOSTS='0', PORTLESS_STATE_DIR=str(work/'tmp/portless'),
               npm_config_cache=str(work/'cache/npm'),
               npm_config_store_dir=str(work/'cache/pnpm'),
               HOME=str(work/'home'), TMPDIR=tempfile.mkdtemp(prefix='f26-', dir='/tmp'),
               PI_SUBAGENTS_TEMP_ROOT=str(work/'tmp'/f'pi-subagents-uid-{os.getuid()}'),
               PI_SUBAGENT_MAX_DEPTH='3',
               XDG_CONFIG_HOME=str(work/'home/.config'), PI_CODING_AGENT_DIR=str(native),
               PI_TELEMETRY='0', PI_OFFLINE='1',
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
    env['MCPORTER_DAEMON_DIR'] = str(Path(env['TMPDIR'])/'mcporter')
    collector = None
    env.update(runtime_resource_environment(runtime, run))
    try:
        collector, binding = start_local_telemetry(run)
        env.update(telemetry_environment(binding))
    except Exception as exc:
        if os.environ.get('FACTORY26_EXP_TELEMETRY_BINDING'):
            raise
        metadata['telemetry_diagnostic_error'] = f'{type(exc).__name__}: {exc}'
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

    shared_proxy = None
    try:
        initialize_repository(app)
        shared_proxy = start_shared_proxy(runtime, run, env)
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
        from braid_runtime import publish_application
        publish_application(repository, delivery['delivery_commit'], run/'application-artifact', inputs,
                            {'attempt_id': os.environ.get('FACTORY26_EXP_ATTEMPT_ID', run.name), 'braid_run_id': run.name})
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
        if shared_proxy is not None:
            try:
                stop_shared_proxy(shared_proxy, run)
            except Exception as exc:
                metadata['shared_proxy_cleanup_error'] = str(exc)
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
    recovery_required = (error is not None or metadata.get('process_exit_code') != 0 or
                         metadata.get('braid', {}).get('status') != 'quiescent' or
                         history.get('status') != 'completed')
    if recovery_required:
        save(run/'recovery-workspace.json', {'path':str(work), 'request':str(run/'braid-request.json')})
    try:
        receipt = finalize_archive(run, reclaim_workspace=not recovery_required)
        if receipt['reclaim_state']['status'] == 'eligible':
            shutil.rmtree(work)
        elif work.exists() and not recovery_required:
            save(run/'recovery-workspace.json', {
                'path':str(work), 'request':str(run/'braid-request.json'),
                'reason':'archive receipt did not authorize workspace reclamation'})
            finalize_archive(run, reclaim_workspace=False)
    except Exception as exc:
        metadata['archive_error'] = f'{type(exc).__name__}: {exc}'
        save(run/'recovery-workspace.json', {
            'path':str(work), 'request':str(run/'braid-request.json'),
            'reason':'archive finalization failed', 'error':metadata['archive_error']})
        phase(run/'run.json', metadata, 'frozen' if metadata['status']=='generated' else 'failed', 'braid.log')
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
