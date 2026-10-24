#!/usr/bin/env python3
"""
Claude Code CLI → Claude Desktop 记忆转换工具

将 Claude Code CLI 的记忆文件（CLAUDE.md、.claude/memory/）转换并导入到
Claude Desktop 的记忆系统中。

使用方法:
    python3 claude_memory_converter.py [OPTIONS]

示例:
    # 转换指定项目的记忆
    python3 claude_memory_converter.py --project /path/to/project

    # 转换全局记忆（~/.claude/）
    python3 claude_memory_converter.py --global-only

    # 同时转换全局 + 指定项目
    python3 claude_memory_converter.py --project /path/to/project --include-global

    # 预览模式（不实际写入）
    python3 claude_memory_converter.py --project /path/to/project --dry-run

    # 指定 Claude Desktop 记忆目录
    python3 claude_memory_converter.py --project /path/to/project --target /custom/memory/dir
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ──────────────────────────────────────────────
# 常量
# ──────────────────────────────────────────────

CLAUDE_CODE_GLOBAL_DIR = Path.home() / ".claude"

# Claude Desktop 记忆目录（按优先级查找）
CLAUDE_DESKTOP_MEMORY_CANDIDATES = [
    Path.home() / "Library" / "Application Support" / "Claude" / "memory",
    Path.home() / ".claude-desktop" / "memory",
]


# ──────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────

def slugify(text: str) -> str:
    """将文本转为 kebab-case slug（用于文件名）。"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:60]


def parse_frontmatter(content: str) -> Tuple[dict, str]:
    """解析 YAML frontmatter，返回 (metadata_dict, body)。"""
    if not content.startswith('---'):
        return {}, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_str = parts[1].strip()
    body = parts[2].strip()

    metadata = {}
    for line in frontmatter_str.split('\n'):
        line = line.strip()
        if ':' in line:
            key, _, value = line.partition(':')
            metadata[key.strip()] = value.strip().strip('"\'')

    return metadata, body


def detect_memory_type(content: str, source_path: str) -> str:
    """根据内容和来源路径推断记忆类型。"""
    content_lower = content.lower()
    path_lower = source_path.lower()

    # 从已有 frontmatter 中读取
    metadata, _ = parse_frontmatter(content)
    if 'type' in metadata and metadata['type'] in ('user', 'feedback', 'project', 'reference'):
        return metadata['type']

    # CLAUDE.md 通常是项目指令（优先级最高，避免被内容关键词误匹配）
    if 'claude.md' in path_lower:
        return 'project'

    # 基于路径推断
    if 'memory' in path_lower:
        if any(k in path_lower for k in ['user', 'profile', 'role']):
            return 'user'
        if any(k in path_lower for k in ['feedback', 'pref']):
            return 'feedback'
        if any(k in path_lower for k in ['project', 'context']):
            return 'project'
        if any(k in path_lower for k in ['ref', 'link', 'resource']):
            return 'reference'

    # 基于内容推断
    if any(k in content_lower for k in ['role:', 'responsibility', 'i am', "i'm a", 'position:']):
        return 'user'
    if any(k in content_lower for k in ['always do', 'never do', 'prefer', "don't", 'avoid']):
        return 'feedback'
    if any(k in content_lower for k in ['deadline', 'sprint', 'milestone', 'requirement', 'feature']):
        return 'project'
    if any(k in content_lower for k in ['http', 'url', 'link', 'dashboard', 'tool:']):
        return 'reference'

    return 'project'


def extract_title(content: str, filename: str, source_path: str) -> str:
    """从内容中提取标题。"""
    metadata, body = parse_frontmatter(content)

    # 优先用 frontmatter 的 name
    if 'name' in metadata:
        return metadata['name']

    # CLAUDE.md 用所在目录名作为标题
    if 'claude.md' in filename.lower():
        parent = Path(source_path).parent
        # 如果是 .claude/CLAUDE.md，取上一级目录名
        if parent.name == '.claude':
            parent = parent.parent
        project_name = parent.name or Path.cwd().name
        return "{} 项目指令".format(project_name)

    # 尝试从第一个标题提取
    for line in body.split('\n'):
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()

    # 用文件名
    name = filename.replace('.md', '').replace('.claude-', '')
    name = name.replace('-', ' ').replace('_', ' ').title()
    return name


