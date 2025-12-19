import json
import os
from typing import Optional
from langchain.tools import tool, ToolRuntime


@tool
def query_features(
    keyword: Optional[str] = None,
    theme: Optional[str] = None,
    timeliness: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = 0,
    runtime: ToolRuntime = None
) -> str:
    """
    查询特征知识库中的特征信息。
    
    支持以下筛选方式：
    1. 关键词搜索：支持空格分隔的多个关键词，在所有字段（字段名称、字段中文、特征描述、SQL逻辑）中搜索，要求所有关键词都匹配（AND逻辑）。
    2. 主题筛选：支持逗号分隔的多个主题（如 '用户,招工'），匹配任意一个主题即可（OR逻辑）。
    3. 时效性筛选：支持逗号分隔的多个时效性（如 '实时,离线'），匹配任意一个时效性即可（OR逻辑）。
    4. 分页：通过limit和offset控制返回结果数量，避免数据过多。
    
    Args:
        keyword: 搜索关键词，空格分隔多个关键词，如 "登录 时间"
        theme: 主题筛选，逗号分隔多个主题，如 "用户,招工"
        timeliness: 时效性筛选，逗号分隔多个时效性，如 "实时,离线"
        limit: 返回的最大特征数量，默认返回所有匹配结果
        offset: 跳过的特征数量，用于分页
        runtime: LangChain 工具运行时，用于获取上下文
    
    Returns:
        str: 格式化后的特征信息字符串，包含匹配数量、分页信息和特征详情
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
    
    # 处理多值参数
    keyword_list = []
    if keyword:
        # 分割空格，去除空字符串
        keyword_list = [k.strip() for k in keyword.split() if k.strip()]
    
    theme_list = []
    if theme:
        # 分割逗号，去除空格
        theme_list = [t.strip() for t in theme.split(',') if t.strip()]
    
    timeliness_list = []
    if timeliness:
        timeliness_list = [tl.strip() for tl in timeliness.split(',') if tl.strip()]
    
    # 筛选特征
    filtered = []
    for feat in features:
        # 主题筛选
        if theme_list:
            feat_theme = feat.get('主题', '')
            if not any(t == feat_theme for t in theme_list):
                continue
        
        # 时效性筛选
        if timeliness_list:
            feat_timeliness = feat.get('时效性', '')
            if not any(tl == feat_timeliness for tl in timeliness_list):
                continue
        
        # 关键词筛选
        if keyword_list:
            # 搜索字段包括所有文本字段
            search_fields = [
                feat.get('字段名称', ''),
                feat.get('字段中文', ''),
                feat.get('特征描述', ''),
                feat.get('涉及sql逻辑', '')
            ]
            # 检查所有关键词是否都在某个字段中出现（AND逻辑）
            # 我们要求每个关键词至少在一个字段中出现（跨字段）
            matched_all = True
            for kw in keyword_list:
                kw_lower = kw.lower()
                # 检查关键词是否在任何字段中出现
                kw_matched = any(kw_lower in field.lower() for field in search_fields if field)
                if not kw_matched:
                    matched_all = False
                    break
            if not matched_all:
                continue
        
        filtered.append(feat)
    
    # 排序：按字段名称字母顺序
    filtered.sort(key=lambda x: x.get('字段名称', '').lower())
    
    # 分页
    total = len(filtered)
    if offset > 0:
        filtered = filtered[offset:]
    if limit is not None:
        filtered = filtered[:limit]
    
    if not filtered:
        return "未找到匹配的特征。"
    
    # 格式化输出
    result_lines = []
    result_lines.append(f"找到 {total} 个匹配的特征（显示 {len(filtered)} 个）：")
    if offset > 0 or (limit is not None and limit < total):
        result_lines.append(f"分页：偏移量 {offset}，限制 {limit if limit is not None else '无'}")
    result_lines.append("")
    
    for idx, feat in enumerate(filtered, 1):
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