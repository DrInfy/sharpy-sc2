import os
import shutil
from bot_loader.ladder_zip import LadderZip


class DummyZip(LadderZip):
    def __init__(self, archive_name: str, race: str, file: str, build: str = None):
        root_dir = os.getcwd()
        self.dummy_file = file
        self.new_dummy_file = os.path.join(root_dir, "dummy", "dummy.py")
        self.build = build

        files = [
            ("dummy", None),
            (os.path.join("dummies", "run.py"), "run.py"),
        ]
        super().__init__(archive_name, race, files)

    def pre_zip(self):
        if self.build:
            with open("config.ini", "a", newline="\n") as handle:
                handle.writelines([self.build, ""])
        shutil.copy(self.dummy_file, self.new_dummy_file)

    def post_zip(self):
        if self.build:
            with open("config.ini", "r") as f:
                lines = f.readlines()
            with open("config.ini", "w") as f:
                for line in lines:
                    if self.build not in line:
                        f.write(line)
        os.remove(self.new_dummy_file)
