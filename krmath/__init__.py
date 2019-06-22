from redbot.core.bot import Red

from .krmath import KRMath


def setup(bot: Red):
    krmath = KRMath(bot)
    bot.add_cog(krmath)
