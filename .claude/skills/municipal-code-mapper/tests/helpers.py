import json, os, shutil, subprocess, sys, tempfile, unittest

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(SKILL, "scripts")
FIX = os.path.join(SKILL, "examples", "eastvale-9.10")
GOLD = os.path.join(FIX, "golden")
SOURCE = os.path.join(FIX, "source.md")


def run(script, *args, check=False):
    """Run a script as a subprocess (isolated mode); returns CompletedProcess."""
    p = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, script), *map(str, args)], capture_output=True, text=True)
    if check and p.returncode:
        raise AssertionError(f"{script} failed ({p.returncode}):\n{p.stdout}\n{p.stderr}")
    return p


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def dump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


class TmpCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="mapper-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def golden_copy(self):
        d = os.path.join(self.tmp, "golden")
        shutil.copytree(GOLD, d)
        return d

    def write(self, name, text):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p
