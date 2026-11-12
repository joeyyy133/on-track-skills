#!/usr/bin/env python3
"""Local, non-executing project ledger checks. Does not run commands from records."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = re.compile(r'V(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z')
REVISION = re.compile(r'REQ-[0-9]{3,}\Z')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Fixed coverage boundary, printed with every fingerprint.
EXCLUDED = {'.git', '.ontrack', 'node_modules', '.venv', '__pycache__', 'dist', 'build', 'coverage'}
def source_digest(root):
    h = hashlib.sha256()
    def fail(error):
        raise error
    for base, dirs, files in os.walk(root, followlinks=False, onerror=fail):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED)
        # Include symlink directory identities without traversing their targets.
        links = [d for d in dirs if (Path(base) / d).is_symlink()]
        dirs[:] = [d for d in dirs if d not in links]
        for name in sorted(files + links):
            if name in EXCLUDED:
                continue
            p = Path(base) / name
            label = p.relative_to(root).as_posix().encode()
            mode = p.lstat().st_mode
            data = os.readlink(p).encode() if p.is_symlink() else p.read_bytes()
            for piece in (label, str(mode).encode(), data):
                h.update(len(piece).to_bytes(8, 'big')); h.update(piece)
    return h.hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def init(root):
    if not root.is_dir():
        raise ValueError('项目目录必须已存在')
    folder = root / '.ontrack'
    folder.mkdir()  # Refuse overwrite, even a partial ledger.
    (folder / 'requirements.md').write_text('# 当前需求\n\n待从用户已确认要求填写目标、约束和原子验收条目。\n', encoding='utf-8')
    write(folder / 'state.json', {
        'schema': 1, 'product_version': 'V1.0.0',
        'requirements': {'revision': 'REQ-001', 'sha256': digest(folder / 'requirements.md'),
                         'approval': {'actor': None, 'reference': None}},
        'acceptance': [], 'tasks': [], 'current_task': None,
        'next_action': '根据用户确认填写需求和验收条目', 'unknowns': [], 'blockers': [], 'pending_changes': []})
    write(folder / 'evidence.json', [])
    write(folder / 'releases.json', {'milestones': [], 'final': None})
    (folder / 'decisions.md').write_text('# 设计决策\n\n仅记录已知理由；推断和未知须明确标注。\n', encoding='utf-8')
    (folder / 'CHANGELOG.md').write_text('# 发布记录\n\n尚未发布。\n', encoding='utf-8')
    print('已初始化；需求尚未确认，检查应保持不通过。没有创建 Git、标签或 Final。')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE).decode().strip()


def approval(value):
    return (isinstance(value, dict) and value.get('actor') == 'user'
            and isinstance(value.get('reference'), str) and bool(value['reference'].strip()))


def check(root, complete=False, final=False, release=False):
    folder = root / '.ontrack'
    errors = []
    def require(ok, message):
        if not ok:
            errors.append(message)
    def read(name):
        path = folder / name
        if path.is_symlink() or not path.resolve().is_relative_to(folder.resolve()):
            raise ValueError('账本文件不能是越界路径或符号链接')
        return json.loads(path.read_text(encoding='utf-8'))
    if folder.is_symlink():
        raise ValueError('.ontrack 不能是符号链接')
    state, evidence, releases = read('state.json'), read('evidence.json'), read('releases.json')
    require(isinstance(state, dict), 'state 必须是对象')
    if not isinstance(state, dict):
        return errors
    require(state.get('schema') == 1, '未知 schema')
    require(bool(VERSION.fullmatch(str(state.get('product_version', '')))), '产品版本须为 Vx.y.z')
    req = state.get('requirements', {})
    if not isinstance(req, dict):
        req = {}
    revision, checksum = req.get('revision'), req.get('sha256')
    require(bool(REVISION.fullmatch(str(revision or ''))), '缺少有效需求修订号')
    require(approval(req.get('approval')), '需求缺少用户确认来源')
    requirements_file = folder / 'requirements.md'
    require(not requirements_file.is_symlink(), '需求文件不能是符号链接')
    require(checksum == digest(requirements_file), '需求内容变化：必须重新核对批准、修订号、任务及证据')
    for key in ['acceptance', 'tasks', 'unknowns', 'blockers']:
        require(isinstance(state.get(key), list), key + ' 必须为数组')
    acceptance = state.get('acceptance', [])
    tasks = state.get('tasks', [])
    if not isinstance(acceptance, list) or not isinstance(tasks, list):
        return errors
    require(bool(acceptance), '没有验收条目')
    require(bool(tasks), '没有任务')
    ids, task_ids, mapped = set(), set(), set()
    required_ids = set()
    for a in acceptance:
        if not isinstance(a, dict):
            require(False, '验收条目必须为对象'); continue
        aid = a.get('id')
        require(isinstance(aid, str) and bool(aid) and aid not in ids, '验收 ID 缺失或重复')
        require(isinstance(a.get('criterion'), str) and bool(a['criterion'].strip()), '验收条件不能为空')
        require(type(a.get('required')) is bool, 'required 必须为布尔值')
        if isinstance(aid, str):
            ids.add(aid)
            if a.get('required') is True:
                required_ids.add(aid)
    require(bool(required_ids), '至少需要一个本轮必需验收条目')
    for t in tasks:
        if not isinstance(t, dict):
            require(False, '任务必须为对象'); continue
        tid = t.get('id')
        require(isinstance(tid, str) and bool(tid) and tid not in task_ids, '任务 ID 缺失或重复')
        if isinstance(tid, str):
            task_ids.add(tid)
        refs = t.get('requirements')
        valid_refs = isinstance(refs, list) and bool(refs) and all(isinstance(r, str) and r in ids for r in refs)
        require(valid_refs, '任务必须映射已有验收条目')
        if valid_refs:
            mapped.update(refs)
        require(t.get('status') in ['pending', 'in_progress', 'done', 'blocked'], '任务状态不合法')
        require(isinstance(t.get('files'), list), '任务 files 必须为数组')
    require(required_ids <= mapped, '必需验收存在未映射任务')
    require(state.get('current_task') is None or state.get('current_task') in task_ids, 'current_task 不存在')
    require(isinstance(state.get('next_action'), str) and bool(state['next_action'].strip()), '缺少下一步')
    require(isinstance(evidence, list), 'evidence 必须为数组')
    require(isinstance(releases, dict) and isinstance(releases.get('milestones'), list), '发布记录格式错误')
    if not isinstance(evidence, list) or not isinstance(releases, dict):
        return errors
    evidence_ids = set()
    for e in evidence:
        if not isinstance(e, dict):
            require(False, '证据必须为对象'); continue
        eid = e.get('id')
        require(isinstance(eid, str) and bool(eid) and eid not in evidence_ids, '证据 ID 缺失或重复')
        if isinstance(eid, str):
            evidence_ids.add(eid)
        require(e.get('result') in ['passed', 'failed', 'not_run'], '证据 result 不合法')
        require(isinstance(e.get('requirement_ids'), list) and all(isinstance(r, str) and r in ids for r in e['requirement_ids']), '证据映射无效')
    if complete or final or release:
        require(not state.get('blockers'), '仍有阻塞')
        require(all(isinstance(t, dict) and t.get('status') == 'done' for t in tasks), '仍有未完成任务')
        source = source_digest(root)
        head = None
        if release or final:
            try:
                head = git(root, 'rev-parse', 'HEAD')
                require(Path(git(root, 'rev-parse', '--show-toplevel')).resolve() == root, '项目须是 Git 根目录')
                dirty = git(root, 'status', '--porcelain', '--untracked-files=all', '--', '.', ':(exclude).ontrack')
                require(not dirty, '源码工作区不干净；不要把未提交改动当作当前提交验证')
            except (subprocess.CalledProcessError, FileNotFoundError):
                require(False, '缺少可复现的 Git HEAD')
        latest = {}
        for e in evidence:
            if not isinstance(e, dict):
                continue
            if (e.get('requirements_revision') == revision
                and e.get('requirements_sha256') == checksum and e.get('source_sha256') == source
                and (not (release or final) or (head and e.get('commit') == head))
                and isinstance(e.get('requirement_ids'), list)):
                for rid in e['requirement_ids']:
                    if isinstance(rid, str):
                        latest[rid] = e.get('result') if all(isinstance(e.get(k), str) and bool(e[k].strip()) for k in ['command', 'output', 'limitations']) else 'invalid'
        covered = {rid for rid, result in latest.items() if result == 'passed'}
        require(required_ids <= covered, '必需验收缺少当前需求及当前源码的通过证据：' + ', '.join(sorted(required_ids-covered)))
        if final:
            f = releases.get('final')
            if not isinstance(f, dict):
                require(False, '没有用户确认的 Final')
            else:
                require(approval(f.get('approval')), 'Final 缺少本轮交付用户确认来源')
                require(f.get('version') == state.get('product_version') and f.get('commit') == head, 'Final 与当前版本/提交不一致')
                matches = [m for m in releases.get('milestones', []) if isinstance(m, dict) and m.get('version') == f.get('version') and m.get('commit') == head]
                require(len(matches) == 1, 'Final 必须唯一对应一个保留里程碑')
                if len(matches) == 1:
                    m = matches[0]
                    require(m.get('tag') == f.get('version'), '标签应等于版本号')
                    try:
                        tag = git(root, 'rev-parse', '--verify', 'refs/tags/' + str(m.get('tag')) + '^{commit}')
                        require(tag == head, '真实标签与提交不一致')
                    except subprocess.CalledProcessError:
                        require(False, '真实 Git 标签不存在')
                    artifacts = m.get('artifacts')
                    require(isinstance(artifacts, list), 'artifacts 必须为数组')
                    for p in artifacts if isinstance(artifacts, list) else []:
                        require(isinstance(p, str) and not Path(p).is_absolute() and (root / p).resolve().is_relative_to(root) and (root / p).is_file(), '交付物缺失或越界')
    return errors


def resume(root):
    folder = root / '.ontrack'
    if not folder.exists():
        sources = [name for name in ('openspec', '.planning') if (root / name).is_dir()]
        return {'status': 'existing_framework' if sources else 'uninitialized',
                'sources': sources, 'action': '读取现有规范，不自动初始化' if sources else '先核对项目规范和用户要求'}
    if folder.is_symlink() or (folder / 'state.json').is_symlink() or (folder / 'releases.json').is_symlink():
        raise ValueError('恢复拒绝符号链接账本')
    state = json.loads((folder / 'state.json').read_text(encoding='utf-8'))
    releases = json.loads((folder / 'releases.json').read_text(encoding='utf-8'))
    errors = check(root)
    try:
        vcs = {'head': git(root, 'rev-parse', 'HEAD'), 'working_tree': git(root, 'status', '--porcelain')}
    except (subprocess.CalledProcessError, FileNotFoundError):
        vcs = {'head': None, 'working_tree': '未建立或不可读取 Git 状态'}
    return {'status': 'needs_review' if errors else 'ready_for_review', 'errors': errors,
            'requirements': state.get('requirements'), 'product_version': state.get('product_version'),
            'final': releases.get('final'), 'tasks': state.get('tasks'), 'current_task': state.get('current_task'),
            'next_action': state.get('next_action'), 'unknowns': state.get('unknowns'),
            'blockers': state.get('blockers'), 'pending_changes': state.get('pending_changes', []), 'git': vcs,
            'note': '仅回读记录，未证明功能完成，未执行任何任务'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'check', 'snapshot', 'resume'])
    parser.add_argument('project', type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--complete', action='store_true')
    modes.add_argument('--final', action='store_true')
    modes.add_argument('--release', action='store_true')
    args = parser.parse_args()
    try:
        root = args.project.resolve(strict=True)
        if args.action == 'init':
            if args.complete or args.final or args.release:
                parser.error('init 不接受检查模式')
            init(root)
        elif args.action == 'resume':
            if args.complete or args.final or args.release:
                parser.error('resume 不接受检查模式')
            print(json.dumps(resume(root), ensure_ascii=False, indent=2))
        elif args.action == 'snapshot':
            if args.complete or args.final or args.release:
                parser.error('snapshot 不接受检查模式')
            print(json.dumps({'source_sha256': source_digest(root), 'excluded_names': sorted(EXCLUDED)}, ensure_ascii=False))
        else:
            errors = check(root, args.complete, args.final, args.release)
            for e in errors:
                print('FAIL: ' + e)
            if errors:
                return 1
            print('PASS: 一致性检查通过；不代表日志真实或验证充分。')
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as e:
        print('ERROR: ' + str(e), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