def generate_description(content: str, memory_type: str) -> str:
    """生成简短描述（用于 MEMORY.md 索引）。"""
    _, body = parse_frontmatter(content)

    # 取第一段有意义的文本
    for line in body.split('\n'):
        line = line.strip()
        # 跳过标题、空行、列表标记
        if not line or line.startswith('#') or line.startswith('- ') or line.startswith('* '):
            continue
        # 截断到合理长度
        desc = line[:120]
        if len(line) > 120:
            desc = desc.rsplit(' ', 1)[0] + '...'
        return desc

    return "{} type memory".format(memory_type)


def read_file_safe(path: Path) -> Optional[str]:
    """安全读取文件，失败返回 None。"""
    try:
        return path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as e:
        print("  ⚠ 无法读取 {}: {}".format(path, e), file=sys.stderr)
        return None


# ──────────────────────────────────────────────
# 收集源文件
# ──────────────────────────────────────────────

def collect_code_memories(
    project_dir: Optional[str],
    include_global: bool,
    global_only: bool
) -> List[Tuple[str, str]]:
    """
    收集 Claude Code 的记忆文件。

    返回: [(source_path, content), ...]
    """
    sources = []  # type: List[Tuple[str, str]]

    # 1) 全局记忆
    if include_global or global_only:
        global_dir = CLAUDE_CODE_GLOBAL_DIR
        if global_dir.is_dir():
            # 全局 CLAUDE.md
            global_claude_md = global_dir / "CLAUDE.md"
            if global_claude_md.is_file():
                content = read_file_safe(global_claude_md)
                if content:
                    sources.append((str(global_claude_md), content))

            # 全局 memory 目录
            global_memory = global_dir / "memory"
            if global_memory.is_dir():
                for md_file in sorted(global_memory.glob("*.md")):
                    if md_file.name == "MEMORY.md":
                        continue  # 跳过索引文件
                    content = read_file_safe(md_file)
                    if content:
                        sources.append((str(md_file), content))

            # projects 子目录
            projects_dir = global_dir / "projects"
            if projects_dir.is_dir():
                for project_hash in projects_dir.iterdir():
                    if not project_hash.is_dir():
                        continue
                    for md_file in sorted(project_hash.glob("*.md")):
                        content = read_file_safe(md_file)
                        if content:
                            sources.append((str(md_file), content))
        else:
            print("⚠ 全局 Claude Code 目录不存在: {}".format(global_dir))

    # 2) 项目记忆
    if project_dir and not global_only:
        project_path = Path(project_dir)

        # 项目根目录 CLAUDE.md
        project_claude_md = project_path / "CLAUDE.md"
        if project_claude_md.is_file():
            content = read_file_safe(project_claude_md)
            if content:
                sources.append((str(project_claude_md), content))

        # 项目 .claude/ 目录
        claude_dir = project_path / ".claude"
        if claude_dir.is_dir():
            # .claude/CLAUDE.md
            claude_dir_md = claude_dir / "CLAUDE.md"
            if claude_dir_md.is_file():
                content = read_file_safe(claude_dir_md)
                if content:
                    sources.append((str(claude_dir_md), content))

            # .claude/memory/
            memory_dir = claude_dir / "memory"
            if memory_dir.is_dir():
                for md_file in sorted(memory_dir.glob("*.md")):
                    if md_file.name == "MEMORY.md":
                        continue
                    content = read_file_safe(md_file)
                    if content:
                        sources.append((str(md_file), content))

            # .claude/commands/ (自定义命令，也可作为参考记忆)
            commands_dir = claude_dir / "commands"
            if commands_dir.is_dir():
                for md_file in sorted(commands_dir.glob("*.md")):
                    content = read_file_safe(md_file)
                    if content:
                        sources.append((str(md_file), content))

    return sources


