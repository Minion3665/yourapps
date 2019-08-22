import discord, base64, typing, traceback, time

import manager
import helper
from discord.ext import commands, tasks

data = manager.json_mngr().read('./prefixes.json')
prefixf = open('./token', 'r')
prefix = prefixf.readlines()
prefix = base64.b64encode(bytes(prefix[0], 'utf-8'))
prefixf.close()

def get_prefix(b0t, message):
	return commands.when_mentioned_or("ym!" if str(message.guild.id) not in data.keys() else data[str(message.guild.id)])(b0t, message)


bot = commands.AutoShardedBot(command_prefix=get_prefix, case_insensitive=True,
							  help_command=commands.MinimalHelpCommand(), owner_id=421698654189912064)
bot.last_tb = 'nerd, im bug free so far!'
print("+===+ STATUS +===+")
@bot.event
async def on_shard_ready(shard):
	print("|Shard {}:ONLINE|".format(shard))


@bot.event
async def on_ready():
	bot.load_extension('jishaku')
	bot.load_extension('cogs.core')
	print('|MAIN BOT: ONLINE|')
	print('|MAIN BOT:' + bot.user.name + '|')
	print("+================+")

# cog management

@bot.command()
@commands.is_owner()
async def reload(ctx, cog: str):
	"""reload cogs!"""
	try:
		bot.reload_extension(cog)
	except commands.ExtensionNotLoaded:
		bot.load_extension(cog)
	except:
		bot.last_tb = traceback.format_exc()
		await ctx.send(f"An error occurred. please use `{ctx.prefix}tb` to see it.")
	await ctx.send("Success!")


@bot.command(name='traceback', aliases=['tb'])
@commands.is_owner()
async def _traceback(ctx):
	"""Get the latest error."""
	error_pages = list(manager.Formatting.pagify(bot.last_tb, page_length=1700, shorten_by=18))
	msgs = []
	dele=False
	last_page = error_pages[-1]
	for page in error_pages:
		if page == last_page:
			add_r = True
		else:
			add_r = False
		ta = await ctx.send(f"```py\n{page}\n```")
		msgs.append(ta)
		if add_r:
			await ta.add_reaction('\N{WASTEBASKET}')
			r, u = await bot.wait_for('reaction_add',
										check=lambda r, u:
										r.message.id == ta.id and str(r.emoji) == '\N{WASTEBASKET}' and u == ctx.author)
			dele=True
		else:
			continue

	if dele:
		for msg in msgs:
			try:
				await msg.delete()
			except:
				pass
	return
perms = f"```\nsend Messages\nread messages\nread message history\nadd reactions\nmanage messages\nuse external emoji" \
		f"manage roles\n```"
errors = {
	commands.CommandNotFound: None,
	helper.CancelledError: "Process cancelled.",
	commands.BotMissingPermissions: f"Im missing permissions!\nPlease ensure i have the following permssions:\n{perms}",
	KeyError: f"There was a keyerror; have you run setup?"
}
@bot.event
async def on_command_error(ctx, error):
	error = getattr(error, 'original', error)
	if isinstance(error, commands.CommandNotFound):
		return
	if ctx.author.id == ctx.bot.owner_id:
		await ctx.send(error)
	try:
		await ctx.message.add_reaction('<:eekuborkedit:603246957288226860>')
	except:
		pass
	finally:
		if isinstance(error, commands.MissingRequiredArgument):
			return await ctx.send_help(bot.get_command(ctx.command.qualified_name))
		elif isinstance(error, commands.BadArgument):
			await ctx.send(f"bad argument\n{str(error)}")
			await ctx.send_help(bot.get_command(ctx.command.qualified_name))
		if error in errors:
			return await ctx.send(errors[error])
		try:
			await ctx.send(f"{ctx.author.mention} Hey! wheres my fly swatter?!\n(an error was raised and has been reported to my "
						"developer.)")
		except:
			traceback.print_exc()
		try:
			raise error
		except:
			traceback.print_exc()
			bot.last_tb = traceback.format_exc()

def x():
	bot.run(str(base64.b64decode(prefix).decode('utf-8')))

x()