import os
import shutil
import subprocess

import argparse
import zipfile
from typing import Tuple, List, Optional

from version import update_version_txt

root_dir = os.path.dirname(os.path.abspath(__file__))

# Files or folders common to all bots.
common = [
    ("jsonpickle", None),
    (os.path.join("python-sc2", "sc2"), "sc2"),
    ("sc2pathlibp", None),
    ("requirements.txt", None),
    ("version.txt", None),
    ("config.py", None),
    ("config.ini", None),
    ("ladder.py", None),
    ("ladderbots.json", None),
]
json = """{
  "Bots": {
    "[NAME]": {
      "Race": "[RACE]",
      "Type": "Python",
      "RootPath": "./",
      "FileName": "run.py",
      "Debug": false
    }
  }
}"""

class LadderZip:
    archive: str
    files: List[Tuple[str, Optional[str]]]
    
    def __init__(self, archive_name: str, race: str,
                 files: List[Tuple[str, Optional[str]]],
                 common_files: List[Tuple[str, Optional[str]]] = None):
        self.name = archive_name
        self.race = race
        self.archive = archive_name + ".zip"

        self.files = files
        if common_files:
            self.files.extend(common_files)
        else:
            self.files.extend(common)

    def create_json(self):
        return json.replace("[NAME]", self.name).replace("[RACE]", self.race)

    def pre_zip(self):
        """ Override this as needed, actions to do before creating the zip"""
        pass

    def post_zip(self):
        """ Override this as needed, actions to do after creating the zip"""
        pass

class DummyZip(LadderZip):

    def __init__(self, archive_name: str, race: str, file: str):
        self.dummy_file = file
        self.new_dummy_file = os.path.join(root_dir, "dummy", "dummy.py")
        files = [
            ("sharpy", None),
            ("dummy", None),
            (os.path.join("dummies", "run.py"), "run.py"),
        ]
        super().__init__(archive_name, race, files)

    def pre_zip(self):
        shutil.copy(self.dummy_file, self.new_dummy_file)

    def post_zip(self):
        os.remove(self.new_dummy_file)


zip_types = {

    # Protoss dummies
    "zealot": DummyZip("SharpKnives", "Protoss", os.path.join("dummies", "protoss", "proxy_zealot_rush.py")),
    "cannonrush": DummyZip("SharpCannon", "Protoss", os.path.join("dummies", "protoss", "cannon_rush.py")),
    "dt": DummyZip("SharpShadows", "Protoss", os.path.join("dummies", "protoss", "dark_templar_rush.py")),
    "4gate": DummyZip("SharpRush", "Protoss", os.path.join("dummies", "protoss", "gate4.py")),
    "stalker": DummyZip("SharpSpiders", "Protoss", os.path.join("dummies", "protoss", "macro_stalkers.py")),
    "robo": DummyZip("SharpRobots", "Protoss", os.path.join("dummies", "protoss", "robo.py")),
    "voidray": DummyZip("SharpRays", "Protoss", os.path.join("dummies", "protoss", "voidray.py")),

    # Terran dummies
    "cyclone": DummyZip("RustyLocks", "Terran", os.path.join("dummies", "terran", "cyclones.py")),
    "oldrusty": DummyZip("OldRusty", "Terran", os.path.join("dummies", "terran", "rusty.py")),
    "bc": DummyZip("FlyingRust", "Terran", os.path.join("dummies", "terran", "battle_cruisers.py")),
    "marine": DummyZip("RustyMarines", "Terran", os.path.join("dummies", "terran", "marine_rush.py")),
    "tank": DummyZip("RustyTanks", "Terran", os.path.join("dummies", "terran", "two_base_tanks.py")),
    "bio": DummyZip("RustyInfantry", "Terran", os.path.join("dummies", "terran", "bio.py")),
    "banshee": DummyZip("RustyScreams", "Terran", os.path.join("dummies", "terran", "banshees.py")),

    # Zerg dummies
    "lings": DummyZip("BluntTeeth", "Zerg", os.path.join("dummies", "zerg", "lings.py")),
    "200roach": DummyZip("BluntRoach", "Zerg", os.path.join("dummies", "zerg", "macro_roach.py")),
    "macro": DummyZip("BluntMacro", "Zerg", os.path.join("dummies", "zerg", "macro_zerg_v2.py")),
    "mutalisk": DummyZip("BluntFlies", "Zerg", os.path.join("dummies", "zerg", "mutalisk.py")),
    "hydra": DummyZip("BluntSpit", "Zerg", os.path.join("dummies", "zerg", "roach_hydra.py")),
    # "spine": DummyZip("BluntDefender", "Zerg", os.path.join("dummies", "debug", "spine_defender.py")),
    "12pool": DummyZip("BluntCheese", "Zerg", os.path.join("dummies", "zerg", "twelve_pool.py")),
    "workerrush": DummyZip("BluntyWorkers", "Zerg", os.path.join("dummies", "zerg", "worker_rush.py")),

    # All
    "all": None
}