# ──────────────────────────────────────────────
# 转换 & 写入
# ──────────────────────────────────────────────

def convert_memory(
    source_path: str,
    content: str,
    project_name: Optional[str]
) -> Dict:
    """
    将 Claude Code 记忆转换为 Claude Desktop 格式。

    返回: {filename, name, description, type, body, source}
    """
    filename = Path(source_path).name
    metadata, body = parse_frontmatter(content)

    # 提取字段
    name = extract_title(content, filename, source_path)
    memory_type = detect_memory_type(content, source_path)
    description = metadata.get('description', '') or generate_description(content, memory_type)

    # 构建 slug 文件名
    slug = metadata.get('name', '') or slugify(name)
    if not slug:
        slug = slugify(filename.replace('.md', ''))

    # 避免文件名冲突：加项目前缀
    if project_name and 'claude.md' in filename.lower():
        slug = "{}-{}".format(slugify(project_name), slug)

    # 确保不重名
    if not slug:
        slug = "memory-{}".format(datetime.now().strftime('%H%M%S'))

    return {
        'filename': "{}.md".format(slug),
        'name': name,
        'description': description,
        'type': memory_type,
        'body': body,
        'source': source_path,
    }


def write_memory_file(memory: Dict, target_dir: Path, dry_run: bool) -> Path:
    """写入单个记忆文件到 Claude Desktop 记忆目录。"""
    target_path = target_dir / memory['filename']

    # 如果已存在，加数字后缀
    counter = 1
    original_stem = target_path.stem
    while target_path.exists() and not dry_run:
        target_path = target_dir / "{}-{}.md".format(original_stem, counter)
        counter += 1

    # 构建文件内容
    file_content = (
        "---\n"
        "name: {name}\n"
        "description: {description}\n"
        "type: {type}\n"
        "---\n"
        "\n"
        "{body}\n"
    ).format(**memory)

    if dry_run:
        print("  [DRY RUN] 将写入: {}".format(target_path))
        print("    name: {}".format(memory['name']))
        print("    type: {}".format(memory['type']))
        print("    desc: {}...".format(memory['description'][:80]))
    else:
        target_path.write_text(file_content, encoding='utf-8')
        print("  ✓ 已写入: {}".format(target_path.name))

    return target_path


def build_memory_index(target_dir: Path, memories: List[Dict], dry_run: bool):
    """构建/更新 MEMORY.md 索引文件。"""
    index_path = target_dir / "MEMORY.md"

    # 读取已有索引（如果存在）
    existing_lines = []  # type: List[str]
    if index_path.is_file() and not dry_run:
        existing_content = read_file_safe(index_path)
        if existing_content:
            existing_lines = [
                line for line in existing_content.split('\n')
                if line.strip() and not line.startswith('#')
            ]

    # 生成新条目
    new_lines = []  # type: List[str]
    for mem in memories:
        desc = mem['description'][:100]
        if len(mem['description']) > 100:
            desc = desc.rsplit(' ', 1)[0] + '...'
        new_lines.append("- [{}]({}) — {}".format(mem['name'], mem['filename'], desc))

    # 合并（去重）
    all_lines = existing_lines.copy()
    for line in new_lines:
        # 简单去重：检查文件名是否已存在
        filename_match = re.search(r'\]\(([^)]+)\)', line)
        if filename_match:
            fname = filename_match.group(1)
            if not any(fname in existing for existing in all_lines):
                all_lines.append(line)
        else:
            all_lines.append(line)

    # 构建索引内容
    index_content = "# Memory Index\n\n"
    index_content += "\n".join(all_lines)
    index_content += "\n"

    if dry_run:
        print("\n  [DRY RUN] 将更新 MEMORY.md ({} 条记录)".format(len(all_lines)))
    else:
        index_path.write_text(index_content, encoding='utf-8')
        print("\n  ✓ 已更新 MEMORY.md ({} 条记录)".format(len(all_lines)))


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────

