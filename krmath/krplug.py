import asyncio
import concurrent.futures
from typing import Any
import re
import time

from py_expression_eval import Parser
import discord
from redbot.core import Config, checks, commands
from redbot.core.bot import Red


Cog: Any = getattr(commands, "Cog", object)
parser = Parser()


class KRMath(Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command(name="calc")
    async def calc(self, ctx: commands.Context, *, expr):
        """
        General calculator command `%calc 1+1`, 
        see: https://github.com/Axiacore/py-expression-eval 
        for a full list of what you can do
        """
        try:
            result = await asyncio.wait_for(a_parse(expr), timeout=1)
            ctx.send(result)
        except asyncio.TimeoutError:
            print("Calculation timeout.")
        except:
            print("Calculation error.")

    async def a_parse(self, expr):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, parse, expr)
        return result

    def parse(self, expr):
        return parser.parse(expr).evaluate({})
