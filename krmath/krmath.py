import asyncio
import concurrent.futures
from typing import Any
import re
import time
import math

from beautifultable import BeautifulTable
from py_expression_eval import Parser
import discord
from redbot.core import Config, checks, commands
from redbot.core.bot import Red


Cog: Any = getattr(commands, "Cog", object)


class KRMath(Cog):
    parser = Parser()
    softcaps = {
        "crit": {
            "MaxK": 2000,
            "X1": 2000,
            "A1": 1,
            "B1": 1500,
            "X2": 1500,
            "A2": 500,
            "B2": 750,
            "MinK": 0,
            "X3": -500,
            "A3": 0,
            "B3": 0,
            "X4": 0,
            "A4": 0,
            "B4": 0
        },
        "acc": {
            "MaxK": 2000,
            "X1": 2000,
            "A1": 1,
            "B1": 1500,
            "X2": 1500,
            "A2": 500,
            "B2": 750,
            "MinK": -920,
            "X3": -2,
            "A3": 3,
            "B3": -938,
            "X4": 1,
            "A4": 0,
            "B4": 0
        },
        "ccacc": {
            "MaxK": 900,
            "X1": 900,
            "A1": 1000000,
            "B1": 1000000,
            "X2": 450,
            "A2": 1000,
            "B2": 0,
            "MinK": 0,
            "X3": -500,
            "A3": 0,
            "B3": 0,
            "X4": 0,
            "A4": 0,
            "B4": 0
        },
        "dodge": {
            "MaxK": 1000,
            "X1": 1000,
            "A1": 3,
            "B1": 0,
            "X2": 500,
            "A2": 500,
            "B2": 250,
            "MinK": 0,
            "X3": -500,
            "A3": 0,
            "B3": 0,
            "X4": 0,
            "A4": 0,
            "B4": 0
        },
        "critresist": {
            "MaxK": 1000,
            "X1": 1000,
            "A1": 3,
            "B1": 0,
            "X2": 500,
            "A2": 500,
            "B2": 250,
            "MinK": 0,
            "X3": -500,
            "A3": 0,
            "B3": 0,
            "X4": 0,
            "A4": 0,
            "B4": 0
        },
        "ccresist": {
            "MaxK": 1000,
            "X1": 1000,
            "A1": 1000000,
            "B1": 1000000,
            "X2": 500,
            "A2": 1000,
            "B2": 0,
            "MinK": 0,
            "X3": -500,
            "A3": 0,
            "B3": 0,
            "X4": 0,
            "A4": 0,
            "B4": 0
        },
        "pen": {
            "MaxK": 900,
            "X1": 1000,
            "A1": 2,
            "B1": 1000,
            "X2": 450,
            "A2": 409,
            "B2": 266,
            "MinK": 0,
            "X3": -500,
            "A3": 0,
            "B3": 0,
            "X4": 0,
            "A4": 0,
            "B4": 0
        },
        "aspd": {
            "MaxK": 2500,
            "X1": 2400,
            "A1": 1,
            "B1": -733,
            "X2": 1600,
            "A2": 500,
            "B2": 800,
            "MinK": 250,
            "X3": -10000,
            "A3": 0,
            "B3": 0,
            "X4": 500,
            "A4": 1,
            "B4": -1500
        },
        "blockdef": {
            "MaxK": 450,
            "X1": 775,
            "A1": 3,
            "B1": 1500,
            "X2": 225,
            "A2": 204,
            "B2": 179,
            "MinK": -920,
            "X3": -2,
            "A3": 3,
            "B3": -938,
            "X4": -1,
            "A4": 0,
            "B4": 0
        },
        "mpatk": {
            "MaxK": 2300,
            "X1": 2400,
            "A1": 1,
            "B1": -900,
            "X2": 1200,
            "A2": 500,
            "B2": 600,
            "MinK": 0,
            "X3": -500,
            "A3": 0,
            "B3": 0,
            "X4": 0,
            "A4": 0,
            "B4": 0
        }
    }

    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command(name="calc")
    async def calc(self, ctx: commands.Context, *, expr):
        """
        General calculator command `%calc 1+1`,
        see: https://github.com/Axiacore/py-expression-eval
        for a full list of what you can do.
        Will result in an error if an invalid expression or
        an expensive computation is performed.
        """
        try:
            result = await asyncio.wait_for(self.a_parse(expr.replace("`", "")), timeout=1)
            await ctx.send(result)
        except:
            await ctx.send("Calculation error.")

    @commands.command(name="softcap")
    async def softcap(self, ctx: commands.Context, val):
        """
        Softcap command `%softcap 1000`,
        """
        await ctx.send(self.sc_table(int(val)))

    async def a_parse(self, expr):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, self.parse, expr)
        return result

    def parse(self, expr):
        return self.parser.parse(expr).evaluate({})

    def sc_table(self, val):
        table = BeautifulTable()
        table.column_headers = ["Stat Name", "1st Softcap", "Capped Value"]
        table.column_alignments['Stat Name'] = BeautifulTable.ALIGN_LEFT
        table.column_alignments['1st Softcap'] = BeautifulTable.ALIGN_RIGHT
        table.column_alignments['Capped Value'] = BeautifulTable.ALIGN_RIGHT
        table.set_style(BeautifulTable.STYLE_BOX)

        table.append_row(["Crit", str(self.softcaps["crit"]["X2"]),
                          self.actualStat(self.softcaps["crit"], val)])
        table.append_row(["Accuracy", str(self.softcaps["acc"]["X2"]), self.actualStat(
            self.softcaps["acc"], val)])
        table.append_row(["Dodge, Block, Lifesteal", str(self.softcaps["dodge"]["X2"]), self.actualStat(
            self.softcaps["dodge"], val)])
        table.append_row(["Crit Resist", str(self.softcaps["critresist"]["X2"]), self.actualStat(
            self.softcaps["critresist"], val)])
        table.append_row(["Penetration, Tough", str(self.softcaps["pen"]["X2"]), self.actualStat(
            self.softcaps["pen"], val)])
        table.append_row(["CC ACC", "No Softcap", self.actualStat(
            self.softcaps["ccacc"], val)])
        table.append_row(["CC Resist", "No Softcap", self.actualStat(
            self.softcaps["ccresist"], val)])
        table.append_row(["Attack speed", str(self.softcaps["aspd"]["X2"]), self.actualStat(
            self.softcaps["aspd"], val)])
        table.append_row(["Block DEF", str(self.softcaps["blockdef"]["X2"]), self.actualStat(
            self.softcaps["blockdef"], val)])
        table.append_row(["Mp/Atk", str(self.softcaps["mpatk"]["X2"]),
                          self.actualStat(self.softcaps["mpatk"], val)])

        return "```\n" + str(table) + "\n```"

    def actualStat(self, statType, istat):
        actual = 0
        # variable names are fucked cause vespa
        if istat == 0:
            actual = 0
        # 2nd upper softcap
        elif istat > statType["X1"]:
            actual = self.attenuateInv(
                istat, statType["MaxK"], statType["A1"], statType["B1"])
        # 1st upper softcap
        elif istat > statType["X2"]:
            actual = math.floor(
                (istat * statType["A2"]) / 1000) + statType["B2"]
        # 2nd lower softcap
        elif istat < statType["X3"]:
            actual = self.attenuateInv(
                istat, statType["MinK"], statType["A3"], statType["B3"])
        # 1st lower softcap
        elif istat < statType["X4"]:
            actual = self.attenuate(
                istat, statType["MinK"], statType["A4"], statType["B4"])
        # uncapped
        else:
            actual = istat
        # return to 1 significant decimal place
        actual = round(actual) / 10
        return str(round(actual, 1)) + "%"

    def attenuate(self, x, k, a, b):
        return math.floor((k * 1000000) / (a * x * x + b * x + 1000000))

    def attenuateInv(self, x, k, a, b):
        return k - math.floor((k * 1000000) / (a * x * x + b * x + 1000000))
