import discord
from discord.ext import commands
import asyncio
from manager import json_mngr


class AppError(Exception):
	def __init__(self, id: float, *, reason: str = 'No Reason'):
		self.id = id,
		self.reason = reason

	def __str__(self):
		return f"AppError {self.id}: {self.reason}"

	def __int__(self):
		return int(str(self.id).replace('.', ''))

	def __float__(self):
		return self.id

	def __error_code__(self):
		return self.id

	def __error__(self):
		return (self.id, self.reason)

	def __error_reason__(self):
		return self.reason


class CancelledError(AppError):
	def __str__(self):
		return 'application cancelled'

class App:
	def __init__(self):
		self.hi = ''

	async def create(self, ctx, name: str, *, timeout: float = None, check=None, setup=False):
		"""create an application"""
		bot = ctx.bot
		if check is None:
			def check(message):
				return message.author == ctx.author and message.channel == ctx.channel

		if ctx.guild is None:
			dest = ctx.author
		else:
			dest = ctx.channel
		color = discord.Color.gold()
		title = "Create an application!"
		e = discord.Embed(title="Create an application!", color=discord.Color.gold())
		e.description = "please say anything to continue."
		sourcemsg = await dest.send(embed=e)

		questions = []
		resp = await bot.wait_for('message', check=check, timeout=timeout)
		await resp.delete()
		e.description = "What do you want the description of this app to be? (max chars: 256)"
		await sourcemsg.edit(embed=e)
		resp = await bot.wait_for('message', check=check, timeout=timeout)
		await resp.delete()
		description = resp.content
		e.description = "What would you like your first question to be? (max chars: 256)"
		await sourcemsg.edit(embed=e)
		while True:
			resp = await bot.wait_for('message', check=check, timeout=timeout)
			if len(resp.content) > 256:
				await sourcemsg.edit(embed=discord.Embed(title=title, description=f"too long. try again. "
																				f"({len(resp.content)} / 256)",
														color=discord.Color.dark_gold()))
			else:
				questions.append(resp.content)
				break
		e = discord.Embed(title=f"apply for: {name}", color=discord.Color.blue())
		e.add_field(name=questions[0], value='*(response goes here)*', inline=False)
		await sourcemsg.edit(embed=e)
		guide = discord.Embed(title="Create an application!", color=discord.Color.gold())
		if setup:
			guide.description = "Alright, so your first question is set! you will see a live update on the above embed of " \
								"what people applying will see!\n\nto undo your previous response, you can say \"--undo\" " \
								"and the bot will remove the question. ready to continue? just say your next question!\n\nDone?" \
								"say `--finish`!"
		else:
			guide.description = "```\nFinish application: --finish\nUndo last question: --undo\n```"
		guide.set_footer(icon_url='http://www.kidsmathgamesonline.com/images/pictures/numbers600/number25.jpg',
						text="Due to discord being very strict, you have a limit of 25 questions per app.")
		guidemsg = await dest.send(embed=guide)
		await guidemsg.edit(embed=guide)
		await sourcemsg.edit(embed=e)
		while True:
			if len(questions) == 24:
				await dest.send("**warning**: this is your last question.", delete_after=20)
			elif len(questions) == 25:
				break
			q = await bot.wait_for('message', check=check, timeout=timeout)
			if isinstance(dest, discord.TextChannel):
				if dest.guild:
					await q.delete(delay=0.5)
			if q.content.lower() == '--undo':
				questions.pop()  # removes last item in the list
				e.remove_field(len(e.fields) - 1)  # remove the last field
				e.description = f'Total questions: {len(questions)}||/25||\nTotal Characters: {len(e)}||/6000||'
			elif q.content.lower() == '--finish':
				break
			else:
				questions.append(q.content)
				e.add_field(name=questions[len(questions) - 1], value="*(response goes here)*", inline=False)
				e.description = f'Total questions: {len(questions)}||/25||\nTotal Characters: {len(e)}||/6000||'
			await sourcemsg.edit(embed=e)
		await guidemsg.edit(embed=guide)
		await sourcemsg.edit(embed=e)
		x = await dest.send(
			embed=discord.Embed(
				title="Do you want the applier to get roles if they are accepted?",
				color=discord.Color.blue()
			)
		)
		yes = '\U00002705'
		no = '\U0000274c'
		await x.add_reaction(yes)
		await x.add_reaction(no)
		r, u = await bot.wait_for('reaction_add', check=lambda r, u: str(r.emoji) in [yes,
																					  no] and r.message.id == x.id and u.id == ctx.author.id,
								  timeout=timeout)
		ADD_ROLE = None
		if str(r.emoji) == yes:
			while True:
				await x.edit(embed=discord.Embed(
				title="what is the role's Name?", color=discord.Color.blue()
				))
				rolee = await bot.wait_for('message', check=check)
				for role in ctx.guild.roles:
					if role.name.lower().startswith(rolee.content.lower().replace('@', '')):
						if ctx.guild:
							await rolee.delete(delay=0.3)
						ADD_ROLE = role
						break

				else:
					await x.edit(embed=discord.Embed(title="Not Found", description="Try again.", color=discord.Color.purple()))
					continue
				break
			ADD_ROLE = ADD_ROLE
		await x.edit(embed=discord.Embed(
			title="Do you want to save this application?", color=discord.Color.gold()
		))
		await x.remove_reaction(r.emoji, ctx.author)
		r, u = await bot.wait_for('reaction_add', check=lambda r, u: str(r.emoji) in [yes, no] and r.message.id == x.id and u.id == ctx.author.id, timeout=timeout)
		if str(r.emoji) == yes:
			pass
		else:
			raise CancelledError
		e.description = description
		e = e.to_dict()
		e['reward_role'] = ADD_ROLE
		e['PURE_QUESTIONS'] = questions
		return e

	async def get_responses(self, ctx, app=None, *, questions):
		e = discord.Embed(title="Apply", description="answer the following questions.\n\nwant to cancel? type `--abort`",
						color=discord.Color.blue())
		msg = await ctx.send(embed=e)
		responses = []
		for num, question in enumerate(questions, start=1):
			e.add_field(name=str(num) + '. ' + question, value="Your response...")
			await msg.edit(embed=e)
			q_r = await ctx.bot.wait_for('message', check=lambda m: (m.author, m.channel) == (ctx.author, ctx.channel),
										 timeout=600)
			if q_r.content.lower() == '--abort':
				raise TimeoutError
			e.remove_field(len(e.fields) - 1)
			e.add_field(name=str(num) + '. ' + question, value=q_r.content)
			continue
		return e
