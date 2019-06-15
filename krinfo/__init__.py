from redbot.core.bot import Red

from .krinfo import KRInfo


def setup(bot: Red):
    krinfo = KRInfo(bot)
    bot.add_cog(krinfo)
