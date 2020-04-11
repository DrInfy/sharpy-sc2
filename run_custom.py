import os
import sys

sys.path.insert(1, "python-sc2")

from bot_loader import GameStarter, BotDefinitions
from version import update_version_txt


def main():
    update_version_txt()
    root_dir = os.path.dirname(os.path.abspath(__file__))
    ladder_bots_path = os.path.join("Bots")
    ladder_bots_path = os.path.join(root_dir, ladder_bots_path)
    definitions: BotDefinitions = BotDefinitions(ladder_bots_path)
    starter = GameStarter(definitions)
    starter.play()


if __name__ == "__main__":
    main()
