from textual.widgets import Static, Markdown, Rule
from textual.containers import Horizontal

class Message(Static):
	DEFAULT_CSS = """
	#container {
		# border: solid blue;
		height: auto;
		margin: 1;
	}

	#sender {
		padding: 1;
		width: 0.2fr;
		# border: solid red;
		text-align: right;
		background: #666666;
		height: 100%;
	}
	#content {
		padding: 1;
		width: 0.8fr;
		# border: solid blue;
		text-align: left;
		background: #333333;
		height: auto;
	}
	"""

	def __init__(self, sender: str = "sender", content: str = "content", *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._sender = sender
		self._content = content

	def compose(self):
		with Horizontal(id="container"):
			yield Static(self._sender, id="sender")
			yield Markdown(self._content, id="content")

	def set_sender(self, sender: str):
		self.query_one("#sender").content = str(sender)

	def set_content(self, content: str):
		self.query_one("#content").content = str(content)