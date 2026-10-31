import bisect
import re
from dataclasses import dataclass
from functools import cached_property

REGEX_AFTER_CHARS = set("(,=:[!&|?{};+-*%<>~^")
REGEX_AFTER_WORDS = {"return", "typeof", "case", "do", "else", "in", "of", "new", "delete", "void", "throw"}
BLOCK_KEYWORDS = {"if", "for", "while", "switch", "catch", "with"}
OBJECT_KEY = re.compile(r"\s*([A-Za-z_$][\w$]*)\s*[:,}]")


@dataclass
class Source:
	"""A JS script read as a regex scan reads it.

	`code` blanks comments and the contents of strings, template text and regex literals
	(quotes stay); `text` blanks only comments. Both keep the script's length and newlines,
	so an offset in one is the same place in the other and in the script.
	"""

	script: str

	def __post_init__(self):
		self.text, self.code = _strip(self.script)

	def line(self, offset: int) -> int:
		return bisect.bisect_left(self._newlines, offset) + 1

	def depth(self, offset: int) -> int:
		"""Braces open before `offset`."""
		return self._depths[offset]

	def closing(self, offset: int) -> int:
		"""The offset of the bracket that closes the one at `offset`, or the end."""
		pairs = {"{": "}", "(": ")", "[": "]"}
		opener, closer = self.code[offset], pairs[self.code[offset]]
		level = 0
		for i in range(offset, len(self.code)):
			if self.code[i] == opener:
				level += 1
			elif self.code[i] == closer:
				level -= 1
				if level == 0:
					return i
		return len(self.code)

	def literal(self, start: int, end: int) -> str | None:
		"""The string literal that starts the span, unquoted, or None when it is not a literal."""
		raw = self.text[start:end].strip()
		if len(raw) >= 2 and raw[0] in "'\"`" and raw[-1] == raw[0]:
			return raw[1:-1]
		return None

	def function_bodies(self, start: int, end: int) -> list[tuple[int, int]]:
		"""Spans of the function bodies that open between `start` and `end`."""
		bodies = []
		for i in range(start, end):
			if self.code[i] == "{" and self._opens_function(i):
				bodies.append((i, self.closing(i)))
		return bodies

	def object_keys(self, offset: int) -> list[tuple[str, int]]:
		"""The keys of the object literal whose `{` is at `offset`, with their offsets."""
		keys, level = [], 0
		for i in range(offset, self.closing(offset)):
			level += (self.code[i] in "([{") - (self.code[i] in ")]}")
			if level == 1 and self.code[i] in "{,":
				key = OBJECT_KEY.match(self.code, i + 1)
				if key:
					keys.append((key.group(1), key.start(1)))
		return keys

	def _opens_function(self, offset: int) -> bool:
		end = _skip_space_back(self.code, offset - 1)
		if self.code[end - 1 : end + 1] == "=>":
			return True
		if end < 0 or self.code[end] != ")":
			return False
		return _word_before(self.code, _opening(self.code, end)) not in BLOCK_KEYWORDS

	@cached_property
	def _newlines(self) -> list[int]:
		return [i for i, ch in enumerate(self.code) if ch == "\n"]

	@cached_property
	def _depths(self) -> list[int]:
		depths, level = [], 0
		for ch in self.code:
			depths.append(level)
			level += (ch == "{") - (ch == "}")
		depths.append(level)
		return depths


def _strip(script: str) -> tuple[str, str]:
	text, code = list(script), list(script)
	i, n = 0, len(script)
	templates = []  # brace depth of each `${` we are inside, innermost last
	braces = 0

	def blank(buffers, a, b):
		for buffer in buffers:
			for k in range(a, b):
				if buffer[k] != "\n":
					buffer[k] = " "

	while i < n:
		ch = script[i]
		nxt = script[i + 1] if i + 1 < n else ""
		if ch == "/" and nxt == "/":
			end = script.find("\n", i)
			end = n if end == -1 else end
			blank((text, code), i, end)
			i = end
		elif ch == "/" and nxt == "*":
			end = script.find("*/", i + 2)
			end = n if end == -1 else end + 2
			blank((text, code), i, end)
			i = end
		elif ch in "'\"":
			end = _string_end(script, i + 1, ch)
			blank((code,), i + 1, end - 1)
			i = end
		elif ch == "`" or (ch == "}" and templates and templates[-1] == braces):
			if ch == "}":
				templates.pop()
			end, opens_expression = _template_end(script, i + 1)
			blank((code,), i + 1, end - 2 if opens_expression else end - 1)
			if opens_expression:
				templates.append(braces)
			i = end
		elif ch == "/" and _regex_may_start(script, i):
			end = _regex_end(script, i + 1)
			blank((code,), i + 1, end - 1)
			i = end
		else:
			braces += (ch == "{") - (ch == "}")
			i += 1
	return "".join(text), "".join(code)


def _string_end(script: str, i: int, quote: str) -> int:
	while i < len(script) and script[i] not in (quote, "\n"):
		i += 2 if script[i] == "\\" else 1
	return min(i + 1, len(script))


def _template_end(script: str, i: int) -> tuple[int, bool]:
	"""Scan template text from `i`: the offset after its end and whether a `${` ended it."""
	while i < len(script):
		if script[i] == "\\":
			i += 2
		elif script[i] == "`":
			return i + 1, False
		elif script.startswith("${", i):
			return i + 2, True
		else:
			i += 1
	return len(script), False


def _regex_may_start(script: str, i: int) -> bool:
	end = _skip_space_back(script, i - 1)
	if end < 0 or script[end] in REGEX_AFTER_CHARS:
		return True
	return _word_before(script, end + 1) in REGEX_AFTER_WORDS


def _skip_space_back(text: str, i: int) -> int:
	while i >= 0 and text[i].isspace():
		i -= 1
	return i


def _word_before(text: str, offset: int) -> str:
	"""The identifier that ends just before `offset`, spaces between allowed."""
	end = _skip_space_back(text, offset - 1)
	start = end
	while start >= 0 and (text[start].isalnum() or text[start] in "_$"):
		start -= 1
	return text[start + 1 : end + 1]


def _regex_end(script: str, i: int) -> int:
	in_class = False
	while i < len(script) and script[i] != "\n":
		ch = script[i]
		if ch == "\\":
			i += 2
			continue
		if ch == "[":
			in_class = True
		elif ch == "]":
			in_class = False
		elif ch == "/" and not in_class:
			return i + 1
		i += 1
	return i


def _opening(code: str, offset: int) -> int:
	level = 0
	for i in range(offset, -1, -1):
		if code[i] == ")":
			level += 1
		elif code[i] == "(":
			level -= 1
			if level == 0:
				return i
	return 0
