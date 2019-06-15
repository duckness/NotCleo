import asyncio
from typing import Any
import json
import os
import re

import discord
from redbot.core import Config, checks, commands
from redbot.core.bot import Red


Cog: Any = getattr(commands, "Cog", object)


class KRInfo(Cog):
    def __init__(self):
        self.bot = bot
        self.data, self.names, self.heroes = self.load_files()
        self.config = Config.get_conf(
            self, identifier=107114105110102111, force_registration=True)

    @commands.command()
    async def skill(self, ctx: commands.Context, hero: str):
        """
        Shows the skills of a hero `%skill <hero>`
        """
        txt = self.get_skill(hero.lower().capitalize())
        await ctx.send(txt)

    @commands.command()
    async def books(self, ctx: commands.Context, hero: str):
        """
        Shows the book upgrade on skills of a hero `%books <hero>`
        """
        txt = self.get_books(hero.lower().capitalize())
        await ctx.send(txt)

    @commands.command()
    async def perks(self, ctx: commands.Context, hero: str):
        """
        Shows the transcend skills of a hero `%perks <hero>`
        """
        txt = self.get_perks(hero.lower().capitalize())
        await ctx.send(txt)

    @commands.command()
    async def ut(self, ctx: commands.Context, hero: str, stars: str = "0"):
        """
        Shows the UTs of a hero `%ut <hero> <stars>`, defaults to 0 star UT
        """
        try:
            stars = int(stars)
        except:
            stars = 0
        txt = self.get_ut(hero.lower().capitalize(), stars)
        await ctx.send(txt)

    @commands.command()
    async def ut(self, ctx: commands.Context, hero: str, stars: str = "0"):
        """
        Shows the UW of a hero `%uw <hero> <stars>`, defaults to 0 star UW
        """
        try:
            stars = int(stars)
        except:
            stars = 0
        txt = self.get_uw(hero.lower().capitalize(), stars)
        await ctx.send(txt)

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
        return skill_str

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
        return skill_str

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
        return skill_str

    def get_uw(self, hero, stars):
        hero_vars, hero_locale = self.get_hero(hero)
        skill_str = ""
        skill_str += self.bold(hero_locale["uw"]["name"]) + "\n"
        skill_str += hero_locale["uw"]["description"][stars] + "\n"
        return skill_str

    def get_ut(self, hero, stars):
        hero_vars, hero_locale = self.get_hero(hero)
        skill_str = ""
        for i in range(1, 5):
            s = "s" + str(i)
            skill_str += self.bold(s.upper() + ": " +
                                   hero_locale[s]["ut"]["name"]) + "\n"
            skill_str += hero_locale[s]["ut"]["description"][stars] + "\n\n"
        return skill_str

    def bold(self, string_):
        return "**" + string_ + "**"

    def parse_vars(self, string_, vars_):
        for i, var in enumerate(vars_):
            string_ = string_.replace("{" + str(i) + "}", str(var))
        return string_

    def get_hero(self, hero):
        hero_id = self.names[hero]
        hero_vars = self.data["hero"][hero_id]
        hero_locale = self.heroes[hero_id]
        return hero_vars, hero_locale

    def load_files(self):
        fullpath = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(fullpath, "Mask-of-Goblin/src/data.json")) as f:
            data = json.load(f)
        with open(os.path.join(fullpath, "Mask-of-Goblin/public/i18n/English/hero/names.json")) as f:
            names = json.load(f)
        heroes = {}
        for k, v in names.items():
            with open(os.path.join(fullpath, "Mask-of-Goblin/public/i18n/English/hero/" + str(v) + ".json")) as f:
                hero = json.load(f)
            heroes[str(v)] = hero
        return data, names, heroes
