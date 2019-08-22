import discord, asyncio, aiohttp
import json

from manager import json_mngr
import helper
from discord.ext import commands, tasks


class PostFailed(Exception):
	def __init__(self, resp: int=404, reason: str=None):
		self.resp = resp
		self.reason = reason

	def __str__(self):
		return str(self.resp)+' '+self.reason
	def __int__(self):
		return self.resp


class Core(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.session = None
		self.guildbancheck.start()

	async def submit_app(self, ctx, embed: discord.Embed, appname, *, rawdata=None):
		guild = str(ctx.guild.id)
		data = json_mngr().read('./data/settings.json')
		if str(guild) not in data.keys():  # wot
			await ctx.send("Error: the bot was unable to send a message to the guild's log channel. please tell "
						"an administrator")
		else:
			logchannel = self.bot.get_channel(data[guild]['log_channel'])
			if logchannel is None:
				await ctx.send("Error: the bot was unable to send a message to the guild's log channel. please tell "
									"an administrator to set a log channel")
			else:
				embed.title = f"The application for {ctx.author}, {appname}:"
				await logchannel.send(embed=embed)
			apps = json_mngr().read('./data/apps.json')
			apps[guild]['submitted'].append(embed)
			json_mngr().handle_modify('./data/apps.json', newdata=apps, backup=True)
			return

	@tasks.loop(seconds=30)
	async def guildbancheck(self):
		data = json_mngr().read('./data/allowed_guilds.json')
		for guild in self.bot.guilds:
			if guild.id not in data['whitelist']:
				try:
					await guild.owner.send(f"Sorry, but your guild ({guild.name}) is not whitelisted, so i left.\nif this is a mistake"
											", please contanct my developer.\n\nNot a mistake, but still want me? go"
											"to http://dragdev.xyz/ya/beta-join.html and request acces!")
				except:
					pass
				finally:
					await guild.leave()
				channel = self.bot.get_channel(606993571014377474)
				if channel is None:
					print(f"left unauthorized guild: {guild.name} {guild.owner} {guild.id}")
				else:
					await channel.send(f"left {guild.name} ({guild.id}) {guild.owner} for: unauthorized ")
				continue


	def can_view_or_edit():
		def p(ctx):
			data = json_mngr().read('./data/settings.json')
			if str(ctx.guild.id) not in data.keys():
				return False  # no config

			if len(data[str(ctx.guild.id)]['view_roles']) == 0 and len(data[str(ctx.guild.id)]['edit_roles']) == 0:
				return False  # no role set

			for role in ctx.author.roles:
				if role.id in data[str(ctx.guild.id)]['view_roles'] or role.id in data[str(ctx.guild.id)]['edit_roles']:
					return True
			else:
				return False  # no role
		return commands.check(p)

	def can_edit():
		def p(ctx):
			data = json_mngr().read('./data/settings.json')
			if str(ctx.guild.id) not in data.keys():
				return False  # no config

			if len(data[str(ctx.guild.id)]['edit_roles']) == 0:
				return False  # no role set

			for role in ctx.author.roles:
				if role.id in data[str(ctx.guild.id)]['edit_roles']:
					return True
			else:
				return False  # no role
		return commands.check(p)

	async def d(self):
		return aiohttp.ClientSession()

	def cog_unload(self):
		self.guildbancheck.stop()
		try:
			self.bot.loop.create_task(self.session.close())
		except AttributeError:  # not opened
			pass

	async def post(self, content: str):
		if self.session is None:
			await self.d()

		async with self.session.post('https://mystb.in/documents/', data=bytes(content, 'utf-8')) as resp:
			if resp.status == 200:
				j = await resp.json()
				print(j)
				return j

	@commands.command()
	async def positions(self, ctx):
		"""List the current applications for this server"""
		if self.session is None:
			self.session = await self.d()
		data = json_mngr().read('./data/apps.json')
		if str(ctx.guild.id) not in data.keys():
			e = discord.Embed(
				description="This guild has no apps!",
				color=discord.Color.dark_magenta()
			)
			return await ctx.send(embed=e)
		else:
			content = ""
			ccontent = ""
			_open=discord.Embed(title="Open Applications:", color=discord.Color.green())
			for app in data[str(ctx.guild.id)]['open'][:25]:
				_open.add_field(name=app['name'], value=app['value'], inline=True)
				content += f"App Name: {app['name']}\nApp Value: {app['value']}\n\n"
			if len(_open) > 6000:
				_open.clear_fields()
				url = await self.post(content)
				url = f'https://mystb.in/{url["key"]}.md'
				_open.description=f"Too many characters to display, so i put it in the url! click my title."
				_open.url = url
			closed = discord.Embed(title="closed applications:", color=discord.Color.red())
			for app in data[str(ctx.guild.id)]['closed'][:25]:
				closed.add_field(name=app['name'], value=app['value'], inline=True)
				ccontent += f"App Name: {app['name']}\nApp Value: {app['value']}\n\n"
			if len(closed) > 6000:
				closed.clear_fields()
				url = await self.post(content)
				url = f'https://mystb.in/{url["key"]}.md'
				closed.description=f"Too many characters to display, so i put it in the url! click my title."
				closed.url = url
			await ctx.send(embed=_open)
			await ctx.send(embed=closed)

	@commands.command()
	@can_edit()
	@commands.guild_only()
	@commands.bot_has_permissions(manage_messages=True, external_emojis=True, add_reactions=True, embed_links=True)
	async def setup(self, ctx, *, name: str):
		"""Run setup, and create your first app!"""
		# TODO: visualise errors
		data = json_mngr().read('./data/apps.json')
		if str(ctx.guild.id) not in data.keys():
			data[str(ctx.guild.id)] = {
				"open": [],
				"closed":[],
				"submitted":[],
				"appdata":{}
			}
		if name.lower() in data[str(ctx.guild.id)]['appdata'].keys():
			return await ctx.send("That application already exists!")
		appdata = await helper.App().create(ctx, name, timeout=120.0, setup=True)
		data[str(ctx.guild.id)]['open'].append({'name': name, 'value': appdata['description']})
		data[str(ctx.guild.id)]['appdata'][name.lower()] = appdata
		json_mngr().handle_modify('./data/apps.json', newdata=data, indent=2, backup=True)
		await ctx.send(ctx.author.mention + ' Successfully made an application!')

	@commands.group(name='app', case_insensitive=True, invoke_without_command=True)
	@can_edit()
	@commands.guild_only()
	@commands.bot_has_permissions(manage_messages=True, external_emojis=True, add_reactions=True, embed_links=True)
	async def _app(self, ctx):
		"""application management"""
		await ctx.send_help(ctx.command)

	@_app.command(name="create")
	@can_edit()
	async def app_create(self, ctx, *, name: str = None):
		"""Create an application!"""
		if name is None:
			return await ctx.send("Please reinvoke this command, but supply a name for your app next time!")

	@commands.command(name='close', aliases=['toggle'])
	@can_edit()
	@commands.guild_only()
	@commands.bot_has_permissions(manage_messages=True, external_emojis=True, add_reactions=True, embed_links=True)
	async def __close(self, ctx, *, name: str):
		"""toggles an application. for example, if it is already closed, it will open it."""
		_data = json_mngr().read('./data/apps.json')
		data = _data[str(ctx.guild.id)]
		_open = data['open']
		_closed = data['closed']
		for app in data['closed']:
			if app['name'] == name.lower():
				data['closed'].remove(app)
				data['open'].append(app)
				did='opened'
				break
		else:
			for app in data['open']:
				if app['name'] == name.lower():
					data['open'].remove(app)
					data['closed'].append(app)
					did = 'closed'
					break
			else:
				return await ctx.send("No app by that name was found.")
		json_mngr().handle_mod('./data/apps.json', newdata=data, indent=2, backup=True)
		await ctx.send(f'{did} the application. view it with `{ctx.prefx}positions`!')

	@commands.group(invoke_without_command=True)
	@commands.has_permissions(administrator=True)
	async def editrole(self, ctx, *, role: discord.Role):
		"""Set the role that is allowed to edit apps
		leave blank to reset it"""
		data = json_mngr().read('./data/settings.json')
		if str(ctx.guild.id) not in data.keys():
			data[str(ctx.guild.id)] = {
				"edit_roles": [],
				"view_roles": [],
				"log_channel": None
			}
		if role:
			data[str(ctx.guild.id)]['edit_roles'].append(role.id)
			json_mngr().handle_modify('./data/settings.json', newdata=data, indent=2, backup=True)
			await ctx.send(f"added {role.id} as an editing role.")

	@editrole.command()
	@commands.has_permissions(administrator=True)
	async def remove(self, ctx, *, role: discord.Role):
		"""remove an editing role"""
		data = json_mngr().read('./data/settings.json')
		if str(ctx.guild.id) not in data.keys():
			data[str(ctx.guild.id)] = {
				"edit_roles": [],
				"view_roles": [],
				"log_channel": None
			}
		if role:
			if role.id in data[str(ctx.guild.id)]['edit_roles']:
				data[str(ctx.guild.id)]['edit_roles'].remove(role.id)
			json_mngr().handle_modify('./data/settings.json', newdata=data, indent=2, backup=True)
			await ctx.send(f"removed {role.id} as an editing role.")

	async def get_answer(self, ctx):
		def c(m):
			return m.author == ctx.author and ctx.channel == m.channel
		try:
			to_ret = await self.bot.wait_for('message', check=c, timeout=190)
			return to_ret
		except asyncio.TimeoutError:
			return None

	@commands.command()
	@commands.bot_has_permissions(manage_messages=True, external_emojis=True, add_reactions=True, embed_links=True)
	async def apply(self, ctx, *, appname: str):
		"""apply for an app!"""
		# return await ctx.send("this command is None-functional as it does not have working framework.")
		_data = json_mngr().read('./data/apps.json')
		print(_data)
		data = _data[str(ctx.guild.id)]
		print(data)
		for app in data['open']:
			if app['name'].lower() == appname.lower():
				if app['name'] in data['appdata'].keys():
					print(data['appdata'])
					print(data['appdata'][app['name']])
					print(data['appdata'][app['name']]["PURE_QUESTIONS"])
					questions = data['appdata'][app['name']]["PURE_QUESTIONS"]
					_questions = enumerate(questions, start=1)
					e = discord.Embed(title=f"apply for {app['name']}!", color=discord.Color.blue())
					message = await ctx.send(embed=e)
					for n, q in _questions:
						e.add_field(name=f"{n}. {q}", value="your answer here")
						await message.edit(content=None, embed=e)
						answer = await self.get_answer(ctx)
						if answer is None:
							return await ctx.send("Timed out.")
						e.remove_field(len(e.fields) - 1)
						e.add_field(name=f"{n}. {q}", value=answer.content)
					x = await ctx.send("Are you sure you want to submit this application?")
					yes = '\U00002705'
					no = '\U0000274c'
					await x.add_reaction(yes)
					await x.add_reaction(no)
					r, u = await self.bot.wait_for('reaction_add', check=lambda r, u: str(r.emoji) in [yes, no] and r.message.id == x.id and u.id == ctx.author.id)
					if str(r.emoji) == yes:
						await self.submit_app(ctx, e, app['name'])
					else:
						return await x.edit(content="cancelled.")

def setup(bot):
	bot.add_cog(Core(bot))
