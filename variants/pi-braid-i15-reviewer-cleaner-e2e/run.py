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

from agent_support import (save, phase, hashes, digest, logged, cleanup_workspace, validate_application,
                           copy_application, deliver, browser_executable, budgeted_pi,
                           start_local_telemetry, telemetry_environment, stop_local_telemetry)
from agent_support import runtime_resource_environment, start_shared_proxy, stop_shared_proxy
from agent_support import model_bindings, bind_native_models, native_model_route, bind_native_role
from agent_support import bind_native_model_scope
from braid_runtime import (initialize_repository, read_runtime_result, load_delivery,
                           export_delivery, archive_state)
from core import archive_sessions, finalize_archive
from harness_layout import bind_layout
from standalone_model_gateway import start_model_gateway, stop_model_gateway

HERE = Path(__file__).resolve().parent
VARIANT = 'pi-braid-i15-reviewer-cleaner-e2e'
ROOT_PROFILE_ID = 'pi-glm-fast'
ROOT_CHECK_MESSAGES = (
    '请检查当前工作进展；没有新事实、决定或行动时结束处理，无需公开回执。',
    '请检查当前工作进展；仅在变化影响当前判断、下一步或交接时维护已有 task packet 与相关 Issue/PR 入口，无变化无需重复整理或公开回执。',
)
MAIN_SKILLS = ('svc-sub-agents', 'svc-task-packet','svc-documentation',
               'svc-verification', 'hyperformula', 'handsontable', 'better-auth-best-practices',
               'organization-best-practices', 'fixing-accessibility', 'ponytail', 'impeccable',
               'agent-browser', 'e2e', 'context7-docs', 'braid-collaboration', 'arc-bench')
REVIEWER_SKILLS = ('braid-collaboration', 'arc-bench', 'svc-verification', 'e2e',
                   'agent-browser', 'svc-sub-agents', 'context7-docs')
# Braid member conditions stay in the parent profile; native children receive their own role and task.
RUN_CONDITIONS = '''交付条件
本次为人工介入研究运行；用户可通过Issue/PR评论提出澄清、纠正或工作请求，按对象中的明确输入协作。依据原始需求处理常规歧义并记录重要假设，遇到不可自行解决的阻塞时保留证据。当前工作项或委派决定你的职责和可修改范围，下列环境约定不扩大它。
业务验收以本次run/input中的原始需求及允许参考附件为绝对权威，直接读取原文并引用路径、版本和条款；Issue摘录、PR说明、设计和自验不能降低标准。增量任务保留未取消的基线要求、已有功能和业务数据；歧义记录解释与证据，不从实现反推需求。
同一PR最多一个当前Braid reviewer责任与执行，不限制该reviewer委派的原生验收角色数量。请求审阅前冻结base/head；审阅期间实施者、root和reviewer不得推进任一引用，包括packet-only提交。先结束旧请求并确认旧审阅执行实际收口，再修复或建立下一候选和新请求；不同PR可并行。
代码和数据修改限于本次临时工作区；不得向其它外部系统或开发源码仓库push、发布或修改。可以查询公开库/API文档；不得读取、搜索或下载外部验收测试、benchmark实现、参考应用或先前实验结果。
JavaScript生态中的应用使用现代TypeScript，避免以JavaScript编写业务源码。按需求选择框架，使用所选框架的官方脚手架；SPA可优先评估Vite。选择并锁定兼容实际运行环境的依赖版本，不机械使用latest。

开发工具与反馈
开发时使用pnpm安装依赖、构建和运行脚本，提交pnpm-lock.yaml。预打包环境通过PATH提供pnpm、portless、e2e、agent-browser和Playwright；e2e使用独立冻结的工具依赖与浏览器，读取独立e2e技能取得本工作树接线。BROWSER_CHECK_NODE_MODULES和BROWSER_EXECUTABLE_PATH继续供已有Playwright/agent-browser入口使用。复用这些工具、浏览器和本次运行的包缓存。
应用检查使用Vitest，复杂组件按需使用Browser Mode；完整应用验收优先使用e2e的TypeScript测试，也可按需求使用Playwright自动化测试或脚本。检查失败保留首次结果、trace、控制台和请求错误，依据需求设计判据，不以通过数量代替覆盖说明。依赖安装失败保留原始错误与首轮日志，不通过反复安装掩盖失败。
新建应用的UI使用适合所选框架的成熟组件库和图标库，样式统一使用Tailwind CSS；接续既有应用时沿用基线技术栈，不为样式工具偏好迁移。按需求组合、定制已有控件，核对实际role、可访问名称、状态、键盘和焦点行为。统一少量视觉变量，图标随应用打包；动态样式采用所选Tailwind CSS版本可静态提取的完整类名映射或适当的CSS变量。
采用Tailwind CSS时，按所选版本的官方方式配置构建集成和CSS导入，确认应用入口实际加载该CSS。使用正式构建产物和正式启动路径，在实际页面核对代表性布局、颜色和字体的计算样式；不能仅凭构建成功声明样式生效。
在真实跨模块边界统一请求、响应与错误格式，按需要使用运行时schema校验；不为此增加代码生成系统。

数据与服务状态
持久化优先评估SQLite，写入通过事务完成；迁移和原需求指定的种子数据可重复执行，正常启动准备所需初始数据，重启不覆盖已有用户数据。核实数据库驱动与正式安装、启动环境的兼容性。前端优先使用同源相对API，开发代理转发后端；正式验收使用构建产物与正式启动路径。
开发、自检服务使用portless，为每个工作项和服务取唯一名称（例如portless issue-2-api pnpm run dev），应用遵守其注入的HOST/PORT，通过命令输出的URL访问。服务已由portless管理时，用agent-browser技能的with-service --check-only包裹检查，不重复启动。使用结束后停止自己的常驻服务；共享代理仍被其它成员使用时不停止它。
每次验收执行（包括原生子角色和同一PR内并行进程）分别使用独立数据库、缓存、上传目录、端口、浏览器会话和证据目录，从只读种子复制初始数据；不能只按PR分配一个共享验收目录。记录自己启动的进程与路径，完成后关闭自己的进程和会话，不污染候选、其它验收或交付应用的初始状态。'''


