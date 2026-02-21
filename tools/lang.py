"""
Language Utility — 统一语言指令注入
====================================
所有 Phase 的 LLM prompt 通过此模块获取语言指令，
避免在每个 phase 中重复定义。

Usage:
    from tools.lang import get_lang_instruction
    instruction = get_lang_instruction(data)   # data: CompanyData
"""


def get_lang_instruction(data) -> str:
    """
    根据 data.report_language 返回 LLM 语言指令。
    - "zh" → 强制中文输出
    - "en" → 空字符串 (默认英文)
    """
    if getattr(data, 'report_language', 'en') == 'zh':
        return "IMPORTANT: You MUST respond entirely in Chinese (中文). All analysis, reasoning, and conclusions must be written in Chinese."
    return ""
