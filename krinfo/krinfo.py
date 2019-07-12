import asyncio
from typing import Any
import json
import os
import re

import discord
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from fuzzywuzzy import fuzz, process


Cog: Any = getattr(commands, "Cog", object)


class KRInfo(Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.data, self.hero_names, self.heroes, self.artifact_names, self.artifacts = self.load_files()
        self.config = Config.get_conf(
            self, identifier=107114105110102111, force_registration=True)

    @commands.command(name="skills", aliases=["skill"])
    async def skills(self, ctx: commands.Context, hero: str):
        """
        Shows the skills of a hero `%skills <hero>`
        """
        await self.reply(ctx=ctx, func=self.get_skill, hero=hero)

    @commands.command(name="books", aliases=["book"])
    async def books(self, ctx: commands.Context, hero: str):
        """
        Shows the book upgrade on skills of a hero `%books <hero>`
        """
        await self.reply(ctx=ctx, func=self.get_books, hero=hero)

    @commands.command(name="perks", aliases=["perk", "transcend"])
    async def perks(self, ctx: commands.Context, hero: str):
        """
        Shows the transcend skills of a hero `%perks <hero>`
        """
        await self.reply(ctx=ctx, func=self.get_perks, hero=hero)

    @commands.command()
    async def ut(self, ctx: commands.Context, hero: str, stars: str = "0"):
        """
        Shows the UTs of a hero `%ut <hero> <stars>`, defaults to 0 star UT
        """
        try:
            stars = int(stars)
        except:
            stars = 0
        if stars < 0 or stars > 5:
            stars = 0
        await self.reply(ctx=ctx, func=self.get_ut, hero=hero, stars=stars)

    @commands.command()
    async def uw(self, ctx: commands.Context, hero: str, stars: str = "0"):
        """
        Shows the UW of a hero `%uw <hero> <stars>`, defaults to 0 star UW
        """
        try:
            stars = int(stars)
        except:
            stars = 0
        if stars < 0 or stars > 5:
            stars = 0
        await self.reply(ctx=ctx, func=self.get_uw, hero=hero, stars=stars)

    @commands.command(name="hero")
    async def hero(self, ctx: commands.Context, hero: str):
        """
        Shows basic data of a hero `%hero <hero>`
        """
        await self.reply(ctx=ctx, func=self.get_story, hero=hero)

    @commands.command(name="artifact")
    async def artifact(self, ctx: commands.Context, *, artifact: str):
        """
        Shows basic data of an artifact `%artifact <artifact> <stars>`, defaults to 0 star artifact
        """
        temp = artifact.rsplit(" ", 1)
        if len(temp) == 2 and str.isdigit(temp[1]):
            stars = int(temp[1])
            artifact = temp[0]
        else:
            stars = 0
        if stars < 0 or stars > 5:
            stars = 0
        results = self.fuzzysearch(
            artifact.lower().capitalize(), self.artifact_names)
        if results[1] > 50:
            await ctx.send(embed=self.get_artifact(results[0], stars))
        else:
            await ctx.send(f"Unable to locate {artifact}.")

    async def reply(self, ctx, func, hero: str, stars: int=None):
        hero_ = hero.lower().capitalize()
        results = self.fuzzysearch(hero_, self.hero_names)
        if results[1] < 50:
            hero_ = hero
        else:
            hero_ = results[0]
        if self.check_hero(hero_):
            if type(stars) is int:
                emb = func(hero_, stars)
            else:
                emb = func(hero_)
            await ctx.send(embed=emb)
        else:
            await ctx.send(f"Unable to locate {hero}.")

    def get_artifact(self, artifact, stars):
        artifact_locale = self.get_artifact_locale(artifact)
        skill_str = ""
        skill_str += artifact_locale["description"][stars] + "\n"
        title = artifact_locale["name"]
        id_ = self.artifact_names[artifact]
        return self.get_arti_embed(title, id_, skill_str)

    def get_skill(self, hero):
        def parse_skill(skill_vars, skill_locale, skill_num):
            skill_str = ""
            skill_str += self.bold(skill_num.upper() + ": " +
                                   skill_locale["name"]) + "\n"
            if "mana" in skill_vars:
                skill_str += "mana: " + str(skill_vars["mana"]) + "\n"
            if "cooldown" in skill_vars:
                skill_str += "cooldown: " + str(skill_vars["cooldown"]) + "s\n"
            skill_str += self.parse_vars(skill_locale["description"],
                                         skill_vars["description"]) + "\n"
            if "linked" in skill_vars:
                for i, linked in enumerate(skill_vars["linked"]):
                    skill_str += self.bold(skill_locale["linked"][str(i)]["name"] +
                                           " (" + skill_num.upper() + " linked skill)") + "\n"
                    skill_str += self.parse_vars(skill_locale["linked"]
                                                 [str(i)]["description"], linked) + "\n"
            skill_str += "\n"
            return skill_str
        hero_vars, hero_locale = self.get_hero(hero)
        skill_str = ""
        for i in range(1, 5):
            s = "s" + str(i)
            skill_str += parse_skill(hero_vars[s], hero_locale[s], s)
        title = hero_locale["name"] + ", " + hero_locale["subtitle"]
        id_ = hero_vars["index"]
        return self.get_embed(title, id_, skill_str)

    def get_books(self, hero):
        hero_vars, hero_locale = self.get_hero(hero)
        skill_str = ""
        for i in range(1, 5):
            s = "s" + str(i)
            skill_str += self.bold(s.upper()) + "\n"
            skill_str += self.parse_vars(hero_locale[s]["books"]
                                         ["0"], hero_vars[s]["books"][0]) + "\n"
            skill_str += self.parse_vars(hero_locale[s]["books"]
                                         ["1"], hero_vars[s]["books"][1]) + "\n"
            skill_str += self.parse_vars(hero_locale[s]["books"]
                                         ["2"], hero_vars[s]["books"][2]) + "\n\n"
        title = hero_locale["name"] + ", " + hero_locale["subtitle"]
        id_ = hero_vars["index"]
        return self.get_embed(title, id_, skill_str)

    def get_perks(self, hero):
        hero_vars, hero_locale = self.get_hero(hero)
        skill_str = ""
        for i in range(1, 5):
            s = "s" + str(i)
            skill_str += self.bold(s.upper() + " Light") + "\n"
            skill_str += self.parse_vars(hero_locale[s]
                                         ["light"], hero_vars[s]["light"]) + "\n"
            skill_str += self.bold(s.upper() + " Dark") + "\n"
            skill_str += self.parse_vars(hero_locale[s]
                                         ["dark"], hero_vars[s]["dark"]) + "\n\n"
        skill_str += self.bold("T5 Light") + "\n"
        skill_str += self.parse_vars(hero_locale["t5"]
                                     ["light"], hero_vars["t5"]["light"]) + "\n"
        skill_str += self.bold("T5 Dark") + "\n"
        skill_str += self.parse_vars(hero_locale["t5"]
                                     ["dark"], hero_vars["t5"]["dark"]) + "\n"
        title = hero_locale["name"] + ", " + hero_locale["subtitle"]
        id_ = hero_vars["index"]
        return self.get_embed(title, id_, skill_str)

    def get_uw(self, hero, stars):
        hero_vars, hero_locale = self.get_hero(hero)
        skill_str = ""
        skill_str += self.bold(hero_locale["uw"]["name"]) + "\n"
        skill_str += hero_locale["uw"]["description"][stars] + "\n"
        title = hero_locale["name"] + ", " + hero_locale["subtitle"]
        id_ = hero_vars["index"]
        return self.get_embed(title, id_, skill_str)

    def get_ut(self, hero, stars):
        hero_vars, hero_locale = self.get_hero(hero)
        skill_str = ""
        for i in range(1, 5):
            s = "s" + str(i)
            skill_str += self.bold(s.upper() + ": " +
                                   hero_locale[s]["ut"]["name"]) + "\n"
            skill_str += hero_locale[s]["ut"]["description"][stars] + "\n\n"
        title = hero_locale["name"] + ", " + hero_locale["subtitle"]
        id_ = hero_vars["index"]
        return self.get_embed(title, id_, skill_str)

    def get_story(self, hero):
        hero_vars, hero_locale = self.get_hero(hero)
        story_str = "*" + hero_locale["description"] + "*"
        class_str = hero_vars["class"].capitalize(
        ) + " / " + hero_vars["type"].capitalize() + "\n"
        ranged = hero_vars["auto"]["rangeType"]
        if ranged == "Ranged":
            ranged += "-" + str(hero_vars["auto"]["range"])
        class_str += ranged + " / " + \
            hero_vars["position"]["type"].capitalize(
            ) + "-" + str(hero_vars["position"]["weight"])
        index_str = self.bold("Gender") + ": " + "WIP\n"
        index_str += self.bold("Age") + ": " + "WIP\n"
        index_str += self.bold("Height") + ": " + "WIP\n"
        index_str += self.bold("Race") + ": " + "WIP\n"
        index_str += self.bold("Birthday") + ": " + "WIP\n"
        index_str += self.bold("Likes") + ": " + hero_locale["like"] + "\n"
        index_str += self.bold("Dislikes") + ": " + hero_locale["dislike"]
        additional_str = "Mp/Atk: " + str(hero_vars["mpatk"]) + "\n"
        additional_str += "Mp/Sec: " + str(hero_vars["mpsec"]) + "\n"
        for k, v in self.data["class"][hero_vars["class"]]["attributes"].items():
            additional_str += k.capitalize() + ": " + str(v) + "\n"
        additional_str = additional_str.strip()
        fields = {
            "Class Info": {"s": class_str, "inline": False},
            "Main Stats": {"s": "WIP", "inline": True},
            "Additional Stats": {"s": additional_str, "inline": True},
            "Hero Index": {"s": index_str, "inline": False},
            "Story": {"s": hero_locale["story"], "inline": False}
        }
        id_ = hero_vars["index"]
        return self.get_embed(hero, id_, story_str, fields)

    def get_embed(self, hero, id_, text="", fields=None):
        embed = discord.Embed(title=hero,
                              description=text,
                              url="https://maskofgoblin.com/hero/" + str(id_))
        if fields:
            for k, v in fields.items():
                embed.add_field(name=k, value=v["s"], inline=v["inline"])
        return embed

    def get_arti_embed(self, artifact, id_, text="", fields=None):
        embed = discord.Embed(title=artifact,
                              description=text,
                              url="https://maskofgoblin.com/artifact/" + str(id_))
        if fields:
            for k, v in fields.items():
                embed.add_field(name=k, value=v["s"], inline=v["inline"])
        return embed

    def bold(self, string_):
        return "**" + string_ + "**"

    def parse_vars(self, string_, vars_):
        if vars_ is not None:
            for i, var in enumerate(vars_):
                string_ = string_.replace("{" + str(i) + "}", str(var))
        return string_

    def check_hero(self, hero):
        return True if hero in self.hero_names else False

    def get_hero(self, hero):
        hero_id = self.hero_names[hero]
        hero_vars = self.data["hero"][hero_id]
        hero_locale = self.heroes[hero_id]
        return hero_vars, hero_locale

    def get_artifact_locale(self, artifact):
        arti_id = self.artifact_names[artifact]
        artifact_locale = self.artifacts[arti_id]
        return artifact_locale

    def get_unique(self, star, baseVal):
        # fix level to 90
        return math.floor((math.floor((star * 98677)/1000) * baseVal)/1000)

    def fuzzysearch(self, hero, names):
        extracted = process.extract(
            hero, names.keys(), limit=1, scorer=fuzz.QRatio)
        if extracted:
            return extracted[0]
        else:
            return None

    def load_files(self):
        fullpath = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(fullpath, "Mask-of-Goblin/src/data.json")) as f:
            data = json.load(f)
        with open(os.path.join(fullpath, "Mask-of-Goblin/public/i18n/English/hero/names.json")) as f:
            hero_names = json.load(f)
        with open(os.path.join(fullpath, "Mask-of-Goblin/public/i18n/English/artifact/names.json")) as f:
            artifact_names = json.load(f)
        heroes = {}
        for k, v in hero_names.items():
            with open(os.path.join(fullpath, "Mask-of-Goblin/public/i18n/English/hero/" + str(v) + ".json")) as f:
                hero = json.load(f)
            heroes[str(v)] = hero
        artifacts = {}
        for k, v in artifact_names.items():
            with open(os.path.join(fullpath, "Mask-of-Goblin/public/i18n/English/artifact/" + str(v) + ".json")) as f:
                artifact = json.load(f)
            artifacts[str(v)] = artifact
        return data, hero_names, heroes, artifact_names, artifacts
