import json, traceback, datetime, time
class json_mngr:
	class IdNotFound(Exception):
		pass

	def handle_modify(self, fp: str, newdata: dict, indent=2, *, backup: bool = False, ret_data: bool = True):
		if backup:
			with open(fp, 'r') as back:
				hackup = json.load(back)
		try:
			with open(fp, 'w') as alafile:
				try:
					json.dump(newdata, alafile, indent=indent)
					if ret_data:
						time.sleep(1)
						return self.read(fp)
					else:
						return
				except:
					json.dump(backup, alafile, indent=indent)
					return traceback.format_exc()
		except:
			return traceback.format_exc()

	def read(self, fp):
		try:
			with open(fp, 'r') as alafile:
				try:
					z = json.load(alafile)
					return z
				except:
					return traceback.format_exc()
		except:
			return traceback.format_exc()

	async def find(self, fp, *, in_key: str, thing, direct_path: str = None):
		with open(fp, 'r') as tofind:
			data = json.load(tofind)
			if data:
				if in_key in data.keys():
					if thing in data[in_key].keys():
						return data[in_key][thing]
				else:
					raise self.IdNotFound(f"{in_key} not found in {data}")

class Formatting:
	@staticmethod
	def escape(text, *, mass_mentions=True, formatting=False, invites=False, mentions=False, urls=False):
		if mass_mentions:
			text = text.replace("@everyone", "@\u200beveryone")
			text = text.replace("@here", "@\u200bhere")
		if formatting:
			text = (text.replace("`", "\\`")
					.replace("*", "\\*")
					.replace("_", "\\_")
					.replace("~", "\\~")
					.replace('|', '\\|'))
		if invites:
			# invites are basically sub of urls, since urls do this to the https part
			text = text.replace('ord.gg', 'ord\u200b.gg')

		if mentions:
			text = text.replace('@', '@\u200b').replace('#', '#\u200b')

		if urls:
			text = text.replace('http', 'http\u200b')
		return text

	@classmethod
	def date(cls, datetime_format):
		return datetime_format.strftime('%d/%m/%Y %Z')

	@classmethod
	def time(cls, datetime_format):
		return datetime_format.strftime("%I:%M %p")

	@classmethod
	def both(cls, datetime_format):
		return datetime_format.strftime(f"{cls.time(datetime_format)} @ {cls.date(datetime_format)}")

	@classmethod
	def dynamic_time(cls, time):
		date_join = datetime.datetime.strptime(str(time), "%Y-%m-%d %H:%M:%S.%f")
		date_now = datetime.datetime.now(datetime.timezone.utc)
		date_now = date_now.replace(tzinfo=None)
		since_join = date_now - date_join

		m, s = divmod(int(since_join.total_seconds()), 60)
		h, m = divmod(m, 60)
		d, h = divmod(h, 24)

		if d > 0:
			msg = "{0}d {1}h {2}m {3}s ago"
		elif d == 0 and h > 0:
			msg = "{1}h {2}m {3}s ago"
		elif d == 0 and h == 0 and m > 0:
			msg = "{2}m {3}s ago"
		elif d == 0 and h == 0 and m == 0 and s > 0:
			msg = "{3}s ago"
		else:
			msg = ""
		return msg.format(d, h, m, s)

	@classmethod
	def pagify(cls, text: str, delims=["\n"], *, escape=False, shorten_by=0,
			   page_length=1900):
		"""DOES NOT RESPECT MARKDOWN BOXES OR INLINE CODE"""
		in_text = text
		if escape:
			num_mentions = text.count("@here") + text.count("@everyone")
			shorten_by += num_mentions
		page_length -= shorten_by
		while len(str(in_text)) > page_length:
			closest_delim = max([in_text.rfind(d, 0, page_length)
								 for d in delims])
			closest_delim = closest_delim if closest_delim != -1 else page_length
			if escape:
				to_send = cls.escape(in_text[:closest_delim])
			else:
				to_send = in_text[:closest_delim]
			yield to_send
			in_text = in_text[closest_delim:]

		if escape:
			yield cls.escape(in_text)
		else:
			yield in_text


