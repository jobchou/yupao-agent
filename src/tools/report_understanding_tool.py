import os
import pandas as pd
from typing import Optional
from langchain.tools import tool, ToolRuntime


@tool
def understand_report(
    file_path: str,
    sample_rows: Optional[int] = 5,
    runtime: ToolRuntime = None
) -> str:
    """
    读取报表文件（CSV或Excel），理解其结构和内容。
    返回列名、行数、数据类型和示例数据。
    
    Args:
        file_path: 报表文件路径（相对于工作空间根目录或绝对路径）
        sample_rows: 返回的示例数据行数，默认5
        runtime: LangChain工具运行时
    
    Returns:
        str: 报表的结构化描述
    """
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    full_path = os.path.join(workspace_path, file_path)
    
    if not os.path.exists(full_path):
        return f"报表文件不存在: {full_path}"
    
    # 根据扩展名选择读取方式
    ext = os.path.splitext(full_path)[1].lower()
    
    try:
        if ext == '.csv':
            df = pd.read_csv(full_path)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(full_path)
        elif ext == '.json':
            df = pd.read_json(full_path)
        else:
            return f"不支持的文件格式: {ext}。请使用 CSV、Excel 或 JSON 格式。"
    except Exception as e:
        return f"读取报表文件失败: {str(e)}"
    
    # 构建描述
    lines = []
    lines.append(f"报表文件: {file_path}")
    lines.append(f"总行数: {len(df)}")
    lines.append(f"总列数: {len(df.columns)}")
    lines.append("")
    lines.append("列信息:")
    for i, col in enumerate(df.columns, 1):
        dtype = str(df[col].dtype)
        non_null = df[col].count()
        lines.append(f"  {i}. {col} (类型: {dtype}, 非空值: {non_null}/{len(df)})")
    
    lines.append("")
    lines.append(f"前 {sample_rows} 行示例数据:")
    sample = df.head(sample_rows)
    # 格式化示例数据为表格
    lines.append(sample.to_string(index=False))
    
    return "\n".join(lines)