import os
import shutil
import subprocess
import zipfile
from typing import Tuple, List, Optional
from version import update_version_txt

# Files or folders common to all bots.

common_sharpy = [
    ("jsonpickle", None),
    ("sharpy", None),
    (os.path.join("python-sc2", "sc2"), "sc2"),
    ("sc2pathlibp", None),
    ("config.py", None),
    ("ladder.py", None),
]

common = [
    ("requirements.txt", None),
    ("version.txt", None),
    ("config.ini", None),
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

json_exe = """{
  "Bots": {
    "[NAME]": {
      "Race": "[RACE]",
      "Type": "cppwin32",
      "RootPath": "./",
      "FileName": "[NAME].exe",
      "Debug": false
    }
  }
}"""


class LadderZip:
    archive: str
    files: List[Tuple[str, Optional[str]]]

    def __init__(
        self,
        archive_name: str,
        race: str,
        files: List[Tuple[str, Optional[str]]],
        common_files: List[Tuple[str, Optional[str]]] = None,
    ):
        self.name = archive_name
        self.race = race
        self.archive = archive_name + ".zip"

        self.files = files
        if common_files:
            self.files.extend(common_files)
        else:
            self.files.extend(common)
            self.files.extend(common_sharpy)

        # Executable
        # --specpath /opt/bk/spec --distpath /opt/bk/dist --workpath /opt/bk/build

        self.pyinstaller = (
            'pyinstaller -y --add-data "[FOLDER]/sc2pathlibp'
            '";"sc2pathlibp/" --add-data "[FOLDER]/sc2";"sc2/" '
            '--add-data "[FOLDER]/config.ini";"." --add-data '
            '"[FOLDER]/version.txt";"."  '
            '"[FOLDER]/run.py" '
            '--add-binary="C:\\Windows\\System32\\vcomp140.dll";"." '
            '-n "[NAME]" '
            '--distpath "[OUTPUTFOLDER]"'
        )

    def create_json(self):
        return json.replace("[NAME]", self.name).replace("[RACE]", self.race)

    def create_bin_json(self):
        return json_exe.replace("[NAME]", self.name).replace("[RACE]", self.race)

    def pre_zip(self):
        """ Override this as needed, actions to do before creating the zip"""
        pass

    def post_zip(self):
        """ Override this as needed, actions to do after creating the zip"""
        pass

    def package_executable(self, output_dir: str):
        zip_name = f"{self.name}_bin.zip"
        print()
        print("unzip")
        zip_path = os.path.join(output_dir, self.archive)
        source_path = os.path.join(output_dir, self.name + "_source")
        bin_path = os.path.join(output_dir, self.name)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(source_path)

        print("run pyinstaller")
        self.pyinstaller = (
            self.pyinstaller.replace("[FOLDER]", source_path)
            .replace("[OUTPUTFOLDER]", bin_path)
            .replace("[NAME]", self.name)
        )

        print(self.pyinstaller)
        subprocess.run(self.pyinstaller)

        # Reset bin path as pyinstaller likes to make a new run folder
        run_path = os.path.join(bin_path, self.name)

        # remove PIL and cv2
        print("removing PIL and cv2")
        shutil.rmtree(os.path.join(run_path, "cv2"))
        shutil.rmtree(os.path.join(run_path, "PIL"))
        # Create new ladderbots.json
        f = open(os.path.join(run_path, "ladderbots.json"), "w+")
        f.write(self.create_bin_json())
        f.close()

        print("Zip executable version")
        zipf = zipfile.ZipFile(os.path.join(output_dir, zip_name), "w", zipfile.ZIP_DEFLATED)
        LadderZip.zipdir(run_path, zipf, run_path)
        zipf.close()
        shutil.rmtree(bin_path)
        shutil.rmtree(source_path)

    def create_ladder_zip(self, exe: bool):

        print()

        archive_name = self.archive

        bot_specific_paths = self.files

        # Remove previous archive
        if os.path.isfile(archive_name):
            print(f"Deleting {archive_name}")
            os.remove(archive_name)

        files_to_zip = []
        directories_to_zip = []
        files_to_delete = []

        f = open("ladderbots.json", "w+")
        f.write(self.create_json())
        f.close()

        self.pre_zip()

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
        zipf = zipfile.ZipFile(archive_name, "w", zipfile.ZIP_DEFLATED)
        for file in files_to_zip:
            zipf.write(file)
        for directory in directories_to_zip:
            LadderZip.zipdir(directory, zipf)
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

        if not os.path.exists("publish"):
            os.mkdir("publish")

        shutil.move(archive_name, os.path.join("publish", archive_name))
        self.post_zip()

        print(f"\nSuccessfully created {os.path.join('publish', archive_name)}")

        if exe:
            self.package_executable("publish")

    @staticmethod
    def zipdir(path: str, ziph: zipfile.ZipFile, remove_path: Optional[str] = None):
        # ziph is zipfile handle
        for root, dirs, files in os.walk(path):
            for file in files:
                if "__pycache__" not in root:
                    path_to_file = os.path.join(root, file)
                    if remove_path:
                        ziph.write(path_to_file, path_to_file.replace(remove_path, ""))
                    else:
                        ziph.write(path_to_file)
