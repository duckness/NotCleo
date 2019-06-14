from redbot.core.bot import Red

from .krplug import KRPlug


def setup(bot: Red):
    krplug = KRPlug(bot)
    bot.add_cog(krplug)
    bot.loop.create_task(krplug.check_plug())
