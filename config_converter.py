#!/usr/bin/env python3
"""
Claude Code CLI → Claude Desktop 配置转换工具

将 Claude Code CLI 的配置（MCP servers、环境变量、权限等）转换为
Claude Desktop 的配置格式。

注意：部分配置项（如 hooks、权限）在 Claude Desktop 中没有对等概念，
脚本会将这些内容导出为注释或单独的参考文件，方便手动迁移。

使用方法:
    python3 config_converter.py [OPTIONS]

示例:
    # 预览转换结果
    python3 config_converter.py --project /path/to/project --dry-run

    # 转换并写入
    python3 config_converter.py --project /path/to/project

    # 仅转换全局配置
    python3 config_converter.py --global-only

    # 合并到已有的 Claude Desktop 配置（不覆盖已有项）
    python3 config_converter.py --project /path/to/project --merge
"""

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# ──────────────────────────────────────────────
# 常量
# ──────────────────────────────────────────────

CLAUDE_CODE_GLOBAL_DIR = Path.home() / ".claude"

# Claude Desktop 配置文件
CLAUDE_DESKTOP_CONFIG = (
    Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
)


# ──────────────────────────────────────────────
# 读取 Claude Code 配置
# ──────────────────────────────────────────────

def read_json(path: Path) -> Optional[dict]:
    """安全读取 JSON 文件。"""
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as e:
        print("  ⚠ 无法读取 {}: {}".format(path, e), file=sys.stderr)
        return None


def collect_code_configs(
    project_dir: Optional[str],
    include_global: bool,
    global_only: bool,
) -> Dict[str, Any]:
    """
    收集 Claude Code 的配置，返回合并后的配置字典。

    优先级: 项目配置 > 全局配置
    """
    merged = {
        "env": {},
        "permissions": {"allow": [], "deny": []},
        "mcpServers": {},
        "hooks": {},
        "model": None,
        "other": {},
    }

    configs_to_merge = []  # [(source_label, config_dict), ...]

    # 1) 全局配置
    if include_global or global_only:
        global_dir = CLAUDE_CODE_GLOBAL_DIR
        if global_dir.is_dir():
            for name in ("settings.json", "settings.local.json"):
                path = global_dir / name
                cfg = read_json(path)
                if cfg:
                    configs_to_merge.append(("global:{}".format(name), cfg))
                    print("  📄 读取: {}".format(path))

            # 项目级全局配置（projects/<hash>/settings.json）
            projects_dir = global_dir / "projects"
            if projects_dir.is_dir():
                for project_hash in projects_dir.iterdir():
                    if not project_hash.is_dir():
                        continue
                    for name in ("settings.json", "settings.local.json"):
                        path = project_hash / name
                        cfg = read_json(path)
                        if cfg:
                            configs_to_merge.append(
                                ("global-project:{}:{}".format(project_hash.name, name), cfg)
                            )
                            print("  📄 读取: {}".format(path))
        else:
            print("⚠ 全局 Claude Code 目录不存在: {}".format(global_dir))

    # 2) 项目配置
    if project_dir and not global_only:
        project_path = Path(project_dir)
        claude_dir = project_path / ".claude"
        if claude_dir.is_dir():
            for name in ("settings.json", "settings.local.json"):
                path = claude_dir / name
                cfg = read_json(path)
                if cfg:
                    configs_to_merge.append(("project:{}".format(name), cfg))
                    print("  📄 读取: {}".format(path))

    if not configs_to_merge:
        return merged

    # 按顺序合并（后面的覆盖前面的，即项目优先级高于全局）
    for label, cfg in configs_to_merge:
        # env
        if "env" in cfg:
            merged["env"].update(cfg["env"])

        # permissions
        if "permissions" in cfg:
            for key in ("allow", "deny"):
                if key in cfg["permissions"]:
                    existing = set(merged["permissions"][key])
                    for item in cfg["permissions"][key]:
                        if item not in existing:
                            merged["permissions"][key].append(item)
                            existing.add(item)

        # mcpServers
        if "mcpServers" in cfg:
            merged["mcpServers"].update(cfg["mcpServers"])

        # hooks
        if "hooks" in cfg:
            merged["hooks"].update(cfg["hooks"])

        # model
        if "model" in cfg:
            merged["model"] = cfg["model"]

        # 收集其他字段
        known_keys = {"env", "permissions", "mcpServers", "hooks", "model"}
        for key, value in cfg.items():
            if key not in known_keys:
                merged["other"][key] = value

    return merged


# ──────────────────────────────────────────────
# 转换为 Claude Desktop 格式
# ──────────────────────────────────────────────

