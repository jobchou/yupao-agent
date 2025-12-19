import os
import pandas as pd
from typing import Optional
from langchain.tools import tool, ToolRuntime


@tool
def query_data_assets(
    query: str,
    file_path: Optional[str] = None,
    runtime: ToolRuntime = None
) -> str:
    """
    查询数据资产目录，根据用户需求推荐相关数据表、字段或指标。
    读取Excel格式的数据资产文件，根据关键词在描述、表名、字段名等文本列中搜索匹配项。
    
    Args:
        query: 用户查询关键词，描述需要哪方面的数据
        file_path: Excel文件路径，默认为assets/数据资产.xlsx
        runtime: LangChain工具运行时
    
    Returns:
        str: 格式化后的建议结果，包含匹配的数据资产信息
    """
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    
    if file_path is None:
        file_path = os.path.join(workspace_path, "assets/数据资产.xlsx")
    else:
        # 如果传入的是相对路径，则基于工作空间解析
        if not os.path.isabs(file_path):
            file_path = os.path.join(workspace_path, file_path)
    
    if not os.path.exists(file_path):
        return f"数据资产文件不存在: {file_path}\n请确保已将Excel文件上传到assets目录，或通过file_path参数指定正确路径。"
    
    try:
        # 读取Excel文件，默认读取第一个sheet
        df = pd.read_excel(file_path, dtype=str)  # 所有列作为字符串处理
        # 填充NaN为空字符串
        df = df.fillna('')
        
        if df.empty:
            return "数据资产文件为空，请检查Excel文件内容。"
        
        # 获取所有文本列（所有列都作为字符串）
        text_columns = df.columns.tolist()
        
        # 构建匹配条件：任一文本列包含查询关键词（不区分大小写）
        query_lower = query.lower()
        mask = pd.Series(False, index=df.index)
        
        for col in text_columns:
            # 确保列是字符串类型
            col_series = df[col].astype(str).str.lower()
            mask = mask | col_series.str.contains(query_lower, na=False)
        
        matched_df = df[mask]
        
        if matched_df.empty:
            return f"未找到与 '{query}' 相关的数据资产。\n\n建议：\n1. 尝试其他关键词\n2. 检查数据资产文件是否包含相关描述\n3. 查看现有数据表列表：\n{', '.join(df.iloc[:, 0].dropna().astype(str).tolist()[:10])}..."
        
        # 限制返回的行数，避免输出过长
        max_rows = 10
        if len(matched_df) > max_rows:
            matched_df = matched_df.head(max_rows)
            row_count_msg = f"找到 {len(matched_df)} 个匹配项（显示前{max_rows}个）："
        else:
            row_count_msg = f"找到 {len(matched_df)} 个匹配项："
        
        # 格式化输出
        result_lines = []
        result_lines.append(row_count_msg)
        result_lines.append("")
        
        for i, (idx, row) in enumerate(matched_df.iterrows(), 1):
            result_lines.append(f"【匹配项 {i}】")
            # 输出所有列，但隐藏空值列
            for col in text_columns:
                value = str(row[col]).strip()
                if value:
                    result_lines.append(f"{col}: {value}")
            result_lines.append("")
        
        # 添加总体建议
        result_lines.append("=== 建议 ===")
        result_lines.append(f"根据您的需求 '{query}'，推荐关注以上数据资产。")
        result_lines.append("如需更详细的信息，请提供更具体的关键词或联系数据负责人。")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"读取数据资产文件时出错: {str(e)}\n请确保Excel文件格式正确，且包含有效的sheet。"


# 可选：提供一个工具来列出所有数据资产（用于测试）
@tool
def list_data_assets(
    file_path: Optional[str] = None,
    runtime: ToolRuntime = None
) -> str:
    """
    列出数据资产文件中的所有表名或主要字段。
    
    Args:
        file_path: Excel文件路径，默认为assets/数据资产.xlsx
        runtime: LangChain工具运行时
    
    Returns:
        str: 数据资产列表
    """
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    
    if file_path is None:
        file_path = os.path.join(workspace_path, "assets/数据资产.xlsx")
    else:
        if not os.path.isabs(file_path):
            file_path = os.path.join(workspace_path, file_path)
    
    if not os.path.exists(file_path):
        return f"数据资产文件不存在: {file_path}"
    
    try:
        df = pd.read_excel(file_path, dtype=str)
        df = df.fillna('')
        
        if df.empty:
            return "数据资产文件为空。"
        
        result_lines = []
        result_lines.append(f"数据资产文件包含 {len(df)} 条记录，{len(df.columns)} 个字段。")
        result_lines.append("字段列表: " + ", ".join(df.columns.tolist()))
        result_lines.append("")
        result_lines.append("前10条记录:")
        
        for i, (idx, row) in enumerate(df.head(10).iterrows(), 1):
            result_lines.append(f"{i}. {row.iloc[0] if len(row) > 0 else 'N/A'}")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"读取数据资产文件时出错: {str(e)}"