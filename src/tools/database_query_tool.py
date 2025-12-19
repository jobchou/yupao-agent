from typing import Optional
from langchain.tools import tool, ToolRuntime
from storage.database.query_manager import QueryManager, QueryRequest
from storage.database.db import get_session


@tool
def query_database(
    sql: str,
    limit: Optional[int] = 100,
    runtime: ToolRuntime = None
) -> str:
    """
    执行SQL查询，返回查询结果。
    仅支持SELECT查询，确保数据安全。
    
    Args:
        sql: SQL查询语句（必须为SELECT）
        limit: 返回结果行数限制，默认100
        runtime: LangChain工具运行时
    
    Returns:
        str: 格式化后的查询结果，包含列名和数据行
    """
    db = get_session()
    try:
        manager = QueryManager()
        request = QueryRequest(sql=sql, limit=limit)
        result = manager.execute_query(db, request)
        
        if result.row_count == 0:
            return "查询成功，但未返回任何数据。"
        
        # 格式化输出
        lines = []
        lines.append(f"查询成功，返回 {result.row_count} 行数据：")
        lines.append("列名: " + ", ".join(result.columns))
        lines.append("数据:")
        for i, row in enumerate(result.rows, 1):
            # 将每个值转换为字符串，避免None
            row_str = [str(val) if val is not None else "NULL" for val in row]
            lines.append(f"  {i}. {row_str}")
        
        return "\n".join(lines)
    except ValueError as e:
        return f"查询失败: {str(e)}"
    except Exception as e:
        return f"数据库错误: {str(e)}"
    finally:
        db.close()