def convert_mcp_servers(code_servers: Dict[str, Any]) -> Dict[str, Any]:
    """
    将 Claude Code 的 MCP server 配置转换为 Claude Desktop 格式。

    Claude Code 格式:
        {
            "server-name": {
                "command": "npx",
                "args": ["-y", "@some/package"],
                "env": {"KEY": "value"}  # 可选
            }
        }

    Claude Desktop 格式:
        {
            "mcpServers": {
                "server-name": {
                    "command": "npx",
                    "args": ["-y", "@some/package"],
                    "env": {"KEY": "value"},  # 可选
                    "disabled": false          # 可选
                }
            }
        }

    格式基本兼容，主要差异:
    - Claude Desktop 不支持 transport 字段
    - Claude Desktop 支持 disabled 字段
    - Claude Desktop 对 URL 类型 server 格式不同
    """
    converted = {}

    for name, config in code_servers.items():
        if not isinstance(config, dict):
            print("  ⚠ 跳过无效的 server 配置: {}".format(name), file=sys.stderr)
            continue

        server_config = {}  # type: Dict[str, Any]

        # URL 类型的 server（SSE）
        if "url" in config:
            server_config["url"] = config["url"]
            if "transport" in config:
                server_config["transport"] = config["transport"]
        else:
            # 命令行类型
            if "command" in config:
                server_config["command"] = config["command"]
            if "args" in config:
                server_config["args"] = config["args"]

        # 环境变量
        if "env" in config:
            server_config["env"] = config["env"]

        # 其他字段（如 disabled）
        for key in ("disabled",):
            if key in config:
                server_config[key] = config[key]

        if server_config:
            converted[name] = server_config

    return converted


def generate_unsupported_report(code_config: Dict[str, Any]) -> str:
    """生成无法直接转换的配置项报告。"""
    lines = []  # type: List[str]

    # Hooks
    if code_config.get("hooks"):
        lines.append("# Claude Code Hooks（Claude Desktop 不支持，需手动处理）")
        lines.append("#")
        lines.append("# 以下 hooks 在 Claude Code CLI 中配置：")
        for hook_type, hooks in code_config["hooks"].items():
            lines.append("#   {}:".format(hook_type))
            if isinstance(hooks, list):
                for hook in hooks:
                    lines.append("#     - {}".format(json.dumps(hook, ensure_ascii=False)))
            elif isinstance(hooks, dict):
                for event, hook_list in hooks.items():
                    lines.append("#     {}:".format(event))
                    if isinstance(hook_list, list):
                        for hook in hook_list:
                            lines.append("#       - {}".format(json.dumps(hook, ensure_ascii=False)))
                    else:
                        lines.append("#       {}".format(json.dumps(hook_list, ensure_ascii=False)))
        lines.append("")
        lines.append("# 替代方案：Claude Desktop 使用 skills 和 scheduled tasks 来实现类似功能。")
        lines.append("")

    # 权限
    if code_config.get("permissions"):
        perms = code_config["permissions"]
        has_rules = perms.get("allow") or perms.get("deny")
        if has_rules:
            lines.append("# Claude Code 权限规则（Claude Desktop 通过 UI 管理权限）")
            lines.append("#")
            if perms.get("allow"):
                lines.append("# Allow:")
                for rule in perms["allow"]:
                    lines.append("#   - {}".format(rule))
            if perms.get("deny"):
                lines.append("# Deny:")
                for rule in perms["deny"]:
                    lines.append("#   - {}".format(rule))
            lines.append("")
            lines.append("# 在 Claude Desktop 中，权限在 Settings > Permissions 中管理。")
            lines.append("")

    # 模型
    if code_config.get("model"):
        lines.append("# Claude Code 模型设置: {}".format(code_config["model"]))
        lines.append("# Claude Desktop 在 Settings > Model 中选择模型。")
        lines.append("")

    # 其他
    if code_config.get("other"):
        lines.append("# 其他 Claude Code 配置项（无直接对应）:")
        for key, value in code_config["other"].items():
            lines.append("#   {}: {}".format(key, json.dumps(value, ensure_ascii=False)))
        lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# 读取 / 合并 / 写入 Claude Desktop 配置
# ──────────────────────────────────────────────

def read_desktop_config() -> Dict[str, Any]:
    """读取 Claude Desktop 已有配置。"""
    if CLAUDE_DESKTOP_CONFIG.is_file():
        cfg = read_json(CLAUDE_DESKTOP_CONFIG)
        if cfg:
            print("  📄 读取已有 Claude Desktop 配置: {}".format(CLAUDE_DESKTOP_CONFIG))
            return cfg
    return {}


def merge_desktop_config(
    existing: Dict[str, Any],
    new_mcp_servers: Dict[str, Any],
    new_env: Dict[str, str],
    force_overwrite: bool = False,
) -> Dict[str, Any]:
    """
    将转换后的配置合并到 Claude Desktop 配置中。

    - mcpServers: 合并（同名 server 根据 force_overwrite 决定是否覆盖）
    - env: 合并到全局 env（如有）
    """
    result = copy.deepcopy(existing)

    # MCP Servers
    if new_mcp_servers:
        if "mcpServers" not in result:
            result["mcpServers"] = {}

        for name, config in new_mcp_servers.items():
            if name in result["mcpServers"] and not force_overwrite:
                print("  ⚠ 跳过已存在的 MCP server: {}（使用 --force 覆盖）".format(name))
                continue
            result["mcpServers"][name] = config

    return result


