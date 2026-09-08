PYTHON_SEPARATORS: list[str] = [
    # First, try to split along class definitions
    "\nclass ",
    "\ndef ",
    "\n\tdef ",
    # Now split by the normal type of lines
    "\n\n",
    "\n",
    " ",
    "",
]


MARKDOWN_SPERATORS: list[str] = [
    # First, try to split along Markdown headings (starting with level 2)
    "\n#{1,6} ",
    # Note the alternative syntax for headings (below) is not handled here
    # Heading level 2
    # ---------------
    # End of code block
    "```\n",
    # Horizontal lines
    "\n\\*\\*\\*+\n",
    "\n---+\n",
    "\n___+\n",
    # Note that this splitter doesn't handle horizontal lines defined
    # by *three or more* of ***, ---, or ___, but this is not handled
    "\n\n",
    "\n",
    " ",
    "",
]
