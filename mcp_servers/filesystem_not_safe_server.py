# echo.py
import mimetypes

from mcp.server.fastmcp import FastMCP
from pathlib import Path

mcp = FastMCP(name="FileSystemServer", stateless_http=True)


@mcp.tool(description="读取本地文件列表的tool")
def read_file() -> str:
    """获取文件资源列表"""
    files = []
    ROOT_PATH = 'D:\\test-mcp'
    root_path = Path(ROOT_PATH)

    # 检查根目录是否存在，如果不存在则抛出文件未找到错误
    if not root_path.exists():
        raise FileNotFoundError(f"搜索目标目录不存在: {ROOT_PATH}")

    # 递归遍历根目录下的所有文件
    for file_path in root_path.rglob('*'):
        if file_path.is_file():
            try:
                # 获取文件相对于根目录的相对路径
                rel_path = file_path.relative_to(root_path)
                # 对相对路径进行规范化处理，将反斜杠替换为正斜杠
                normalized_path = str(rel_path).replace("\\", "/")
                # 猜测文件的MIME类型
                mime_type, _ = mimetypes.guess_type(str(file_path))

                # 将文件信息添加到文件列表中
                files.append({
                    "uri": f"file:///{normalized_path}",
                    "name": file_path.name,
                    "mimeType": mime_type or "application/octet-stream"
                })
            except Exception as e:
                # 记录文件处理过程中的错误信息
                print(f"文件处理时出错: {file_path.name} - {str(e)}")
                continue

    print(files)

    return files