def find_target_dir(custom_target: Optional[str]) -> Path:
    """查找 Claude Desktop 记忆目录。"""
    if custom_target:
        target = Path(custom_target)
        target.mkdir(parents=True, exist_ok=True)
        return target

    for candidate in CLAUDE_DESKTOP_MEMORY_CANDIDATES:
        if candidate.is_dir():
            return candidate

    # 如果都不存在，创建第一个
    default = CLAUDE_DESKTOP_MEMORY_CANDIDATES[0]
    default.mkdir(parents=True, exist_ok=True)
    return default


def main():
    parser = argparse.ArgumentParser(
        description='Claude Code CLI → Claude Desktop 记忆转换工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--project', '-p',
        help='Claude Code 项目目录路径'
    )
    parser.add_argument(
        '--include-global', '-g',
        action='store_true',
        help='同时转换全局记忆（~/.claude/）'
    )
    parser.add_argument(
        '--global-only',
        action='store_true',
        help='仅转换全局记忆'
    )
    parser.add_argument(
        '--target', '-t',
        help='Claude Desktop 记忆目录（默认自动检测）'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='预览模式，不实际写入文件'
    )
    parser.add_argument(
        '--skip-claude-md',
        action='store_true',
        help='跳过 CLAUDE.md 文件（仅转换 memory/ 目录下的文件）'
    )

    args = parser.parse_args()

    # 参数校验
    if not args.project and not args.global_only and not args.include_global:
        parser.error("请指定 --project、--global-only 或 --include-global 之一")

    if args.project:
        project_path = Path(args.project)
        if not project_path.is_dir():
            print("❌ 项目目录不存在: {}".format(args.project), file=sys.stderr)
            sys.exit(1)
        project_name = project_path.name
    else:
        project_name = None

    # 收集源文件
    print("=" * 50)
    print("Claude Code → Claude Desktop 记忆转换")
    print("=" * 50)

    sources = collect_code_memories(
        args.project,
        args.include_global,
        args.global_only
    )

    # 过滤 CLAUDE.md（如果指定跳过）
    if args.skip_claude_md:
        sources = [(p, c) for p, c in sources if 'claude.md' not in Path(p).name.lower()]

    if not sources:
        print("\n⚠ 未找到任何 Claude Code 记忆文件。")
        print("\n已检查的位置:")
        if args.global_only or args.include_global:
            print("  - {}/CLAUDE.md".format(CLAUDE_CODE_GLOBAL_DIR))
            print("  - {}/memory/".format(CLAUDE_CODE_GLOBAL_DIR))
            print("  - {}/projects/".format(CLAUDE_CODE_GLOBAL_DIR))
        if args.project:
            print("  - {}/CLAUDE.md".format(args.project))
            print("  - {}/.claude/CLAUDE.md".format(args.project))
            print("  - {}/.claude/memory/".format(args.project))
        print("\n提示: 确保已使用 Claude Code CLI 并积累了记忆后再运行此工具。")
        sys.exit(0)

    print("\n📁 找到 {} 个源文件:".format(len(sources)))
    for path, _ in sources:
        print("  - {}".format(path))

    # 转换
    target_dir = find_target_dir(args.target)
    print("\n🎯 目标目录: {}".format(target_dir))

    converted = []
    for source_path, content in sources:
        memory = convert_memory(source_path, content, project_name)
        converted.append(memory)

    # 写入
    print("\n📝 转换结果:")
    written_files = []  # type: List[Dict]
    for memory in converted:
        target_path = write_memory_file(memory, target_dir, args.dry_run)
        memory['target_path'] = target_path
        written_files.append(memory)

    # 更新索引
    build_memory_index(target_dir, written_files, args.dry_run)

    # 汇总
    print("\n" + "=" * 50)
    if args.dry_run:
        print("🔍 预览完成（未实际写入）")
    else:
        print("✅ 转换完成！")
    print("   源文件: {} 个".format(len(sources)))
    print("   目标: {}".format(target_dir))
    if not args.dry_run:
        print("\n💡 重启 Claude Desktop 后记忆将自动生效。")
    print("=" * 50)


if __name__ == '__main__':
    main()
