import logging
import time
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist

from carfigures.packages.carfigures.carfigure import CarFigure
from carfigures.core.models import Car, CarInstance, Player
from carfigures.settings import appearance

log = logging.getLogger("carfigures.core.commands")

if TYPE_CHECKING:
    from .bot import CarFiguresBot


class Core(commands.Cog):
    """
    Core commands of CarFigures bot
    """

    def __init__(self, bot: "CarFiguresBot"):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """
        Ping!
        """
        await ctx.send("Pong.")

    @commands.command()
    @commands.is_owner()
    async def reloadtree(self, ctx: commands.Context):
        """
        Sync the application commands with Discord
        """
        await self.bot.tree.sync()
        await ctx.send("Application commands tree reloaded.")

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, package: str):
        """
        Reload an extension
        """
        package = "carfigures.packages." + package
        try:
            try:
                await self.bot.reload_extension(package)
            except commands.ExtensionNotLoaded:
                await self.bot.load_extension(package)
        except commands.ExtensionNotFound:
            await ctx.send("Extension not found.")
        except Exception:
            await ctx.send("Failed to reload extension.")
            log.error(f"Failed to reload extension {package}", exc_info=True)
        else:
            await ctx.send("Extension reloaded.")

    @commands.command()
    @commands.is_owner()
    async def reloadcache(self, ctx: commands.Context):
        """
        Reload the cache of database models.

        This is needed each time the database is updated, otherwise changes won't reflect until
        next start.
        """
        await self.bot.reloadCache()
        await ctx.send("Database models cache have been reloaded.")

    @commands.command()
    @commands.is_owner()
    async def analyzedb(self, ctx: commands.Context):
        """
        Analyze the database. This refreshes the counts displayed by the `/info status` command.
        """
        connection = Tortoise.get_connection("default")
        t1 = time.time()
        await connection.execute_query("ANALYZE")
        t2 = time.time()
        await ctx.send(f"Analyzed database in {round((t2 - t1) * 1000)}ms.")

    @commands.command()
    @commands.is_owner()
    async def spawn(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel | None = None,
        amount: int = 1,
        *,
        car: str | None = None,
    ):
        """
        Spawn an entity.
        """
        for _ in range(amount):
            if not car:
                carfigure = await CarFigure.getRandom()
            else:
                try:
                    car_model = await Car.get(fullName__iexact=car.lower())
                except DoesNotExist:
                    await ctx.send(f"No such {appearance.collectibleSingular} exists.")
                    return
                carfigure = CarFigure(car_model)
            await carfigure.spawn(channel or ctx.channel)

    @commands.command()
    @commands.is_owner()
    async def transfer(
        self,
        ctx: commands.Context,
        gifter: discord.User,
        receiver: discord.User,
    ):
        """
        Transfer someone's inventory to someone else.
        """
        try:
            oldPlayer = await Player.get(discord_id=gifter.id)
        except DoesNotExist:
            await ctx.send(f"Original player doesn't have any {appearance.collectiblePlural}.")
            return
        
        newPlayer, _ = await Player.get_or_create(discord_id=receiver.id)

        await CarInstance.filter(player=oldPlayer).update(player=newPlayer)

        await ctx.send(
            f"The {appearance.garageName} of {gifter.display_name} has been transferred to {receiver.display_name}."
        )
