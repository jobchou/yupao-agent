import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """SQL查询请求模型"""
    sql: str = Field(..., description="要执行的SQL查询语句（只读，仅支持SELECT）")
    limit: Optional[int] = Field(100, description="返回结果行数限制，默认100")


class QueryResult(BaseModel):
    """SQL查询结果模型"""
    columns: List[str]
    rows: List[List[Any]]
    row_count: int


class QueryManager:
    """数据库查询管理器，提供安全的只读查询能力"""
    
    def execute_query(self, db: Session, request: QueryRequest) -> QueryResult:
        """
        执行SQL查询，返回结果。
        仅允许SELECT查询，防止数据修改。
        
        Args:
            db: 数据库会话
            request: 查询请求
            
        Returns:
            QueryResult: 查询结果
            
        Raises:
            ValueError: 如果SQL不是SELECT查询或格式错误
        """
        sql = request.sql.strip()
        
        # 安全性检查：只允许SELECT查询（忽略大小写，允许前后空白和注释）
        # 简单的检查，防止明显的非SELECT语句
        sql_upper = sql.upper()
        # 去除常见注释和多余空白
        sql_upper = re.sub(r'--.*?\n', ' ', sql_upper)
        sql_upper = re.sub(r'/\*.*?\*/', ' ', sql_upper, flags=re.DOTALL)
        sql_upper = re.sub(r'\s+', ' ', sql_upper).strip()
        
        if not sql_upper.startswith('SELECT'):
            raise ValueError("只允许执行SELECT查询，请检查SQL语句。")
        
        # 可选：添加LIMIT子句如果不存在且用户指定了limit
        # 但为了简单，我们直接执行用户SQL，然后截断结果
        try:
            result = db.execute(text(sql))
            columns = list(result.keys())
            rows = result.fetchall()
            
            # 应用行数限制
            if request.limit and len(rows) > request.limit:
                rows = rows[:request.limit]
            
            # 将行转换为列表
            rows_list = [list(row) for row in rows]
            
            return QueryResult(
                columns=columns,
                rows=rows_list,
                row_count=len(rows_list)
            )
        except Exception as e:
            # 将数据库异常转换为用户友好信息
            raise ValueError(f"SQL执行失败: {str(e)}")
        finally:
            db.close()