def write_desktop_config(config: Dict[str, Any], dry_run: bool, output_path: Optional[str] = None):
    """写入 Claude Desktop 配置。"""
    if output_path:
        target = Path(output_path)
    else:
        target = CLAUDE_DESKTOP_CONFIG

    content = json.dumps(config, indent=2, ensure_ascii=False) + "\n"

    if dry_run:
        print("\n  [DRY RUN] 将写入: {}".format(target))
        print("  内容预览:")
        # 只显示前 50 行
        preview_lines = content.split('\n')[:50]
        for line in preview_lines:
            print("    {}".format(line))
        if len(content.split('\n')) > 50:
            print("    ... (共 {} 行)".format(len(content.split('\n'))))
    else:
        # 备份已有配置
        if target.is_file() and output_path is None:
            backup = target.with_suffix('.json.backup')
            backup.write_text(target.read_text(encoding='utf-8'), encoding='utf-8')
            print("  💾 已备份原配置到: {}".format(backup))

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
        print("  ✓ 已写入: {}".format(target))


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Claude Code CLI → Claude Desktop 配置转换工具',
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
        help='同时转换全局配置（~/.claude/）'
    )
    parser.add_argument(
        '--global-only',
        action='store_true',
        help='仅转换全局配置'
    )
    parser.add_argument(
        '--merge', '-m',
        action='store_true',
        help='合并到已有的 Claude Desktop 配置（默认覆盖）'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制覆盖同名的 MCP server 配置'
    )
    parser.add_argument(
        '--output', '-o',
        help='输出文件路径（默认直接写入 Claude Desktop 配置文件）'
    )
    parser.add_argument(
        '--report',
        help='将无法转换的配置项导出为参考文件'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='预览模式，不实际写入文件'
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

    # 收集 Claude Code 配置
    print("=" * 50)
    print("Claude Code → Claude Desktop 配置转换")
    print("=" * 50)

    code_config = collect_code_configs(
        args.project,
        args.include_global,
        args.global_only
    )

    # 转换 MCP servers
    converted_mcp = convert_mcp_servers(code_config.get("mcpServers", {}))

    print("\n📋 转换结果:")
    print("  环境变量: {} 个".format(len(code_config.get("env", {}))))
    print("  权限规则: {} 条 allow, {} 条 deny".format(
        len(code_config.get("permissions", {}).get("allow", [])),
        len(code_config.get("permissions", {}).get("deny", []))
    ))
    print("  MCP Servers: {} 个（可转换 {} 个）".format(
        len(code_config.get("mcpServers", {})),
        len(converted_mcp)
    ))
    print("  Hooks: {}".format("有" if code_config.get("hooks") else "无"))
    print("  模型: {}".format(code_config.get("model") or "未指定"))

    # 生成不可转换配置的报告
    report = generate_unsupported_report(code_config)
    if report.strip():
        if args.report:
            report_path = Path(args.report)
        else:
            report_path = Path("/tmp/claude_code_unsupported_config.md")

        if args.dry_run:
            print("\n  [DRY RUN] 不可转换的配置项:")
            print(report)
        else:
            report_path.write_text(report, encoding='utf-8')
            print("\n  📝 不可转换的配置项已导出到: {}".format(report_path))
            print("     （请查看并手动迁移 hooks、权限等设置）")

    if not converted_mcp and not code_config.get("env"):
        print("\n⚠ 没有可转换的 MCP server 或环境变量配置。")
        if report.strip():
            print("  所有配置项均为 Claude Desktop 不直接支持的类型。")
            print("  请查看报告文件了解详情。")
        sys.exit(0)

    # 合并到 Claude Desktop 配置
    if args.merge:
        desktop_config = read_desktop_config()
        final_config = merge_desktop_config(
            desktop_config,
            converted_mcp,
            code_config.get("env", {}),
            force_overwrite=args.force,
        )
    else:
        final_config = {"mcpServers": converted_mcp}

    # 写入
    write_desktop_config(final_config, args.dry_run, args.output)

    # 汇总
    print("\n" + "=" * 50)
    if args.dry_run:
        print("🔍 预览完成（未实际写入）")
    else:
        print("✅ 转换完成！")
    print("   可转换项: {} 个 MCP Server".format(len(converted_mcp)))
    if report.strip():
        print("   不可转换项: 已导出到报告文件")
    if not args.dry_run:
        print("\n💡 重启 Claude Desktop 后新配置将生效。")
    print("=" * 50)


if __name__ == '__main__':
    main()
