import json
import os
from typing import Optional
from langchain.tools import tool, ToolRuntime


@tool
def query_features(
    keyword: Optional[str] = None,
    theme: Optional[str] = None,
    timeliness: Optional[str] = None,
    runtime: ToolRuntime = None
) -> str:
    """
    查询特征知识库中的特征信息。
    可以根据关键词（匹配字段名称、字段中文、特征描述）和主题、时效性进行筛选。
    返回匹配的特征列表，每个特征包含字段名称、字段中文、特征描述和SQL逻辑。
    
    Args:
        keyword: 搜索关键词，匹配字段名称、字段中文、特征描述等字段
        theme: 特征主题，如 '用户'、'招工'等
        timeliness: 时效性，如 '实时'、'离线'
        runtime: LangChain 工具运行时，用于获取上下文
    
    Returns:
        str: 格式化后的特征信息字符串
    """
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    features_path = os.path.join(workspace_path, "assets/features.json")
    
    if not os.path.exists(features_path):
        return f"特征文件不存在: {features_path}"
    
    try:
        with open(features_path, 'r', encoding='utf-8') as f:
            features = json.load(f)
    except Exception as e:
        return f"读取特征文件失败: {str(e)}"
    
    # 筛选特征
    filtered = []
    for feat in features:
        if theme and feat.get('主题') != theme:
            continue
        if timeliness and feat.get('时效性') != timeliness:
            continue
        if keyword:
            # 在多个字段中搜索关键词
            search_fields = [
                feat.get('字段名称', ''),
                feat.get('字段中文', ''),
                feat.get('特征描述', '')
            ]
            keyword_lower = keyword.lower()
            matched = any(keyword_lower in field.lower() for field in search_fields if field)
            if not matched:
                continue
        filtered.append(feat)
    
    if not filtered:
        return "未找到匹配的特征。"
    
    # 格式化输出
    result_lines = []
    result_lines.append(f"找到 {len(filtered)} 个匹配的特征：")
    result_lines.append("")
    
    for feat in filtered:
        result_lines.append(f"【{feat.get('字段中文', '')}】")
        result_lines.append(f"字段名称: {feat.get('字段名称', '')}")
        result_lines.append(f"主题: {feat.get('主题', '')}")
        result_lines.append(f"时效性: {feat.get('时效性', '')}")
        result_lines.append(f"特征描述: {feat.get('特征描述', '')}")
        sql_logic = feat.get('涉及sql逻辑', '')
        if sql_logic:
            result_lines.append(f"SQL逻辑: {sql_logic}")
        else:
            result_lines.append("SQL逻辑: 暂无")
        result_lines.append("")
    
    return "\n".join(result_lines)