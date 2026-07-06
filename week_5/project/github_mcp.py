from mcp.server.fastmcp import FastMCP
from github import Github
import os
import sys

# Initialize FastMCP server
mcp = FastMCP("GitHub-Python-Server")

# Validate token immediately
token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
if not token:
    print("CRITICAL: GITHUB_PERSONAL_ACCESS_TOKEN not found", file=sys.stderr)
    sys.exit(1)

g = Github(token)

@mcp.tool()
def list_my_repos():
    """List all your GitHub repositories."""
    try:
        repos = [repo.name for repo in g.get_user().get_repos()]
        return {"repos": repos}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run()