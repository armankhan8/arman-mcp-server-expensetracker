from asyncio import transports
from fastmcp import FastMCP
import random

mcp = FastMCP(name="")

@mcp.tool()
def rolling_dice(sides: int = 6) -> list[int]:
    """Roll a dice with a given number of sides"""
    return [random.randint(1, sides) for _ in range(6)]

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=3001)