REVIEWER_ENVIRONMENT = '''验收环境
本次为人工介入研究运行；按Issue/PR中的明确输入及当前审阅责任协作，不扩大职责。允许查询公开库/API文档，不读取、搜索或下载隐藏验收测试、benchmark实现、参考应用或先前外部实验结果，不向外部系统或开发源码仓库push、发布或修改。
预打包PATH提供pnpm、portless、e2e、agent-browser和Playwright；BROWSER_CHECK_NODE_MODULES与BROWSER_EXECUTABLE_PATH供已有浏览器入口使用，复用本次工具和缓存。依赖或命令失败保留原始输出与真实退出值。
验收服务使用portless，每次执行和服务取唯一名称，通过命令实际输出的URL访问；服务已受管理时不重复启动，结束后停止自己的常驻服务，不停止别人仍使用的共享代理。'''


def native_files(work, runtime, skills, base_url, visual_url, route_bindings=None,
                 desired_model=None):
    """返回供 Braid 使用的 profiles/bindings，并写出 Pi 消费的原生材料。

    成员主模型归 profile，内部角色归原生 agents Markdown。
    本次运行只替换连接与路径；包内有哪些技能和会话启用哪些技能分别选择。
    """
    routes = route_bindings or model_bindings(base_url, visual_url, require_key=False)[0]
    background_bash = runtime/'node_modules/pi-background-bash/index.ts'
    fff = runtime/'node_modules/@ff-labs/pi-fff/src/index.ts'
    context7 = runtime/'node_modules/@upstash/context7-pi/extensions/context7.ts'
    exa = HERE/'extensions/exa.ts'
    cleaner = HERE/'extensions/factory-cleaner.ts'
    for extension in (background_bash, fff, context7, exa, cleaner):
        if not extension.is_file():
            raise FileNotFoundError(f'原生工具扩展缺失：{extension}')
    profiles, bindings = [], {}
    for source in sorted((HERE/'agents').iterdir()):
        if source.name == 'pi-glm-root' and desired_model != 'glm-5.3':
            continue
        profile = json.loads((source/'profile.json').read_text())
        folder = work/'capabilities'/profile['id']
        template = folder/'native-template'
        shutil.copytree(source, template)
        (template/'profile.json').unlink()
        (template/'instructions.md').unlink()
        is_reviewer = 'reviewer-only' in profile.get('tags', [])
        conditions = REVIEWER_ENVIRONMENT if is_reviewer else RUN_CONDITIONS
        profile.update(user_instructions=(source/'instructions.md').read_text().rstrip() +
                       '\n\n' + conditions + '\n',
                       workspace=str(work/'application'))
        providers = json.loads((template/'models.json').read_text())
        model = next(m for m in providers['providers'][profile['provider']]['models']
                     if m['id'] == profile['model'])
        profile['context_window_tokens'] = model['contextWindow']
        profile['provider'], profile['model'], profile_route = native_model_route(profile['provider'], profile['model'], routes)
        bind_native_models(providers, routes)
        save(template/'models.json', providers)
        settings_file = template/'settings.json'
        if settings_file.is_file():
            settings = json.loads(settings_file.read_text())
            bind_native_model_scope(settings, routes)
            save(settings_file, settings)
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
        cleaner_extension = folder/'factory-cleaner.ts'
        shutil.copy2(cleaner, cleaner_extension)
        cleaner_instructions = folder/'factory-cleaner.md'
        shutil.copy2(HERE/'extensions/factory-cleaner.md', cleaner_instructions)
        cleaner_shared = folder/'factory-cleaner-common.md'
        cleaner_shared.write_text('用中文记录面向成员的正文、讨论与维护结果。\n\n' + RUN_CONDITIONS + '\n')
        save(folder/'factory-cleaner.json', dict(provider='factory26', model='glm-5.3-flash',
            thinking_level='high', shared_requirements=str(cleaner_shared),
            instructions=str(cleaner_instructions),
            budget_module=str(Path(budgeted_pi.__code__.co_filename).resolve().with_name('model_budget.mjs'))))
        pi = budgeted_pi(runtime, work.parent)
        flags = [str(pi), '--no-extensions', '--no-skills', '--no-prompt-templates', '--no-themes',
                 '--extension', str(runtime/'node_modules/pi-subagents/index.ts'),
                 '--extension', str(background_bash),
                 '--extension', str(observer),
                 '--extension', str(cleaner_extension),
                 '--extension', str(fff), '--fff-mode', 'tools-only',
                 '--extension', str(context7), '--extension', str(exa)]
        for skill in REVIEWER_SKILLS if is_reviewer else MAIN_SKILLS:
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