def zipdir(path: str, ziph: zipfile.ZipFile):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            if "__pycache__" not in root:
                ziph.write(os.path.join(root, file))


def create_ladder_zip(archive_zip: LadderZip):
    update_version_txt()
    print()

    archive_name = archive_zip.archive

    bot_specific_paths = archive_zip.files

    # Remove previous archive
    if os.path.isfile(archive_name):
        print(f"Deleting {archive_name}")
        os.remove(archive_name)

    files_to_zip = []
    directories_to_zip = []
    files_to_delete = []

    f = open("ladderbots.json", "w+")
    f.write(archive_zip.create_json())
    f.close()

    archive_zip.pre_zip()

    for src, dest in bot_specific_paths:
        if not os.path.exists(src):
            raise ValueError(f"'{src}' does not exist.")

        if dest is None:
            # the file or folder can be used as is.
            if os.path.isdir(src):
                directories_to_zip.append(src)
            else:
                files_to_zip.append(src)
        else:  # need to move the file or folder.

            if os.path.isdir(src):
                shutil.copytree(src, dest)
                directories_to_zip.append(dest)
                files_to_delete.append(dest)
            else:  # src is a file.
                src_file = os.path.basename(src)

                if os.path.isdir(dest):
                    # Join directory with filename
                    dest_path = os.path.join(dest, src_file)
                else:
                    # Rename into another file
                    dest_path = dest

                files_to_zip.append(dest_path)

                print(f"Copying {src} ... {dest_path}")
                files_to_delete.append(dest_path)

                shutil.copy(src, dest_path)

    print()
    print(f"Zipping {archive_name}")
    zipf = zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED)
    for file in files_to_zip:
        zipf.write(file)
    for directory in directories_to_zip:
        zipdir(directory, zipf)
    zipf.close()

    print()
    for file in files_to_delete:

        if os.path.isdir(file):
            print(f"Deleting directory {file}")
            # os.rmdir(file)
            shutil.rmtree(file)
        else:
            print(f"Deleting file {file}")
            os.remove(file)

    os.remove("ladderbots.json")

    if not os.path.exists('publish'):
        os.mkdir('publish')

    shutil.move(archive_name, os.path.join("publish", archive_name))
    archive_zip.post_zip()

    print(f"\nSuccessfully created {os.path.join('publish', archive_name)}")


def get_archive(bot_name: str) -> LadderZip:
    bot_name = bot_name.lower()
    return zip_types.get(bot_name)


def main():
    zip_keys = list(zip_types.keys())
    parser = argparse.ArgumentParser(
        description="Create a Ladder Manager ready zip archive for SC2 AI, AI Arena, Probots, ..."
    )
    parser.add_argument("-n", "--name", help=f"Bot name: {zip_keys}.")

    args = parser.parse_args()

    bot_name = args.name

    if not os.path.exists('dummy'):
        os.mkdir('dummy')

    if bot_name == "all" or not bot_name:
        zip_keys.remove("all")
        for key in zip_keys:
            create_ladder_zip(get_archive(key))
    else:
        if bot_name not in zip_keys:
            raise ValueError(f'Unknown bot: {bot_name}, allowed values are: {zip_keys}')

        create_ladder_zip(get_archive(bot_name))


if __name__ == "__main__":
    main()
