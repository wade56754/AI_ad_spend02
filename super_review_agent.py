#!/usr/bin/env python3
"""
Super Review Agent - 超级文档自动审查系统 (稳健性增强版)

该脚本用于 orchestrate Codex 和 Claude 两个大模型：
- Codex：用于文档审查，输出审查报告
- Claude：用于文档修复，内嵌 doc-fixer 行为规则

核心特性 (v2.1):
- ✅ Codex 路径自动检测（无需手动指定 --codex-cmd 参数）
- ✅ 内嵌 Skill 行为规则（P0 优先、禁止发明字段、保持结构完整等）
- ✅ 跨平台兼容（Windows/macOS/Linux，统一 stdin 传递策略）
- ✅ 增强容错性（7 种 P0/P1 解析方法 + 正面检测兜底）
- ✅ 结构化日志（[Round X/Y] 轮次前缀 + 图标）
- ✅ 空文档检测（防止 Claude 返回空内容覆盖原文档）

支持 4 个模式：
1. review-only: 只调用 Codex，生成审查报告
2. fix-once: Codex 审查 + Claude 修一次
3. auto-polish-loop: 多轮循环，直到无 P0/P1 或 max_rounds
4. quick-check: 快速检测是否存在 P0/P1

使用示例：
    python super_review_agent.py review-only \
        --doc docs/API.md \
        --codex-prompt prompts/reviewer.txt \
        --output tmp/review.md

    python super_review_agent.py auto-polish-loop \
        --doc docs/API.md \
        --codex-prompt prompts/reviewer.txt \
        --skill-name doc-fixer-claude \
        --max-rounds 5 \
        --output tmp/fixed.md \
        --verbose
"""

import argparse
import logging
import subprocess
import sys
import re
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass

# 返回码常量
SUCCESS = 0
ERROR_GENERAL = 1
ERROR_FILE_NOT_FOUND = 2
ERROR_SUBPROCESS_FAILED = 3
ERROR_INVALID_ARGS = 4

# 默认配置
DEFAULT_CLAUDE_CMD = "claude"
DEFAULT_MAX_ROUNDS = 3
DEFAULT_TIMEOUT = 600  # 10 分钟


