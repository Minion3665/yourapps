from manager import json_mngr
from discord.ext import commands, tasks

import discord


class Settings(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	def _setup(self, ctx):
		data = json_mngr().read('./data/settings.json')
		data[str(ctx.guild.id)] = {
			"edit_roles": [],
			"view_roles": [],
			"log_channel": None
		}
		return json_mngr().handle_modify('./data/settings.json', newdata=data)

	@commands.group(name="config", aliases=['settings'], invoke_without_command=True, case_insensitive=True)
	async def _settings(self, ctx, *, value: str = None):
		"""View your server's current configuration settings!
		provide `value` and i will attempt to """
		data = json_mngr().read('./data/settings.json')
		if str(ctx.guild.id) not in data.keys():
			return await ctx.send("You haven't set any settings yet!")
		data = data[str(ctx.guild.id)]
		if ctx.author:
			e = discord.Embed(color=discord.Color.orange())
			for key in data.keys():
				e.add_field(name=key, value=f'setting: {data[key]}', inline=False)
			return await ctx.send(embed=e)

	@_settings.command(name='raw', aliases=['audit', 'data'])
	async def settings_raw(self, ctx):
		"""retrieves all of your guild's data and outputs it in a JSON format. only use this if you understand JSON."""
		data = json_mngr().read('./data/settings.json')
		if str(ctx.guild.id) not in data.keys():
			return await ctx.send("Your guild has no data!")
		else:
			with open('./data/'+str(ctx.guild.id)+'.json', 'w+') as f:
				f.write('{}')
				json_mngr().handle_modify(f'./data/{str(ctx.guild.id)}.json', newdata=data[str(ctx.guild.id)], backup=False)
				f.close()
			return await ctx.send("Here is your guild's data!", file=discord.File('./data/{}.json'.format(str(ctx.guild.id))))

	@_settings.group(name="whitelist", invoke_without_command=True)
	@commands.is_owner()
	async def settings_whitelist(self, ctx):
		"""add a guild to the whitelist"""
		pass

	@_settings.command()
	@commands.has_permissions(administrator=True)
	async def setlog(self, ctx, channel: discord.TextChannel):
		"""set a logging channel for apps"""
		data = json_mngr().read('./data/settings.json')
		if str(ctx.guild.id) not in data.keys():
			data = self._setup(ctx)
		m = await ctx.send("setting...")
		try:
			await channel.send(embed=discord.Embed(title="log permissions test"))
		except discord.Forbidden:
			return await m.edit(content="Unable to send to that channel. please enable embed links and send messages"
										f" for me in {channel.mention}")
		json_mngr().handle_modify('./data/settings.json', newdata=data, backup=True)
		await m.edit(content="complete!")

def setup(bot):
	bot.add_cog(Settings(bot))