def retained_fields_match(expected, stored):
    """Braid serializes optional defaults; every explicitly frozen field must match."""
    if isinstance(expected, dict):
        return isinstance(stored, dict) and all(
            key in stored and retained_fields_match(value, stored[key]) for key, value in expected.items())
    if isinstance(expected, list):
        return isinstance(stored, list) and len(expected) == len(stored) and all(
            retained_fields_match(left, right) for left, right in zip(expected, stored))
    return expected == stored


def resume_routing_change(args, run, gateway_routes, desired_model):
    """Accept explicitly authorized route changes, preserving all other aliases."""
    old_path = run/'routing-snapshot.json'
    old = json.loads(old_path.read_text())
    if args.resume_routing_change_receipt is None:
        if old['routes'] != gateway_routes:
            raise ValueError('恢复 gateway 配方已变化，缺少显式路由变更收据')
        return None
    receipt_path = args.resume_routing_change_receipt.resolve(strict=True)
    receipt_bytes = receipt_path.read_bytes()
    change = json.loads(receipt_bytes)
    catalog_path, routes_path = HERE/'support/model-gateway.json', HERE/'support/gateway-routes.json'
    from hackathon_gateway import prepare_catalog
    _, deployments = prepare_catalog(catalog_path, gateway_routes, aliases=sorted(gateway_routes))
    changed_aliases = change.get('changed_aliases', [change.get('changed_alias')])
    aliases_valid = (isinstance(changed_aliases, list) and bool(changed_aliases)
                     and all(isinstance(alias, str) for alias in changed_aliases)
                     and len(set(changed_aliases)) == len(changed_aliases)
                     and set(old['routes']) == set(gateway_routes)
                     and set(changed_aliases) == {
                         alias for alias in gateway_routes
                         if old['routes'].get(alias) != gateway_routes[alias]})
    if (change.get('run_id') != run.name or change.get('authorized_by') != 'user'
            or not isinstance(change.get('reason'), str) or not change['reason'].strip()
            or change.get('old_routing_snapshot_sha256') != hashlib.sha256(old_path.read_bytes()).hexdigest()
            or change.get('new_catalog_sha256') != hashlib.sha256(catalog_path.read_bytes()).hexdigest()
            or change.get('new_routes_sha256') != hashlib.sha256(routes_path.read_bytes()).hexdigest()
            or not aliases_valid
            or [v for v in old['deployments'] if v['alias'] not in changed_aliases]
               != [v for v in deployments if v['alias'] not in changed_aliases]):
        raise ValueError('路由变更收据、原冻结身份或未授权模型链不一致')
    return dict(change, receipt_source=str(receipt_path),
                receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
                old_routes=old['routes'], new_routes=gateway_routes, new_deployments=deployments)