def find_codex_cmd() -> str:
    """
    自动检测 Codex CLI 路径

    优先级:
    1. 从 PATH 中查找 'codex' 命令
    2. Windows 特殊路径检测
    3. 返回默认命令名 'codex' (如果以上都失败)

    Returns:
        Codex 命令路径（完整路径或命令名）
    """
    import shutil

    # 首先尝试从 PATH 中查找
    codex_path = shutil.which("codex")
    if codex_path:
        return codex_path

    # Windows 特殊路径
    if sys.platform == "win32":
        username = os.getenv("USERNAME", "")
        possible_paths = [
            rf"C:\Users\{username}\AppData\Roaming\npm\codex.cmd",
            r"C:\Program Files\nodejs\codex.cmd",
            rf"C:\Users\{username}\AppData\Local\Programs\codex\codex.cmd"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path

    # 返回默认命令名（可能会失败，但会有清晰的错误信息）
    return "codex"


# 自动检测 Codex 命令路径
DEFAULT_CODEX_CMD = find_codex_cmd()


@dataclass
class ReviewConfig:
    """审查配置"""
    doc_path: Path
    codex_prompt_path: Path
    codex_cmd: str
    output_path: Optional[Path]  # quick-check 不需要 output
    timeout: int
    verbose: bool


@dataclass
class FixConfig(ReviewConfig):
    """修复配置（继承审查配置）"""
    claude_cmd: str
    skill_name: str


@dataclass
class LoopConfig(FixConfig):
    """循环配置（继承修复配置）"""
    max_rounds: int


def setup_logging(verbose: bool = False) -> None:
    """
    配置日志系统

    Args:
        verbose: 是否启用详细日志
    """
    level = logging.DEBUG if verbose else logging.INFO
    format_str = "[%(levelname)s] %(message)s"

    # Windows 兼容性：设置 UTF-8 编码输出
    import io
    if sys.platform == "win32":
        try:
            # 在 Windows 上强制使用 UTF-8 编码
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            # 如果 stdout/stderr 已经是 TextIOWrapper，跳过
            pass

    logging.basicConfig(level=level, format=format_str, stream=sys.stdout)


def log_mode_header(mode: str, doc_path: Path, extra_info: dict = None) -> None:
    """
    统一输出模式头部信息

    Args:
        mode: 模式名称
        doc_path: 文档路径
        extra_info: 额外信息字典（如 max_rounds, prompt 等）
    """
    logging.info("=" * 70)
    logging.info(f"🚀 模式: {mode}")
    logging.info(f"📄 文档: {doc_path}")
    if extra_info:
        for key, value in extra_info.items():
            # 使用更友好的图标
            icon = "⚙️ " if "rounds" in key.lower() or "max" in key.lower() else "📝 "
            logging.info(f"{icon}{key}: {value}")
    logging.info("=" * 70)


def validate_paths(doc_path: Path, codex_prompt_path: Path) -> bool:
    """
    验证必需的文件路径是否存在

    Args:
        doc_path: 文档路径
        codex_prompt_path: Codex prompt 路径

    Returns:
        True 如果所有路径都有效
    """
    if not doc_path.exists():
        logging.error(f"文档不存在: {doc_path}")
        return False
    if not doc_path.is_file():
        logging.error(f"文档路径不是文件: {doc_path}")
        return False
    if not codex_prompt_path.exists():
        logging.error(f"Prompt 文件不存在: {codex_prompt_path}")
        return False
    if not codex_prompt_path.is_file():
        logging.error(f"Prompt 路径不是文件: {codex_prompt_path}")
        return False
    return True


def validate_output_required(output_path: Optional[Path], mode_name: str) -> bool:
    """
    验证 output_path 在需要的模式中是否已提供

    Args:
        output_path: 输出路径
        mode_name: 模式名称

    Returns:
        True 如果验证通过
    """
    if output_path is None:
        logging.error(f"{mode_name} 模式需要 --output 参数")
        return False
    return True


def safe_mkdir(path: Path) -> bool:
    """
    安全地创建目录

    Args:
        path: 目录路径

    Returns:
        True 如果成功创建或已存在
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except (PermissionError, OSError) as e:
        logging.error(f"无法创建目录 {path}: {e}")
        return False


def safe_write_file(path: Path, content: str) -> bool:
    """
    安全地写入文件

    Args:
        path: 文件路径
        content: 文件内容

    Returns:
        True 如果写入成功
    """
    try:
        # 确保父目录存在（如果需要）
        if path.parent and not path.parent.exists():
            if not safe_mkdir(path.parent):
                return False

        path.write_text(content, encoding='utf-8')
        return True
    except (UnicodeEncodeError, PermissionError, OSError) as e:
        logging.error(f"无法写入文件 {path}: {e}")
        return False


def safe_read_file(path: Path) -> Optional[str]:
    """
    安全地读取文件

    Args:
        path: 文件路径

    Returns:
        文件内容，如果失败返回 None
    """
    try:
        return path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, PermissionError, OSError) as e:
        logging.error(f"无法读取文件 {path}: {e}")
        return None


def invoke_codex_review(
    doc_path: Path,
    codex_prompt_path: Path,
    codex_cmd: str = DEFAULT_CODEX_CMD,
    timeout: int = DEFAULT_TIMEOUT
) -> Optional[str]:
    """
    调用 Codex 进行文档审查

    Args:
        doc_path: 待审查文档的路径
        codex_prompt_path: Codex 审查 prompt 文件路径
        codex_cmd: Codex 命令（默认 "codex"）
        timeout: 超时时间（秒）

    Returns:
        审查报告文本，如果失败返回 None
    """
    try:
        import tempfile
        import sys
        
        # 读取 prompt 文件内容
        prompt_content = safe_read_file(codex_prompt_path)
        if prompt_content is None:
            logging.error(f"无法读取 prompt 文件: {codex_prompt_path}")
            return None
        
        # 读取文档内容
        doc_content = safe_read_file(doc_path)
        if doc_content is None:
            logging.error(f"无法读取文档文件: {doc_path}")
            return None
        
        # 构建完整的 prompt：prompt 文件内容 + 文档内容
        full_prompt = f"{prompt_content}\n\n---\n\n待审查文档内容：\n\n{doc_content}"
        
        # 创建临时文件存储完整的 prompt
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(full_prompt)
            tmp_prompt_path = tmp_file.name
        
        try:
            # 使用 codex exec，通过 stdin 传递 prompt
            # 跨平台兼容策略：统一使用 stdin 传递，避免 PowerShell 路径问题
            cmd = [codex_cmd, "exec"]
            input_text = full_prompt

            logging.debug(f"执行命令: {' '.join(cmd)}")
            logging.debug(f"超时设置: {timeout}s")
            logging.debug(f"Prompt 长度: {len(input_text)} 字符")

            result = subprocess.run(
                cmd,
                input=input_text,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=False,
                timeout=timeout,
                shell=False  # 明确禁用 shell，提升安全性
            )
        finally:
            # 清理临时文件
            try:
                import os
                os.unlink(tmp_prompt_path)
            except Exception:
                pass

        if result.returncode != 0:
            logging.error(f"Codex 调用失败 (exit code {result.returncode})")
            if result.stderr:
                logging.error(f"STDERR: {result.stderr.strip()}")
            else:
                logging.error("未返回错误信息，可能是命令路径问题或权限不足")
            return None

        # 记录 stderr（如果有）
        if result.stderr and result.stderr.strip():
            logging.debug(f"Codex STDERR: {result.stderr.strip()}")

        # 检查空输出
        if not result.stdout or not result.stdout.strip():
            logging.error("Codex 返回了空输出，可能是命令参数错误或模型无响应")
            return None

        logging.debug(f"Codex 返回 {len(result.stdout)} 字符")
        return result.stdout

    except FileNotFoundError:
        logging.error(f"Codex 命令未找到: {codex_cmd}")
        logging.error("请确保 Codex CLI 已安装并在 PATH 中")
        return None
    except subprocess.TimeoutExpired:
        logging.error(f"Codex 调用超时（>{timeout}s）")
        return None
    except (OSError, PermissionError) as e:
        logging.error(f"Codex 调用系统错误: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Codex 调用未预期异常: {str(e)}")
        return None


def invoke_claude_fix(
    original_doc_path: Path,
    review_report_path: Path,
    skill_name: str,
    claude_cmd: str = DEFAULT_CLAUDE_CMD,
    timeout: int = DEFAULT_TIMEOUT
) -> Optional[str]:
    """
    调用 Claude 进行文档修复

    Args:
        original_doc_path: 原始文档路径
        review_report_path: 审查报告路径
        skill_name: Claude Skill 名称
        claude_cmd: Claude 命令（默认 "claude"）
        timeout: 超时时间（秒）

    Returns:
        修复后的完整文档文本，如果失败返回 None
    """
    try:
        import sys
        
        # 读取原始文档和审查报告
        original_content = safe_read_file(original_doc_path)
        review_content = safe_read_file(review_report_path)
        
        if original_content is None:
            logging.error(f"无法读取原始文档: {original_doc_path}")
            return None
        if review_content is None:
            logging.error(f"无法读取审查报告: {review_report_path}")
            return None
        
        # 构建 prompt，内嵌 Skill 行为规则（基于 doc-fixer-claude 核心逻辑）
        prompt = f"""你是一个专业的文档修复工具。请严格遵循以下规则修复文档：

## 📋 修复规则 (Inviolable Rules)

1. **P0 优先修复**: 必须修复所有 P0 缺陷（阻塞性问题）
2. **P1 次优先**: 在修复 P0 后，尽量修复 P1 缺陷
3. **禁止发明字段**: 不得添加审查报告中未提及的新问题或字段
4. **保持文档结构**: 不改变原文档的章节编号、标题层次、整体组织结构
5. **保持版本信息**: 如有版本号、更新日期等元信息，保持不变（除非审查报告明确要求修改）
6. **输出完整文档**: 必须输出完整的修复后文档，不得省略任何章节或部分
7. **禁止添加注释**: 不添加 "<!-- 已修复 P0-XXX -->" 等修复痕迹注释

## 📄 原始文档
---
{original_content}
---

## 📊 审查报告
---
{review_content}
---

## 🎯 输出要求
- 直接输出修复后的完整文档内容（Markdown 格式）
- 不添加任何前缀说明（如 "修复后的文档如下："）
- 不添加任何后缀总结（如 "已完成 X 项修复"）
- 确保输出为有效的 Markdown 格式

现在开始修复："""
        
        # 使用 claude -p (print mode) 进行非交互式调用
        # 跨平台统一策略
        cmd = [claude_cmd, "-p", "--output-format", "text"]
        if skill_name:
            cmd.extend(["--skill", skill_name])
        input_text = prompt

        logging.debug(f"执行命令: {' '.join(cmd)}")
        logging.debug(f"超时设置: {timeout}s")
        logging.debug(f"Prompt 长度: {len(input_text)} 字符")

        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=False,
            timeout=timeout,
            shell=False  # 明确禁用 shell，提升安全性
        )

        if result.returncode != 0:
            error_msg = f"❌ Claude 调用失败 (exit code {result.returncode})"
            if result.stderr:
                error_msg += f"\nSTDERR: {result.stderr.strip()}"
            else:
                error_msg += "\n未返回错误信息，可能是命令路径问题或权限不足"
            logging.error(error_msg)
            print(error_msg)  # 确保用户能看到错误
            return None

        # 记录 stderr（如果有）
        if result.stderr and result.stderr.strip():
            logging.debug(f"Claude STDERR: {result.stderr.strip()}")

        # 检查空输出
        if not result.stdout or not result.stdout.strip():
            error_msg = "❌ Claude 返回了空输出，可能是 Skill 执行失败或无响应"
            logging.error(error_msg)
            print(error_msg)
            return None

        # 检查输出是否过短（可能是格式错误）
        if len(result.stdout.strip()) < 100:
            logging.warning(f"⚠️  Claude 返回的内容过短 ({len(result.stdout)} 字符)，可能不是完整文档")
            logging.warning("将仍然使用该输出，但建议手动检查")

        logging.debug(f"Claude 返回 {len(result.stdout)} 字符")
        return result.stdout

    except FileNotFoundError:
        error_msg = f"❌ Claude 命令未找到: {claude_cmd}\n请确保 Claude CLI 已安装并在 PATH 中"
        logging.error(error_msg)
        print(error_msg)
        return None
    except subprocess.TimeoutExpired:
        logging.error(f"Claude 调用超时（>{timeout}s）")
        return None
    except (OSError, PermissionError) as e:
        logging.error(f"Claude 调用系统错误: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Claude 调用未预期异常: {str(e)}")
        return None


def parse_p0_p1_count(review_report: str) -> Tuple[int, int, bool]:
    """
    解析审查报告中的 P0 和 P1 缺陷数量

    支持多种格式：
    - "P0 缺陷: 3个" / "P0 缺陷：3个" (中文)
    - "P0 defects: 3" / "P0 Defects: 3" (英文)
    - "P0: 3" / "P0:3"
    - 统计唯一的 P0-XXX-XXX 模式（仅在缺陷段落中）
    - 统计 markdown 列表中的 P0/P1 条目
    - 在 ## P0 / ## P1 标题段落中统计列表项（兜底策略）

    Args:
        review_report: 审查报告文本

    Returns:
        (P0 数量, P1 数量, 是否成功解析)
        第三个返回值表示是否至少有一种方法成功解析出数字
    """
    # 提前检查：空输入
    if not review_report or not review_report.strip():
        logging.warning("⚠️  审查报告为空，无法解析 P0/P1 数量")
        return 0, 0, False

    p0_count = 0
    p1_count = 0
    p0_parsed = False
    p1_parsed = False

    # 方法 1: 匹配摘要行（中文）
    p0_summary_cn = re.search(r'P0\s*缺陷[：:]\s*(\d+)\s*个', review_report)
    p1_summary_cn = re.search(r'P1\s*缺陷[：:]\s*(\d+)\s*个', review_report)

    if p0_summary_cn:
        p0_count = int(p0_summary_cn.group(1))
        p0_parsed = True
        logging.debug(f"方法 1 (中文摘要) 解析到 P0: {p0_count}")
    if p1_summary_cn:
        p1_count = int(p1_summary_cn.group(1))
        p1_parsed = True
        logging.debug(f"方法 1 (中文摘要) 解析到 P1: {p1_count}")

    # 方法 2: 匹配摘要行（英文）
    if not p0_parsed:
        p0_summary_en = re.search(r'P0\s+defects?[：:]\s*(\d+)', review_report, re.IGNORECASE)
        if p0_summary_en:
            p0_count = int(p0_summary_en.group(1))
            p0_parsed = True
            logging.debug(f"方法 2 (英文摘要) 解析到 P0: {p0_count}")

    if not p1_parsed:
        p1_summary_en = re.search(r'P1\s+defects?[：:]\s*(\d+)', review_report, re.IGNORECASE)
        if p1_summary_en:
            p1_count = int(p1_summary_en.group(1))
            p1_parsed = True
            logging.debug(f"方法 2 (英文摘要) 解析到 P1: {p1_count}")

    # 方法 3: 简化格式 "P0: 3"
    if not p0_parsed:
        p0_simple = re.search(r'P0\s*[：:]\s*(\d+)', review_report)
        if p0_simple:
            p0_count = int(p0_simple.group(1))
            p0_parsed = True
            logging.debug(f"方法 3 (简化格式) 解析到 P0: {p0_count}")

    if not p1_parsed:
        p1_simple = re.search(r'P1\s*[：:]\s*(\d+)', review_report)
        if p1_simple:
            p1_count = int(p1_simple.group(1))
            p1_parsed = True
            logging.debug(f"方法 3 (简化格式) 解析到 P1: {p1_count}")

    # 方法 4: 统计唯一的缺陷 ID（仅在缺陷部分，避免假阳性）
    # 只在包含 "缺陷" 或 "defect" 关键词的段落中统计
    defect_sections = re.findall(
        r'(?:缺陷|defect|issue).*?(?=\n\n|\Z)',
        review_report,
        re.IGNORECASE | re.DOTALL
    )

    if not p0_parsed and defect_sections:
        p0_patterns = set()
        for section in defect_sections:
            p0_patterns.update(re.findall(r'\bP0-[A-Z]+-\d+\b', section))
        if p0_patterns:
            p0_count = len(p0_patterns)
            p0_parsed = True
            logging.debug(f"方法 4 (缺陷 ID) 解析到 P0: {p0_count}")

    if not p1_parsed and defect_sections:
        p1_patterns = set()
        for section in defect_sections:
            p1_patterns.update(re.findall(r'\bP1-[A-Z]+-\d+\b', section))
        if p1_patterns:
            p1_count = len(p1_patterns)
            p1_parsed = True
            logging.debug(f"方法 4 (缺陷 ID) 解析到 P1: {p1_count}")

    # 方法 5: 统计 markdown 列表中的 P0/P1 条目
    if not p0_parsed:
        p0_list_items = re.findall(r'^\s*[-*]\s+P0[-:]', review_report, re.MULTILINE)
        if p0_list_items:
            p0_count = len(p0_list_items)
            p0_parsed = True
            logging.debug(f"方法 5 (markdown 列表) 解析到 P0: {p0_count}")

    if not p1_parsed:
        p1_list_items = re.findall(r'^\s*[-*]\s+P1[-:]', review_report, re.MULTILINE)
        if p1_list_items:
            p1_count = len(p1_list_items)
            p1_parsed = True
            logging.debug(f"方法 5 (markdown 列表) 解析到 P1: {p1_count}")

    # 方法 6: 在 ## P0 / ## P1 标题段落中统计列表项（兜底策略）
    if not p0_parsed:
        p0_section_match = re.search(
            r'^#{1,3}\s*P0.*?\n(.*?)(?=^#{1,3}\s|\Z)',
            review_report,
            re.MULTILINE | re.DOTALL
        )
        if p0_section_match:
            p0_section_content = p0_section_match.group(1)
            p0_list_in_section = re.findall(r'^\s*[-*]\s+', p0_section_content, re.MULTILINE)
            if p0_list_in_section:
                p0_count = len(p0_list_in_section)
                p0_parsed = True
                logging.debug(f"方法 6 (## P0 段落列表) 解析到 P0: {p0_count}")

    if not p1_parsed:
        p1_section_match = re.search(
            r'^#{1,3}\s*P1.*?\n(.*?)(?=^#{1,3}\s|\Z)',
            review_report,
            re.MULTILINE | re.DOTALL
        )
        if p1_section_match:
            p1_section_content = p1_section_match.group(1)
            p1_list_in_section = re.findall(r'^\s*[-*]\s+', p1_section_content, re.MULTILINE)
            if p1_list_in_section:
                p1_count = len(p1_list_in_section)
                p1_parsed = True
                logging.debug(f"方法 6 (## P1 段落列表) 解析到 P1: {p1_count}")

    # 方法 7: 正面检测（如 "无 P0/P1 缺陷" "0个缺陷" 等）
    if not p0_parsed and not p1_parsed:
        # 检测 "无 P0" "无 P1" "0个 P0" 等正面表述
        no_defects_patterns = [
            r'无\s*P0\s*缺陷',
            r'P0\s*缺陷[：:]\s*0',
            r'P0\s*[：:]\s*0',
            r'0\s*个\s*P0',
            r'no\s+P0\s+defects?',
            re.compile(r'P0\s+defects?[：:]\s*0', re.IGNORECASE)
        ]

        for pattern in no_defects_patterns:
            if isinstance(pattern, str):
                if re.search(pattern, review_report):
                    p0_count = 0
                    p0_parsed = True
                    logging.debug(f"方法 7 (正面检测) 解析到 P0: 0 (匹配: {pattern})")
                    break
            else:  # re.Pattern
                if pattern.search(review_report):
                    p0_count = 0
                    p0_parsed = True
                    logging.debug(f"方法 7 (正面检测) 解析到 P0: 0 (匹配: 英文)")
                    break

        # 同样检测 P1
        no_p1_patterns = [
            r'无\s*P1\s*缺陷',
            r'P1\s*缺陷[：:]\s*0',
            r'P1\s*[：:]\s*0',
            r'0\s*个\s*P1',
            r'no\s+P1\s+defects?',
            re.compile(r'P1\s+defects?[：:]\s*0', re.IGNORECASE)
        ]

        for pattern in no_p1_patterns:
            if isinstance(pattern, str):
                if re.search(pattern, review_report):
                    p1_count = 0
                    p1_parsed = True
                    logging.debug(f"方法 7 (正面检测) 解析到 P1: 0 (匹配: {pattern})")
                    break
            else:  # re.Pattern
                if pattern.search(review_report):
                    p1_count = 0
                    p1_parsed = True
                    logging.debug(f"方法 7 (正面检测) 解析到 P1: 0 (匹配: 英文)")
                    break

    # 判断是否至少成功解析了一个
    is_parsed = p0_parsed or p1_parsed

    if not is_parsed:
        logging.warning("⚠️  所有解析方法都未能提取 P0/P1 数量")
        logging.warning("可能原因：审查报告格式不符合预期，或报告内容为空")
        logging.warning("请检查审查报告内容，或手动确认缺陷数量")

    logging.debug(f"最终解析结果 - P0: {p0_count}, P1: {p1_count}, 成功解析: {is_parsed}")
    return p0_count, p1_count, is_parsed


def mode_review_only(config: ReviewConfig) -> int:
    """
    模式 1: review-only
    只调用 Codex，生成审查报告

    Args:
        config: 审查配置

    Returns:
        退出码
    """
    log_mode_header("review-only", config.doc_path, {"Prompt": config.codex_prompt_path})

    if not validate_paths(config.doc_path, config.codex_prompt_path):
        return ERROR_FILE_NOT_FOUND

    if not validate_output_required(config.output_path, "review-only"):
        return ERROR_INVALID_ARGS

    logging.info("正在调用 Codex 进行审查...")
    review_report = invoke_codex_review(
        config.doc_path,
        config.codex_prompt_path,
        config.codex_cmd,
        config.timeout
    )

    if review_report is None:
        return ERROR_SUBPROCESS_FAILED

    if not safe_write_file(config.output_path, review_report):
        return ERROR_GENERAL

    logging.info(f"✓ 审查报告已保存至: {config.output_path}")

    p0_count, p1_count, is_parsed = parse_p0_p1_count(review_report)

    if not is_parsed:
        logging.error("无法解析审查报告中的 P0/P1 数量，请手动检查报告内容")

    logging.info(f"统计: P0 缺陷 {p0_count}个, P1 缺陷 {p1_count}个")

    return SUCCESS


def mode_fix_once(config: FixConfig) -> int:
    """
    模式 2: fix-once
    Codex 审查 + Claude 修一次

    Args:
        config: 修复配置

    Returns:
        退出码
    """
    log_mode_header("fix-once", config.doc_path)

    if not validate_paths(config.doc_path, config.codex_prompt_path):
        return ERROR_FILE_NOT_FOUND

    if not validate_output_required(config.output_path, "fix-once"):
        return ERROR_INVALID_ARGS

    # 步骤 1: Codex 审查
    logging.info("[1/2] 正在调用 Codex 进行审查...")
    review_report = invoke_codex_review(
        config.doc_path,
        config.codex_prompt_path,
        config.codex_cmd,
        config.timeout
    )

    if review_report is None:
        return ERROR_SUBPROCESS_FAILED

    # 保存中间结果
    review_temp_path = config.output_path.parent / f"{config.output_path.stem}_review.md"
    if not safe_write_file(review_temp_path, review_report):
        return ERROR_GENERAL

    logging.info(f"中间文件: {review_temp_path}")

    p0_count, p1_count, is_parsed = parse_p0_p1_count(review_report)

    if not is_parsed:
        logging.warning("无法解析审查报告中的 P0/P1 数量，但仍会继续修复")

    logging.info(f"统计: P0 缺陷 {p0_count}个, P1 缺陷 {p1_count}个")

    # 步骤 2: Claude 修复
    logging.info("[2/2] 正在调用 Claude 进行修复...")
    fixed_doc = invoke_claude_fix(
        config.doc_path,
        review_temp_path,
        config.skill_name,
        config.claude_cmd,
        config.timeout
    )

    if fixed_doc is None:
        return ERROR_SUBPROCESS_FAILED

    if not safe_write_file(config.output_path, fixed_doc):
        return ERROR_GENERAL

    logging.info(f"✓ 修复后文档已保存至: {config.output_path}")

    return SUCCESS


def mode_auto_polish_loop(config: LoopConfig) -> int:
    """
    模式 3: auto-polish-loop
    多轮循环（Codex 审查 → Claude 修复），直到无 P0/P1 或 max_rounds

    Args:
        config: 循环配置

    Returns:
        退出码
    """
    log_mode_header("auto-polish-loop", config.doc_path, {"最大轮数": config.max_rounds})

    if not validate_paths(config.doc_path, config.codex_prompt_path):
        return ERROR_FILE_NOT_FOUND

    if not validate_output_required(config.output_path, "auto-polish-loop"):
        return ERROR_INVALID_ARGS

    # 创建工作目录
    work_dir = config.output_path.parent / f"{config.output_path.stem}_rounds"
    if not safe_mkdir(work_dir):
        return ERROR_GENERAL

    # 复制原始文档到工作目录
    original_content = safe_read_file(config.doc_path)
    if original_content is None:
        return ERROR_GENERAL

    current_doc_path = work_dir / "round_0_original.md"
    if not safe_write_file(current_doc_path, original_content):
        return ERROR_GENERAL

    # 开始循环
    for round_num in range(1, config.max_rounds + 1):
        logging.info("")
        logging.info("=" * 60)
        logging.info(f"[Round {round_num}/{config.max_rounds}]")
        logging.info("=" * 60)

        # 审查
        logging.info(f"[Round {round_num}/Step 1] 正在调用 Codex 审查...")
        review_report = invoke_codex_review(
            current_doc_path,
            config.codex_prompt_path,
            config.codex_cmd,
            config.timeout
        )

        if review_report is None:
            return ERROR_SUBPROCESS_FAILED

        review_path = work_dir / f"round_{round_num}_review.md"
        if not safe_write_file(review_path, review_report):
            return ERROR_GENERAL

        logging.info(f"  中间文件: {review_path}")

        p0_count, p1_count, is_parsed = parse_p0_p1_count(review_report)

        if not is_parsed:
            logging.warning(f"[Round {round_num}] ⚠️  无法解析审查报告中的 P0/P1 数量")
            logging.warning("  将继续循环，但无法判断是否已无缺陷")
            logging.info(f"  统计: P0 缺陷 {p0_count}个, P1 缺陷 {p1_count}个 (解析失败，可能不准确)")
        else:
            logging.info(f"  统计: P0 缺陷 {p0_count}个, P1 缺陷 {p1_count}个")

            # 只有在成功解析的情况下，才检查是否已无缺陷
            if p0_count == 0 and p1_count == 0:
                logging.info(f"[Round {round_num}] 🎉 已无 P0/P1 缺陷，磨光完成！")

                # 复制当前文档到最终输出
                current_content = safe_read_file(current_doc_path)
                if current_content is None:
                    return ERROR_GENERAL
                if not safe_write_file(config.output_path, current_content):
                    return ERROR_GENERAL

                logging.info(f"✓ 最终文档已保存至: {config.output_path}")
                logging.info(f"  总轮数: {round_num}/{config.max_rounds} 轮")
                return SUCCESS

        # 修复
        logging.info(f"[Round {round_num}/Step 2] 正在调用 Claude 修复...")
        fixed_doc = invoke_claude_fix(
            current_doc_path,
            review_path,
            config.skill_name,
            config.claude_cmd,
            config.timeout
        )

        if fixed_doc is None:
            logging.error(f"[Round {round_num}] ✗ Claude 修复失败")
            return ERROR_SUBPROCESS_FAILED

        # 检查 Claude 是否返回空文档（可能是修复失败）
        if not fixed_doc.strip():
            logging.error(f"[Round {round_num}] ✗ Claude 返回了空文档，修复失败")
            logging.error("  建议检查审查报告格式或 Claude Skill 配置")
            return ERROR_SUBPROCESS_FAILED

        # 检查文档是否过短（可能是部分内容）
        if len(fixed_doc.strip()) < len(original_content) * 0.5:
            logging.warning(f"[Round {round_num}] ⚠️  修复后文档长度仅为原文档的 {len(fixed_doc)/len(original_content)*100:.1f}%")
            logging.warning("  可能是 Claude 只返回了部分内容，将仍然保存该结果")

        fixed_doc_path = work_dir / f"round_{round_num}_fixed.md"
        if not safe_write_file(fixed_doc_path, fixed_doc):
            return ERROR_GENERAL

        logging.info(f"  中间文件: {fixed_doc_path}")

        # 更新当前文档路径
        current_doc_path = fixed_doc_path

    # 达到最大轮数，进行最终确认审查
    logging.warning("")
    logging.warning(f"⚠️  已达到最大轮数 {config.max_rounds}")
    logging.info("正在进行最终确认审查...")

    final_review = invoke_codex_review(
        current_doc_path,
        config.codex_prompt_path,
        config.codex_cmd,
        config.timeout
    )

    if final_review is not None:
        final_review_path = work_dir / "final_review.md"
        safe_write_file(final_review_path, final_review)

        final_p0, final_p1, final_parsed = parse_p0_p1_count(final_review)
        if not final_parsed:
            logging.warning("⚠️  最终审查: 无法解析 P0/P1 数量")
        logging.warning(f"最终统计: P0 缺陷 {final_p0}个, P1 缺陷 {final_p1}个")

        if final_p0 > 0 or final_p1 > 0:
            logging.warning("建议增加 --max-rounds 或手动检查文档")

    # 保存最后一轮的结果
    final_content = safe_read_file(current_doc_path)
    if final_content is None:
        return ERROR_GENERAL
    if not safe_write_file(config.output_path, final_content):
        return ERROR_GENERAL

    logging.info(f"✓ 最终文档已保存至: {config.output_path}")

    return SUCCESS


def mode_quick_check(config: ReviewConfig) -> int:
    """
    模式 4: quick-check
    快速检测是否存在 P0/P1，无需输出完整报告

    Args:
        config: 审查配置

    Returns:
        退出码 (0 = 无 P0/P1, 1 = 有 P0/P1 或错误)
    """
    log_mode_header("quick-check", config.doc_path)

    if not validate_paths(config.doc_path, config.codex_prompt_path):
        return ERROR_FILE_NOT_FOUND

    logging.info("正在调用 Codex 进行快速检测...")
    review_report = invoke_codex_review(
        config.doc_path,
        config.codex_prompt_path,
        config.codex_cmd,
        config.timeout
    )

    if review_report is None:
        return ERROR_SUBPROCESS_FAILED

    p0_count, p1_count, is_parsed = parse_p0_p1_count(review_report)

    if not is_parsed:
        error_msg = "❌ 无法解析审查报告中的 P0/P1 数量，请手动检查报告内容"
        logging.error(error_msg)
        print(error_msg)
        return ERROR_GENERAL

    # 输出统计结果（同时到 logging 和 stdout）
    result_msg = f"📊 Quick Check 结果: P0={p0_count}, P1={p1_count}"
    logging.info(result_msg)
    print(result_msg)

    if p0_count == 0 and p1_count == 0:
        success_msg = "✓ 文档质量良好，无 P0/P1 缺陷"
        logging.info(success_msg)
        print(success_msg)
        return SUCCESS
    else:
        warning_msg = f"⚠️  发现 {p0_count} 个 P0 缺陷和 {p1_count} 个 P1 缺陷，需要修复"
        logging.warning(warning_msg)
        print(warning_msg)
        return ERROR_GENERAL


def validate_args(args: argparse.Namespace) -> bool:
    """
    验证命令行参数

    Args:
        args: 解析后的参数

    Returns:
        True 如果参数有效
    """
    # 验证 max_rounds
    if hasattr(args, 'max_rounds') and args.max_rounds <= 0:
        logging.error(f"--max-rounds 必须 > 0，当前值: {args.max_rounds}")
        return False

    # 验证 timeout
    if hasattr(args, 'timeout') and args.timeout <= 0:
        logging.error(f"--timeout 必须 > 0，当前值: {args.timeout}")
        return False

    return True


def main() -> int:
    """主函数：CLI 入口"""
    parser = argparse.ArgumentParser(
        description="Super Review Agent - 超级文档自动审查系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 只审查，不修复
  %(prog)s review-only --doc docs/API.md --codex-prompt prompts/reviewer.txt --output tmp/review.md

  # 审查 + 修复一次
  %(prog)s fix-once --doc docs/API.md --codex-prompt prompts/reviewer.txt --skill-name doc-fixer-claude --output tmp/fixed.md

  # 自动循环磨光（最多 5 轮）
  %(prog)s auto-polish-loop --doc docs/API.md --codex-prompt prompts/reviewer.txt --skill-name doc-fixer-claude --max-rounds 5 --output tmp/polished.md --verbose

  # 快速检测
  %(prog)s quick-check --doc docs/API.md --codex-prompt prompts/reviewer.txt
        """
    )

    subparsers = parser.add_subparsers(dest="mode", help="运行模式")

    # ========== review-only ==========
    parser_review = subparsers.add_parser(
        "review-only",
        help="只调用 Codex，生成审查报告"
    )
    parser_review.add_argument("--doc", required=True, help="待审查文档的路径")
    parser_review.add_argument("--codex-prompt", required=True, help="Codex 审查 prompt 文件路径")
    parser_review.add_argument("--codex-cmd", default=DEFAULT_CODEX_CMD, help=f"Codex 命令 (默认: {DEFAULT_CODEX_CMD})")
    parser_review.add_argument("--output", required=True, help="审查报告输出路径")
    parser_review.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"命令超时时间（秒，默认: {DEFAULT_TIMEOUT}）")
    parser_review.add_argument("--verbose", action="store_true", help="启用详细日志")

    # ========== fix-once ==========
    parser_fix = subparsers.add_parser(
        "fix-once",
        help="Codex 审查 + Claude 修一次"
    )
    parser_fix.add_argument("--doc", required=True, help="待审查文档的路径")
    parser_fix.add_argument("--codex-prompt", required=True, help="Codex 审查 prompt 文件路径")
    parser_fix.add_argument("--codex-cmd", default=DEFAULT_CODEX_CMD, help=f"Codex 命令 (默认: {DEFAULT_CODEX_CMD})")
    parser_fix.add_argument("--claude-cmd", default=DEFAULT_CLAUDE_CMD, help=f"Claude 命令 (默认: {DEFAULT_CLAUDE_CMD})")
    parser_fix.add_argument("--skill-name", required=True, help="Claude Skill 名称")
    parser_fix.add_argument("--output", required=True, help="修复后文档输出路径")
    parser_fix.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"命令超时时间（秒，默认: {DEFAULT_TIMEOUT}）")
    parser_fix.add_argument("--verbose", action="store_true", help="启用详细日志")

    # ========== auto-polish-loop ==========
    parser_loop = subparsers.add_parser(
        "auto-polish-loop",
        help="多轮循环，直到无 P0/P1 或 max_rounds"
    )
    parser_loop.add_argument("--doc", required=True, help="待审查文档的路径")
    parser_loop.add_argument("--codex-prompt", required=True, help="Codex 审查 prompt 文件路径")
    parser_loop.add_argument("--codex-cmd", default=DEFAULT_CODEX_CMD, help=f"Codex 命令 (默认: {DEFAULT_CODEX_CMD})")
    parser_loop.add_argument("--claude-cmd", default=DEFAULT_CLAUDE_CMD, help=f"Claude 命令 (默认: {DEFAULT_CLAUDE_CMD})")
    parser_loop.add_argument("--skill-name", required=True, help="Claude Skill 名称")
    parser_loop.add_argument("--max-rounds", type=int, default=DEFAULT_MAX_ROUNDS, help=f"最大循环轮数 (默认: {DEFAULT_MAX_ROUNDS})")
    parser_loop.add_argument("--output", required=True, help="最终文档输出路径")
    parser_loop.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"命令超时时间（秒，默认: {DEFAULT_TIMEOUT}）")
    parser_loop.add_argument("--verbose", action="store_true", help="启用详细日志")

    # ========== quick-check ==========
    parser_check = subparsers.add_parser(
        "quick-check",
        help="快速检测是否存在 P0/P1"
    )
    parser_check.add_argument("--doc", required=True, help="待审查文档的路径")
    parser_check.add_argument("--codex-prompt", required=True, help="Codex 审查 prompt 文件路径")
    parser_check.add_argument("--codex-cmd", default=DEFAULT_CODEX_CMD, help=f"Codex 命令 (默认: {DEFAULT_CODEX_CMD})")
    parser_check.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"命令超时时间（秒，默认: {DEFAULT_TIMEOUT}）")
    parser_check.add_argument("--verbose", action="store_true", help="启用详细日志")

    args = parser.parse_args()

    if not args.mode:
        parser.print_help()
        return ERROR_INVALID_ARGS

    # 设置日志
    setup_logging(getattr(args, 'verbose', False))

    # 验证参数
    if not validate_args(args):
        return ERROR_INVALID_ARGS

    # 路由到对应模式
    try:
        if args.mode == "review-only":
            config = ReviewConfig(
                doc_path=Path(args.doc),
                codex_prompt_path=Path(args.codex_prompt),
                codex_cmd=args.codex_cmd,
                output_path=Path(args.output),
                timeout=args.timeout,
                verbose=args.verbose
            )
            return mode_review_only(config)

        elif args.mode == "fix-once":
            config = FixConfig(
                doc_path=Path(args.doc),
                codex_prompt_path=Path(args.codex_prompt),
                codex_cmd=args.codex_cmd,
                output_path=Path(args.output),
                timeout=args.timeout,
                verbose=args.verbose,
                claude_cmd=args.claude_cmd,
                skill_name=args.skill_name
            )
            return mode_fix_once(config)

        elif args.mode == "auto-polish-loop":
            config = LoopConfig(
                doc_path=Path(args.doc),
                codex_prompt_path=Path(args.codex_prompt),
                codex_cmd=args.codex_cmd,
                output_path=Path(args.output),
                timeout=args.timeout,
                verbose=args.verbose,
                claude_cmd=args.claude_cmd,
                skill_name=args.skill_name,
                max_rounds=args.max_rounds
            )
            return mode_auto_polish_loop(config)

        elif args.mode == "quick-check":
            config = ReviewConfig(
                doc_path=Path(args.doc),
                codex_prompt_path=Path(args.codex_prompt),
                codex_cmd=args.codex_cmd,
                output_path=None,  # quick-check 不需要 output
                timeout=args.timeout,
                verbose=args.verbose
            )
            return mode_quick_check(config)

        else:
            logging.error(f"未知模式: {args.mode}")
            return ERROR_INVALID_ARGS

    except KeyboardInterrupt:
        logging.warning("\n用户中断操作")
        return ERROR_GENERAL
    except Exception as e:
        logging.error(f"未预期的错误: {str(e)}")
        if getattr(args, 'verbose', False):
            import traceback
            traceback.print_exc()
        return ERROR_GENERAL


if __name__ == "__main__":
    sys.exit(main())
