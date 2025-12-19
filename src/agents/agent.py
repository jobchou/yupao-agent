import os
import json
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from coze_coding_utils.runtime_ctx.context import default_headers
from utils.helper.graph_helper import is_dev_env

# 导入工具
from tools.feature_query_tool import query_features
from tools.database_query_tool import query_database
from tools.report_understanding_tool import understand_report

LLM_CONFIG = "config/agent_llm_config.json"

in_memory_checkpointer = None

# 开发环境默认使用内存记忆, 生产环境默认无记忆
if is_dev_env():
    in_memory_checkpointer = MemorySaver()


def build_agent(ctx=None):
    """
    构建并返回鱼泡科技数产助手Agent。
    
    Args:
        ctx: 运行时上下文，用于传递默认请求头
    
    Returns:
        Agent实例
    """
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    
    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
    
    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )
    
    # 工具列表
    tools = [query_features, query_database, understand_report]
    
    global in_memory_checkpointer
    agent = create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=tools,
        checkpointer=in_memory_checkpointer
    )
    
    return agent