def retained_resume(args, output, requirements, context_bytes, routes, gateway_routes, desired_model):
    """Validate a stopped retained run before any gateway or native process starts."""
    run = args.resume_run_dir.resolve(strict=True)
    if run.parent != output/'.factory26' or not run.is_dir():
        raise ValueError('恢复目录必须是本 output/.factory26 下的确切 run')
    if args.prepare_only or args.initial_application is not None:
        raise ValueError('同 run 恢复不能与 prepare-only/initial-application 混用')
    receipt_path = args.resume_stopped_receipt.resolve(strict=True)
    proof_bytes = receipt_path.read_bytes()
    proof = json.loads(proof_bytes)
    previous = json.loads((run/'run.json').read_text())
    stopped = proof.get('container_state', {})
    container = proof.get('container_id', '')
    if (proof.get('run_id') != run.name or proof.get('stopped') is not True
            or proof.get('owned_execution_stopped') is not True
            or len(container) != 64 or any(c not in '0123456789abcdef' for c in container)
            or stopped.get('Running') is not False or stopped.get('Pid') != 0
            or type(stopped.get('ExitCode')) is not int
            or not isinstance(proof.get('stopped_at'), (int, float))
            or proof['stopped_at'] < previous.get('recovery_started_at', previous['started_at'])):
        raise ValueError('停止收据须证明同 run 的旧 Docker/owned execution 已停止且时间晚于旧启动')
    proof_sha = hashlib.sha256(proof_bytes).hexdigest()
    for old in (run/'recovery').glob('*/resume-identity.json'):
        if json.loads(old.read_text()).get('stopped_receipt_sha256') == proof_sha:
            raise ValueError('此停止收据已经用于一次恢复；须先证明后续执行也已停止')
    if bool(args.evolution) != (run/'baseline-hashes.json').is_file():
        raise ValueError('恢复必须保留原 evolution 发布模式')
    if previous.get('variant') != VARIANT or previous.get('status') == 'generated':
        raise ValueError('恢复仅接受本 variant 尚未完成的保留运行')
    work, state, inputs = run/'work', run/'braid-state', run/'input'
    app, native, skills = work/'application', work/'home/.pi/agent', work/'skills'
    for path in (app, native, skills, state):
        if not path.is_dir():
            raise FileNotFoundError(f'恢复所需持久状态缺失：{path}')
    expected = json.loads((run/'input-hashes.json').read_text())
    if hashes(requirements) != expected or hashes(inputs) != expected:
        raise ValueError('官方需求输入或保留 input 已变化')
    context_path = run/'task-context.md'
    if context_path.exists() != (context_bytes is not None):
        raise ValueError('恢复不能增加或移除补充 task context')
    if context_bytes is not None:
        recorded = json.loads((run/'task-context.json').read_text())['sha256']
        if context_path.read_bytes() != context_bytes or hashlib.sha256(context_bytes).hexdigest() != recorded:
            raise ValueError('恢复 task context 与冻结材料不一致')
    request = json.loads((run/'braid-request.json').read_text())
    stored = json.loads((state/'request.json').read_text())
    root_id = 'pi-glm-root' if desired_model == 'glm-5.3' else ROOT_PROFILE_ID
    root = next(p for p in request['profiles'] if p['id'] == root_id)
    if (request['run_id'] != run.name or request['state'] != str(state)
            or request['root_profile_id'] != root_id or root['model'] != desired_model
            or previous['model'] != desired_model
            or request['prompt'] != (run/'prompt.txt').read_text()
            or not retained_fields_match(request['profiles'], stored['profiles'])
            or not retained_fields_match(request['bindings'], stored['bindings'])
            or any(request[k] != stored[k] for k in ('run_id','prompt','delivery_ref','root_profile_id'))
            or stored['repository'] != str(app.resolve())
            or previous.get('initial_application_commit') != stored['seed_commit']):
        raise ValueError('恢复请求、根成员、模型、原 seed commit 或 Braid 身份不一致')
    current_seed = subprocess.check_output(['git','-C',str(app),'rev-parse','HEAD'], text=True).strip()
    if current_seed != stored['seed_commit']:
        raise ValueError('保留输入仓库 HEAD 已改变，不能保持原 seed commit 接续')
    if json.loads((run/'model-connection.json').read_text())['bindings'] != routes:
        raise ValueError('恢复模型连接与冻结绑定不一致')
    routing_change = resume_routing_change(args, run, gateway_routes, desired_model) if gateway_routes is not None else None
    if args.resume_routing_change_receipt is not None and gateway_routes is None:
        raise ValueError('显式路由变更需要冻结 gateway 配方')
    if not Path(request['pi']['executable']).is_file() or Path(request['pi']['home']) != native:
        raise ValueError('恢复缺少原 budgeted Pi launcher 或原生 home 身份不一致')
    attempt = run/'recovery'/(time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8])
    attempt.mkdir(parents=True)
    # Preserve overwritten controls and derived evidence, not the large worktrees or live state.
    for path in run.iterdir():
        if path.is_file():
            shutil.copy2(path, attempt/path.name)
    for name in ('model-gateway', 'native', 'native-config', 'maintenance', 'application', 'application-artifact'):
        path = run/name
        if path.exists():
            shutil.move(str(path), attempt/name)
    for name in ('result.json','sessions.json'):
        path = state/name
        if path.is_file():
            (attempt/'braid-state').mkdir(exist_ok=True)
            shutil.copy2(path, attempt/'braid-state'/name)
    (attempt/'stopped-receipt.json').write_bytes(proof_bytes)
    metadata = dict(previous)
    for key in ('error','failed_phase','process_exit_code','braid','cleanup_errors','diagnostic_error',
                'maintenance_diagnostic_error','archive_error','generation_finished_at','generation_seconds'):
        metadata.pop(key, None)
    metadata.update(status='generating', run_id=run.name, recovery_attempt=attempt.name, recovery_started_at=time.time())
    if routing_change is not None:
        save(attempt/'routing-change.json', routing_change)
        metadata['routing_change'] = routing_change
    save(attempt/'resume-identity.json', {'run_id':run.name, 'original_started_at':previous['started_at'],
        'stopped_receipt_source':str(receipt_path), 'stopped_receipt_sha256':proof_sha,
        'source_container_id':container, 'seed_commit':stored['seed_commit'],
        'input_sha256':digest(expected), 'model':desired_model, 'root_profile_id':root_id,
        'evolution':bool(args.evolution), 'work_and_native_state_reused':True})
    return run, work, app, native, skills, inputs, state, request, metadata, attempt


