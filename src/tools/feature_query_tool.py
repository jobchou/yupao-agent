import json
import os
from typing import Optional
from langchain.tools import tool, ToolRuntime


@tool
def query_features(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    runtime: ToolRuntime = None
) -> str:
    """
    查询特征知识库中的特征信息。
    可以根据关键词（匹配中文名称、定义、标签）和类别进行筛选。
    返回匹配的特征列表，每个特征包含中文名称、定义和SQL逻辑。
    
    Args:
        keyword: 搜索关键词，匹配中文名称、定义、标签等字段
        category: 特征类别，如 '行为特征'、'交易特征'、'属性特征'
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
        if category and feat.get('category') != category:
            continue
        if keyword:
            # 在多个字段中搜索关键词
            search_fields = [
                feat.get('chinese_name', ''),
                feat.get('definition', ''),
                feat.get('english_name', ''),
                ' '.join(feat.get('tags', []))
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
    for feat in filtered:
        result_lines.append(f"【{feat.get('chinese_name')}】")
        result_lines.append(f"英文名: {feat.get('english_name')}")
        result_lines.append(f"定义: {feat.get('definition')}")
        result_lines.append(f"SQL逻辑: {feat.get('sql_logic')}")
        result_lines.append(f"类别: {feat.get('category')}")
        result_lines.append(f"标签: {', '.join(feat.get('tags', []))}")
        result_lines.append("")
    
    return "\n".join(result_lines)