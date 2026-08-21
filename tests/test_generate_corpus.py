
import os
import tempfile

from tools.generate_corpus import generate


def test_copies_chapters_to_out_dir():
    with tempfile.TemporaryDirectory() as tmp:
        ch = os.path.join(tmp, "chapters")
        out = os.path.join(tmp, "corpus")
        os.makedirs(ch)
        with open(os.path.join(ch, "01-x.md"), "w", encoding="utf-8") as f:
            f.write("hello\n")
        written = generate(ch, out)
        assert len(written) == 1
        assert open(written[0], encoding="utf-8").read() == "hello\n"
