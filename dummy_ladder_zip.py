import os

import argparse

from bot_loader import BotDefinitions
from version import update_version_txt

root_dir = os.path.dirname(os.path.abspath(__file__))


def main():
    definitions = BotDefinitions()
    zip_types = definitions.zippable
    zip_keys = list(zip_types.keys())
    zip_keys.append("all")

    parser = argparse.ArgumentParser(
        description="Create a Ladder Manager ready zip archive for SC2 AI, AI Arena, Probots, ..."
    )
    parser.add_argument("-n", "--name", help=f"Bot name: {zip_keys}.")
    parser.add_argument("-e", "--exe", help="Also make executable (Requires pyinstaller)", action="store_true")
    args = parser.parse_args()

    bot_name = args.name

    if not os.path.exists("dummy"):
        os.mkdir("dummy")

    update_version_txt()

    if bot_name == "all" or not bot_name:
        zip_keys.remove("all")
        for key in zip_keys:
            zip_types.get(key).create_ladder_zip(args.exe)
    else:
        if bot_name not in zip_keys:
            raise ValueError(f"Unknown bot: {bot_name}, allowed values are: {zip_keys}")

        zip_types.get(bot_name).create_ladder_zip(args.exe)


if __name__ == "__main__":
    main()