def generate(args):
    """从选定集成分支的确切 commit 导出应用，分别记录运行与产物结果。

    prepare-only 只准备材料，不产生交付；进入生成后的失败保留工作现场。
    辅助归档异常单独记入 diagnostic_error，不能冒充外部评分或覆盖生成错误。
    """
    visual_url = os.environ.get('VISUAL_BASE_URL')
    provider_env = HERE/'.private/provider-env.json'
    gateway_enabled = provider_env.is_file()
    gateway_catalog = HERE/'support/model-gateway.json'
    gateway_routes_file = HERE/'support/gateway-routes.json'
    if gateway_enabled:
        if not gateway_routes_file.is_file():
            raise FileNotFoundError('私有模型包需要冻结的 support/gateway-routes.json')
        gateway_routes = json.loads(gateway_routes_file.read_text())
        root_model = os.environ.get('MODEL') or 'glm-5.3-flash'
        if root_model not in gateway_routes or 'deepseek-v4-flash-0731' not in gateway_routes:
            raise ValueError('冻结模型链不包含本轮根模型或DeepSeek0731')
        transport = {'provider': 'openai', 'base_url': 'http://127.0.0.1:4011/v1',
                     'credential_env': 'FACTORY26_GATEWAY_TOKEN'}
        routes = {'factory26': dict(transport, model=root_model), 'factory26-visual': dict(transport),
                  'factory26/deepseek-v4-flash': dict(transport, model_id='deepseek-v4-flash-0731')}
        model_env = dict(os.environ, FACTORY26_MODEL_BINDINGS=json.dumps(routes, separators=(',', ':')))
    else:
        routes, model_env = model_bindings(args.base_url, visual_url, require_key=not args.prepare_only)
    _, e2e_model, e2e_route = native_model_route('factory26', 'glm-5.3-flash', routes)
    base_url = routes['factory26']['base_url']
    requirements = args.requirements_dir.resolve(strict=True)
    if not requirements.is_dir():
        raise NotADirectoryError(f'输入不是目录：{requirements}')
    context_file = os.environ.get('TASK_CONTEXT_FILE')
    context_source = Path(context_file).resolve(strict=True) if context_file else None
    if context_source is not None and not context_source.is_file():
        raise ValueError(f'TASK_CONTEXT_FILE 必须指向可读文件：{context_source}')
    context_bytes = context_source.read_bytes() if context_source is not None else None
    runtime = args.runtime.resolve(strict=True)
    e2e_runtime = (args.e2e_runtime or runtime/'e2e').resolve(strict=True)
    if not (e2e_runtime/'node_modules/e2e/dist/cli/bin.js').is_file():
        raise FileNotFoundError(f'e2e addon 缺失：{e2e_runtime}')
    pbb = runtime/'node_modules/pi-background-bash/bin/pbb.js'
    pil = runtime/'node_modules/pi-lane/bin/pil.js'
    if not pbb.is_file() or not pil.is_file():
        raise FileNotFoundError(f'后台任务 CLI 缺失：{pbb} 或 {pil}')
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source_braid = (args.braid or runtime/'bin/braid').resolve(strict=True)
    desired_model = os.environ.get('MODEL') or routes['factory26'].get('model')
    resuming = args.resume_run_dir is not None
    if resuming:
        run, work, app, native, skills, inputs, state, request, metadata, attempt = retained_resume(
            args, output, requirements, context_bytes, routes,
            gateway_routes if gateway_enabled else None, desired_model)
        bind_layout(run, variant=VARIANT, definition_root=HERE, runtime=runtime,
                    skills_root=args.skills_root.resolve(strict=True), braid=source_braid,
                    extra_definitions={'e2e-runtime': e2e_runtime})
        save(attempt/'runtime-identity.json', {'braid':str(source_braid),
            'braid_sha256':hashlib.sha256(source_braid.read_bytes()).hexdigest(),
            'run_py_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'runtime':str(runtime), 'e2e_runtime':str(e2e_runtime)})
    else:
        baseline_hashes = hashes(args.initial_application.resolve(strict=True)) if args.evolution else None
        run = output/'.factory26'/(time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8])
        run.mkdir(parents=True,exist_ok=True)
        work = run/'work'; work.mkdir()
        skills_root = args.skills_root.resolve(strict=True)
        bind_layout(run, variant=VARIANT, definition_root=HERE, runtime=runtime,
                    skills_root=skills_root, braid=source_braid,
                    extra_definitions={'e2e-runtime': e2e_runtime},
                    derived_inputs=['input', 'work/capabilities', 'work/bin', 'work/skills',
                                    'braid-request.json', 'config.json', 'model-connection.json', 'prompt.txt'])
        app = work/'application'
        # The frozen previous-stage application is an input, separate from publication.
        if args.initial_application is not None:
            if args.evolution:
                # The injected output may also be the source. Never traverse the new run or old sessions.
                source = args.initial_application.resolve(strict=True)
                historical = {'.factory26', 'process-evidence', '.factory-e2e', '.arc'}
                def omitted(folder, names):
                    excluded = {'.git', '.braid', 'node_modules', '__pycache__'}
                    if Path(folder) == source:
                        excluded |= historical
                    return excluded.intersection(names)
                shutil.copytree(source, app, ignore=omitted)
                save(run/'baseline-hashes.json', baseline_hashes)
            else:
                copy_application(args.initial_application.resolve(strict=True), app)
        else:
            app.mkdir()
        native = work/'home/.pi/agent'; native.mkdir(parents=True)
        (work/'tmp').mkdir()
        (work/'bin').mkdir()
        shutil.copy2(HERE/'tools/e2e-cli', work/'bin/e2e')
        (work/'bin/e2e').chmod(0o755)
        pbb_launcher = work/'bin/pbb'
        pbb_launcher.write_text('#!/bin/sh\nexec ' + shlex.join((str(runtime/'bin/node'), str(pbb))) + ' "$@"\n')
        pbb_launcher.chmod(0o755)
        skills = work/'skills'; skills.mkdir()
        skill_sources = {}
        for name in MAIN_SKILLS:
            source = (runtime/'node_modules/@upstash/context7-pi/skills/context7-docs'
                      if name == 'context7-docs' else skills_root/name).resolve(strict=True)
            declared_root = runtime if name == 'context7-docs' else skills_root
            if not source.is_relative_to(declared_root):
                raise ValueError(f'技能链接超出已冻结定义：{source}')
            if not (source/'SKILL.md').is_file():
                raise FileNotFoundError(f'冻结技能入口缺失：{source}')
            (skills/name).symlink_to(source, target_is_directory=True)
            skill_sources[name] = str(source)
        inputs = run/'input'; shutil.copytree(requirements, inputs)
        desired_model = os.environ.get('MODEL') or routes['factory26'].get('model')
        profiles, bindings = native_files(work, runtime, skills, base_url, visual_url, routes, desired_model)
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
        save(run/'materials.json', {'agents':hashes(HERE/'agents'), 'skills':{name+'/'+relative: sha256 for name, source in skill_sources.items()
                                             for relative, sha256 in hashes(Path(source)).items()},
                                   'skill_sources':skill_sources, 'harness_layout':str(run/'harness-layout.json'),
                                   'runtime':str(runtime), 'braid':str(source_braid),
                                   'e2e_runtime':str(e2e_runtime),
                                   'e2e_addon':json.loads((e2e_runtime/'addon-source.json').read_text())})
        prompt = f'''本次任务来自 ARC Bench，需求来源是 {inputs} 中的完整允许需求包，最终交付是满足需求的 Web 应用。
处理本次需求、设计、实现和交付时，读取独立技能 arc-bench：{skills/'arc-bench/SKILL.md'}，按当前问题读取其适用reference。
JavaScript生态中的应用使用现代TypeScript，避免以JavaScript编写业务源码。
最终交付时用中文说明结果。'''
        if context_source is not None:
            context_target = run/'task-context.md'
            context_target.write_bytes(context_bytes)
            save(run/'task-context.json', {'source':str(context_source), 'path':str(context_target),
                                         'sha256':hashlib.sha256(context_bytes).hexdigest()})
            prompt += f'\n本次运行的补充任务约定由设施提供，读取独立文件 {context_target}，与完整需求包一起用于工作组织与交付。\n'
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
    temporary = tempfile.mkdtemp(prefix='f26-', dir=work/'tmp')
    temporary_alias = None
    temporary_alias_dir = None
    workspace_cleanup_complete = False
    collector_stopped = False
    daemon_stop_complete = False
    env = dict(model_env, **tool_environment(), PORTLESS_PORT='1355', PORTLESS_HTTPS='0',
               PI_FFF_MODE='tools-only', PI_FFF_MULTIGREP='0',
               PORTLESS_SYNC_HOSTS='0', PORTLESS_STATE_DIR=str(work/'tmp/portless'),
               npm_config_cache=str(work/'cache/npm'),
               npm_config_store_dir=str(work/'cache/pnpm'),
               HOME=str(work/'home'), TMPDIR=temporary,
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
               MCPORTER_DAEMON_DIR=str(Path(temporary)/'m'),
               E2E_RUNTIME=str(e2e_runtime),
               E2E_NODE_MODULES=str(e2e_runtime/'node_modules'),
               E2E_CONFIG_TEMPLATE=str(HERE/'tools/e2e.config.ts'),
               E2E_MODEL=e2e_model, E2E_BASE_URL=e2e_route['base_url'],
               E2E_API_KEY=model_env.get(e2e_route['credential_env'], ''),
               E2E_TELEMETRY_DISABLED='1',
               FACTORY26_TOOL_NODE=str(runtime/'bin/node'),
               FACTORY26_BASE_URL=base_url,
               PATH=os.pathsep.join((str(work/'bin'), str(runtime/'bin'),
                                     str(runtime/'node_modules/.bin'), os.environ.get('PATH',''))))
    collector = None
    begin = time.monotonic()
    error = None
    history = {'status': 'not_started'}
    history_stop = threading.Event()
    history_tool = HERE/'arc-runtime.pyz'
    if not history_tool.is_file():
        history_tool = HERE.parents[1]/'lab/arc_bench/agent_runtime/__main__.py'

    origin = state/'origin.git'

    def cleanup_temporary_alias():
        """Remove only the Linux short-path alias after owned processes are stopped."""
        if temporary_alias is None:
            metadata.setdefault('temporary_paths', {})['cleanup'] = 'not-applicable'
            return
        paths = metadata.setdefault('temporary_paths', {})
        if not workspace_cleanup_complete or not collector_stopped or not daemon_stop_complete:
            paths.update(cleanup='retained', cleanup_reason={
                'workspace_cleanup_complete': workspace_cleanup_complete,
                'collector_stopped': collector_stopped,
                'daemon_stop_complete': daemon_stop_complete,
                'reason': 'process stop could not be proven',
            })
            return
        try:
            temporary_alias.unlink(missing_ok=True)
            temporary_alias_dir.rmdir()
        except OSError as exc:
            paths.update(cleanup='retained', cleanup_reason={
                'type': type(exc).__name__, 'message': str(exc),
            })
            return
        paths.update(cleanup='removed', cleanup_reason=None)

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
    model_gateway = None
    try:
        # Linux Chromium derives its SingletonSocket path from TMPDIR and has no
        # separate browser-temp option. Keep the durable entity under run/work
        # and expose only a short-lived /tmp symlink to child processes.
        if sys.platform.startswith('linux'):
            temporary_alias_dir = Path('/tmp') / f'f26-{uuid.uuid4().hex[:8]}'
            temporary_alias_dir.mkdir(mode=0o700)
            temporary_alias = temporary_alias_dir/'t'
            temporary_alias.symlink_to(temporary, target_is_directory=True)
            env['TMPDIR'] = str(temporary_alias)
            env['MCPORTER_DAEMON_DIR'] = str(temporary_alias/'m')
            metadata['temporary_paths'] = {
                'platform': sys.platform,
                'entity': str(Path(temporary)),
                'alias': str(temporary_alias),
                'alias_target': str(Path(temporary)),
                'cleanup': 'pending',
                'daemon_stop': 'pending',
            }
        else:
            metadata['temporary_paths'] = {
                'platform': sys.platform,
                'entity': str(Path(temporary)),
                'alias': None,
                'cleanup': 'not-applicable',
                'daemon_stop': 'not-applicable',
            }
        phase(run/'run.json', metadata, 'prepared')
        # The existing collector owns resource sampling before gateway/browser startup.
        collector, binding = start_local_telemetry(run)
        collector_stopped = collector is None
        env.update(telemetry_environment(binding))
        env.update(runtime_resource_environment(runtime, run))
        if gateway_enabled:
            from hackathon_gateway import prepare_catalog
            config, snapshot = prepare_catalog(gateway_catalog, gateway_routes, aliases=sorted(gateway_routes))
            expected_snapshot = snapshot
            if resuming:
                expected_snapshot = (metadata['routing_change']['new_deployments']
                    if args.resume_routing_change_receipt is not None
                    else json.loads((run/'routing-snapshot.json').read_text())['deployments'])
            if snapshot != expected_snapshot:
                raise ValueError('恢复 gateway deployment/wire 定义与冻结快照不一致')
            gateway_config = run/'gateway-config.json'
            save(gateway_config, config)
            save(run/'routing-snapshot.json', {'routes': gateway_routes, 'deployments': snapshot})
            if provider_env.parent.stat().st_mode & 0o777 != 0o700:
                provider_env.parent.chmod(0o700)
            if provider_env.stat().st_mode & 0o777 != 0o600:
                provider_env.chmod(0o600)
            model_gateway = start_model_gateway(runtime, run, env, gateway_config,
                bindings=routes, provider_env=provider_env, preserve_parameters=True,
                gateway_routes=gateway_routes)
            env = model_gateway['pi_environment']
            for name in ('OPENAI_API_KEY', 'FACTORY26_API_KEY', 'VISUAL_API_KEY', 'FACTORY26_VISUAL_API_KEY'):
                env.pop(name, None)
            env.update(E2E_API_KEY=env['FACTORY26_GATEWAY_TOKEN'], E2E_BASE_URL=model_gateway['endpoint'],
                       FACTORY26_BASE_URL=model_gateway['endpoint'])
        if not resuming:
            initialize_repository(app)
        if not resuming and args.initial_application is not None:
            subprocess.run(['git', '-C', str(app), 'add', '-A'], check=True)
            subprocess.run(['git', '-C', str(app), 'commit', '-qm',
                            '冻结上一阶段应用作为本阶段起点'], check=True)
            metadata['initial_application_commit'] = subprocess.check_output(
                ['git', '-C', str(app), 'rev-parse', 'HEAD'], text=True).strip()
        shared_proxy = start_shared_proxy(runtime, run, env)
        phase(run/'run.json', metadata, 'braid', 'braid.log')
        history_thread = threading.Thread(target=watch_history, name='arc-history', daemon=True)
        history_thread.start()
        try:
            command = [str(source_braid), 'local', str(run/'braid-request.json')]
            if resuming:
                command.append('--offline-resume')
            code = logged(command,
                          app, env, run/'braid.log', metadata.setdefault('cleanup_errors', []))
        finally:
            history_stop.set()
            history_thread.join()
            try:
                stopped = subprocess.run([str(runtime/'bin/mcporter'), 'daemon', 'stop'],
                                         env=env, capture_output=True, text=True, timeout=45)
                save(run/'e2e-daemon-cleanup.json', {'exit_code':stopped.returncode,
                     'stdout':stopped.stdout, 'stderr':stopped.stderr})
                if stopped.returncode:
                    metadata['e2e_daemon_cleanup_error'] = stopped.stderr or stopped.stdout
                    metadata.setdefault('temporary_paths', {})['daemon_stop'] = 'failed'
                else:
                    daemon_stop_complete = True
                    metadata.setdefault('temporary_paths', {})['daemon_stop'] = 'stopped'
            except Exception as exc:
                metadata['e2e_daemon_cleanup_error'] = str(exc)
                metadata.setdefault('temporary_paths', {})['daemon_stop'] = 'error'
        metadata['process_exit_code'] = code
        metadata['braid'] = read_runtime_result(state)
        metadata['cleanup_pids'] = cleanup_workspace(run)
        workspace_cleanup_complete = True
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
        if args.evolution:
            # Publish only application members; retain injected historical evidence in output.
            validate_application(run/'application')
            for entry in (run/'application').iterdir():
                if entry.name in {'.factory26', 'process-evidence', '.factory-e2e', '.arc', '.git'}:
                    continue
                target = output/entry.name
                if entry.is_dir():
                    shutil.copytree(entry, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(entry, target)
        else:
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
        if model_gateway is not None:
            try:
                stop_model_gateway(model_gateway, run)
            except Exception as exc:
                metadata['model_gateway_cleanup_error'] = str(exc)
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
            workspace_cleanup_complete = True
        except Exception as exc:
            metadata['cleanup_error'] = str(exc)
            workspace_cleanup_complete = False
            if error is None:
                error = exc
                metadata.update(status='generation_failed', error=str(exc), failed_phase='cleanup')
        # Evidence failures stay separate from the generating process's original error.
        try:
            for maintenance in sorted((work/'native-homes').glob('*/.factory/maintenance')):
                shutil.copytree(maintenance, run/'maintenance'/maintenance.parents[1].name)
        except Exception as exc:
            metadata['maintenance_diagnostic_error'] = str(exc)
        try:
            entries = archive_state(state, run) if state.exists() else []
            archive_sessions(run, native, work, entries, telemetry_env=env)
            shutil.copytree(work/'capabilities', run/'native-config')
        except Exception as exc:
            metadata['diagnostic_error'] = str(exc)
        if collector is not None:
            try:
                stop_local_telemetry(collector)
                collector_stopped = True
            except Exception as exc:
                metadata['telemetry_diagnostic_error'] = f'{type(exc).__name__}: {exc}'
        cleanup_temporary_alias()
        if resuming:
            metadata['recovery_generation_seconds'] = time.monotonic()-begin
        metadata.update(generation_seconds=time.monotonic()-begin, generation_finished_at=time.time())
        phase(run/'run.json', metadata, 'frozen' if metadata['status']=='generated' else 'failed', 'braid.log')
    recovery_required = (error is not None or metadata.get('process_exit_code') != 0 or
                         metadata.get('braid', {}).get('status') != 'quiescent' or
                         history.get('status') != 'completed' or
                         bool(metadata.get('maintenance_diagnostic_error')))
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
    parser.add_argument('--resume-run-dir', type=Path, help='复用确切 output/.factory26/run 的持久状态')
    parser.add_argument('--resume-stopped-receipt', type=Path, help='宿主核实旧 Docker 与 owned execution 已停止的 JSON 收据')
    parser.add_argument('--resume-routing-change-receipt', type=Path, help='用户授权的同 run 路由变更收据；未列明模型链保持冻结身份')
    parser.add_argument('--initial-application', type=Path, help='上一阶段冻结应用；只读输入，与最终输出分离')
    parser.add_argument('--evolution', action='store_true', help='增量演化：隔离旧运行证据并保留已注入输出')
    parser.add_argument('--type', choices=['web'], default='web')
    parser.add_argument('--runtime', type=Path, default=HERE/'runtime')
    parser.add_argument('--e2e-runtime', type=Path, help='独立冻结的 e2e addon，默认 runtime/e2e')
    parser.add_argument('--braid', type=Path)
    parser.add_argument('--skills-root', type=Path, default=HERE/'skills')
    parser.add_argument('--base-url')
    parser.add_argument('--prepare-only', action='store_true', help='写出真实原生材料和 Braid 请求，不调用模型')
    args = parser.parse_args()
    if (args.resume_run_dir is None) != (args.resume_stopped_receipt is None):
        parser.error('resume-run-dir 与 resume-stopped-receipt 必须同时提供')
    if args.resume_routing_change_receipt is not None and args.resume_run_dir is None:
        parser.error('路由变更收据只能用于同 run 恢复')
    if args.evolution and args.initial_application is None and args.resume_run_dir is None:
        args.initial_application = args.output_dir
    def interrupted(signum, frame):
        raise KeyboardInterrupt('运行终止信号')
    signal.signal(signal.SIGTERM, interrupted)
    generate(args)
