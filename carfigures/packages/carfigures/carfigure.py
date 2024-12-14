import logging
import random
import string
from datetime import datetime

import discord

from carfigures.core.models import GuildConfig, Car, cars
from carfigures.packages.carfigures.components import CatchView
from carfigures.settings import appearance

log = logging.getLogger("carfigures.packages.carfigures")


class CarFigure:
    def __init__(self, model: Car):
        """
        Defining properties for local use.
        """
        self.name = model.fullName
        self.model = model
        self.message: discord.Message = discord.utils.MISSING
        self.caught = False
        self.time = datetime.now()

    @classmethod
    async def get_random(cls):
        """
        A method to get a random Car instance from a list of enabled cars based on their rarity.
        """
        carfigures = list(filter(lambda m: m.enabled, cars.values()))
        if not carfigures:
            raise RuntimeError("No car to spawn")
        rarities = [x.rarity for x in carfigures]
        cb = random.choices(population=carfigures, weights=rarities, k=1)[0]
        return cls(cb)

    async def spawn(self, channel: discord.TextChannel) -> bool:
        """
        Spawn a carfigure in a channel.
        Parameters
        ----------
        channel: discord.TextChannel
            The channel where to spawn the carfigure. Must have permission to send messages
            and upload files as a bot (not through interactions).
        Returns
        -------
        bool
            `True` if the operation succeeded, otherwise `False`. An error will be displayed
            in the logs if that's the case.
        """

        def generate_random_name():
            """
            Generate a random name.
            """
            source = string.ascii_uppercase + string.ascii_lowercase + string.ascii_letters
            return "".join(random.choices(source, k=15))

        extension = self.model.spawnPicture.split(".")[-1]
        fileLocation = "." + self.model.spawnPicture
        filename = f"nt_{generate_random_name()}.{extension}"
        guild = await GuildConfig.get(guild_id=channel.guild.id)
        spawnrole = f" <@&{guild.spawnRole}>" if guild.spawnRole else None
        try:
            permissions = channel.permissions_for(channel.guild.me)
            if permissions.attach_files and permissions.send_messages:
                self.message = await channel.send(
                    f"A wild {appearance.collectibleSingular} has appeared!{spawnrole}",
                    view=CatchView(self),
                    file=discord.File(fileLocation, filename=filename),
                )
                return True
            else:
                log.error("Missing permission to spawn car in channel %s.", channel)
        except discord.Forbidden:
            log.error(f"Missing permission to spawn car in channel {channel}.")
        except discord.HTTPException:
            log.error("Failed to spawn car", exc_info=True)
        return False
