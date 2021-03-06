import asyncio
import aiohttp
import async_timeout
from datetime import datetime, timedelta
from typing import Any
import re
import html

from bs4 import BeautifulSoup
import parsedatetime
import pytz
from tzlocal import get_localzone
import discord
from redbot.core import Config, checks, commands
from redbot.core.bot import Red


Cog: Any = getattr(commands, "Cog", object)


class KRPlug(Cog):
    URLS = ['https://www.plug.game/kingsraid/1030449/posts?menuId=1',   # Notices
            'https://www.plug.game/kingsraid/1030449/posts?menuId=9',   # Patch Note
            'https://www.plug.game/kingsraid/1030449/posts?menuId=32']  # Game Contents

    full_posts = []

    def __init__(self, bot: Red):
        self.bot = bot

        self.config = Config.get_conf(
            self, identifier=107114112108117103, force_registration=True)

        default_global = {"posts": []}
        default_guild = {"channelid": None}

        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)

    @commands.command()
    @checks.mod_or_permissions(administrator=True)
    @commands.guild_only()
    async def setannounce(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """
        Set the announcement channel for the server `%setannounce <#channel_name>`
        Leave it blank to unset `%setannounce`
        """
        if channel is not None:
            await self.config.guild(ctx.guild).channelid.set(channel.id)
            await ctx.send("Announcement channel has been set to {}".format(channel.mention))
        else:
            await self.config.guild(ctx.guild).channelid.set(None)
            await ctx.send("Announcement channel has been cleared")

    @commands.command()
    @commands.guild_only()
    async def lastannounce(self, ctx: commands.Context):
        """
        Sends the last announcement `%lastannounce`
        """
        await self.check_plug()
        post_ids = await self.config.posts()
        post_id = str(post_ids[0])
        if post_id in self.full_posts:
            await ctx.send(embed=self.get_embed(self.full_posts[post_id]))
        else:
            await ctx.send("Error, cannot find post for some reason.")

    @commands.command()
    @commands.is_owner()
    async def forceannounce(self, ctx: commands.Context):
        """
        Force announce the last announcement `%forceannounce`
        """
        post_ids = await self.config.posts()
        post_id = str(post_ids[0])
        if post_id in self.full_posts:
            await self.send_announcements([self.full_posts[post_id]])
        else:
            await ctx.send("Error, cannot find post for some reason.")

    async def announce_cycle(self):
        while True:
            if self is not self.bot.get_cog("KRPlug"):
                print("Announce canceled, cog has been lost")
                return
            new_posts, new_ids = await self.check_plug()
            if new_posts:
                print("New posts found, attempting to send...")
                await self.send_announcements(new_posts)
                await self.save_plug(new_ids)
            await asyncio.sleep(60)

    async def send_announcements(self, results):
        embeds = []
        for result in results:
            embeds.append(self.get_embed(result))
        for guild in self.bot.guilds:
            for embed in embeds:
                channel = await self.config.guild(guild).channelid()
                if channel is None:
                    continue
                channel = guild.get_channel(channel)
                if channel is None:
                    continue
                # avoid permissions problems
                try:
                    await channel.send(embed=embed)
                except discord.errors.Forbidden as e:
                    print("FORBIDDEN: " + str(e))
                except Exception as e:
                    print(e)

    async def check_plug(self):
        pages = await self.scrape_plug()
        # process the pages into a nicer format
        post_ids, self.full_posts = self.process_pages(pages)
        # check for new posts
        old_ids = await self.config.posts()
        new_posts = []
        if old_ids:
            diff = list(set(post_ids) - set(old_ids))
            for post_id in diff:
                new_posts.append(self.full_posts[str(post_id)])
        return new_posts, post_ids

    # save post history
    async def save_plug(self, new_ids):
        async with self.config.posts() as posts:
            for new_id in new_ids:
                if new_id not in posts:
                    posts.append(new_id)
            posts.sort(reverse=True)

    async def scrape_plug(self):
        # scrape the Plug pages
        client = aiohttp.ClientSession(loop=self.bot.loop)
        async with client as session:
            pages = await asyncio.gather(
                *[self.fetch(session, url) for url in self.URLS],
                loop=self.bot.loop,
                return_exceptions=True
            )
        return pages

    async def fetch(self, session, url):
        async with async_timeout.timeout(10):
            async with session.get(url) as response:
                return await response.text()

    def get_embed(self, dic):
        if dic:
            embed = discord.Embed(title=dic['title'],
                                  description=dic['description'],
                                  url=dic['url'],
                                  timestamp=dic['timestamp'])
            embed.set_author(name=dic['author']['name'],
                             url=dic['author']['url'],
                             icon_url=dic['author']['icon_url'])
            if 'thumbnail' in dic:
                embed.set_thumbnail(url=dic['thumbnail']['url'])
            return embed
        else:
            return discord.Embed(title='No Articles')

    def process_pages(self, pages):
        ids = []
        attributes = {}
        for i, page in enumerate(pages):
            soup = BeautifulSoup(page, 'html.parser')
            contents = soup.find_all(class_='frame_plug')
            # get a list of article-ids
            ids += [int(content.attrs['data-articleid'])
                    for content in contents]
            # get a dictionary of attributes of every forum post in the page
            for content in contents:
                post = {
                    'title': re.sub('\s+', ' ', html.unescape(content.find(class_='tit_feed').string)).strip(),
                    'description': re.sub('\s+', ' ', html.unescape(content.find(class_='txt_feed').string)).strip(),
                    'url': 'https://www.plug.game/kingsraid/1030449/posts/' + content.attrs['data-articleid'],
                    'timestamp': self.get_time(content.find_all(class_='time')[1].string),
                    'author': {
                        'name': re.sub('\s+', ' ', content.find(class_='name').string).strip(),
                        'url': 'https://plug.game' + content.find(class_='name').attrs['href'],
                        'icon_url': content.find(class_='thumb').attrs['src']
                    }
                }
                if content.find_all(class_='img'):
                    post['thumbnail'] = {'url': content.find(
                        class_='img').attrs['style'][21:-1]}
                attributes[content.attrs['data-articleid']] = post
        ids.sort()
        return ids, attributes

    def get_time(self, time_str):
        # parsedatetime NLP does not understand min/hr
        time_str = time_str.replace('min', 'minute').replace('hr', 'hour')
        cal = parsedatetime.Calendar()
        # I honestly don't care if it can't parse the time correctly, it will just output current time
        dt = datetime(*cal.parse(time_str)[0][:6])
        return dt.replace(tzinfo=get_localzone()).astimezone(tz=pytz.utc)
