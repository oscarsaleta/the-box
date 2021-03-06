import logging
import pathlib
import random
from typing import List, Tuple

import logging_configurator
import pandas as pd
import plac

LOGGER = logging.getLogger("the-box")
logging_configurator.configure_logging(log_level="DEBUG")

BOX_ITEM_EXPIRATION = 4
HARDCORE_START = 15


class Player:
    name: str
    house_items: List[str]
    missing_house_items: List[str]
    box_items: List[Tuple[str, int]]

    def __init__(self, name: str, starting_items: List[str]):
        self.name = name
        self.house_items = starting_items.copy()
        self.missing_house_items = []
        self.box_items = []

    @property
    def is_missing_items(self) -> bool:
        return len(self.missing_house_items) > 0

    def lose_random_house_item(self):
        """Move an item from house_items to missing_house_items"""
        try:
            removed_item = self.house_items.pop(random.randrange(len(self.house_items)))
        except Exception:
            print(f"{self.name} cannot lose anything because they have nothing!")
            return

        print(f"{self.name} loses the {removed_item}. They now have: {', '.join(self.house_items)}.")
        self.missing_house_items.append(removed_item)

    def retrieve_random_house_item(self):
        """Move an item from missing_house_items to house_items"""
        try:
            retrieved_item = self.missing_house_items.pop(random.randrange(len(self.missing_house_items)))
        except Exception:
            print(f"{self.name} cannot retrieve any items because they have everything!")
            return

        self.house_items.append(retrieved_item)
        print(f"{self.name} retrieves the {retrieved_item}. They now have: {', '.join(self.house_items)}.")

    def get_box_item(self, item: str, turn: int):
        """Get a new item from The Box. The turn is when the player got the item, but we store it as the turn that it
        will expire"""
        print(f"{self.name} got a {item} from The Box! It will expire in {BOX_ITEM_EXPIRATION} turns")
        self.box_items.append((item, turn + BOX_ITEM_EXPIRATION))

    def cleanup_box_items(self, turn: int) -> str:
        """Remove all gifts from The Box that expired"""
        try:
            returned_item = [item for item in self.box_items if turn >= item[1]][0]
        except Exception:
            return 0
        self.box_items = [item for item in self.box_items if turn < item[1]]
        print(f"{self.name}'s {returned_item[0]} expired!")
        return returned_item[0]

    def __repr__(self):
        return self.name


class TheBox:
    path: pathlib.Path
    house_items: List[str]
    box_items: List[str]

    def __init__(self, box_items: int):
        self.path = pathlib.Path(__file__).parent.absolute()

        self.house_items = self._read_house_items()
        self.box_items = [i + 1 for i in range(box_items)]
        self.original_box_items = [i + 1 for i in range(box_items)]

        self.players = [Player(name=name, starting_items=self.house_items) for name in self._read_players()]

        self.turn = 0

    def _read_house_items(self) -> List[str]:
        """Read house items list"""
        house_items_file = self.path / "house-objects.csv"
        return pd.read_csv(house_items_file, header=None)[0].to_list()

    def _read_players(self) -> List[str]:
        """Read players list"""
        players_file = self.path / "players.csv"
        return pd.read_csv(players_file, header=None)[0].to_list()

    def random_box_item(self) -> str:
        return self.box_items.pop(random.randrange(len(self.box_items)))

    def _retrieve_or_gift(self) -> int:
        result = None
        while result != "1" and result != "2":
            result = input("Type your preference: (1 = retrieve item, 2 = gift from The Box)\n")
        return result

    def one_day(self, hardcore: bool = False):
        print("\n==========================")
        print(f"DAY {self.turn}")

        LOGGER.debug("Current status, day %s:", self.turn)
        LOGGER.debug(
            "Box missing items: %s", sorted(list(set(self.original_box_items).difference(set(self.box_items))))
        )
        for player in self.players:
            LOGGER.debug("%s", player.name)
            LOGGER.debug(" - has items: %s", ", ".join(sorted(player.house_items)))
            LOGGER.debug(" - is missing items: %s", ", ".join(sorted(player.missing_house_items)))
            LOGGER.debug(" - has from the box: %s", ", ".join(sorted([str(x[0]) for x in player.box_items])))

        # 5 PM
        print()
        print("It's 5 PM!")
        # Lose expired gifts
        for player in self.players:
            returned_item = player.cleanup_box_items(turn=self.turn)
            if returned_item != 0:
                self.box_items.append(returned_item)
        if not hardcore:
            # Someone will retrieve an item or get a gift from The Box
            winner = random.choice(self.players)
            print(f"{winner.name} is our lucky player!")
            if winner.is_missing_items:
                print("Will they retrieve a lost item or claim a gift from The Box?")
                if self._retrieve_or_gift() == "1":
                    winner.retrieve_random_house_item()
                else:
                    winner.get_box_item(self.random_box_item(), self.turn)
            else:
                print("They have all the items, so The Box rewards them with a gift!")
                winner.get_box_item(self.random_box_item(), self.turn)
        else:

            # Lose a house item
            loser = random.choice(self.players)
            print(f"Oh, {loser.name} is out of luck. They lose an item!")
            loser.lose_random_house_item()
        # 9 PM
        print()
        print(f"It's 9 PM!")
        loser = random.choice(self.players)
        print(f"Unlucky {loser.name}...")
        loser.lose_random_house_item()

    def play(self):
        print(f"\nWELCOME TO THE BOX")
        print(
            f"Today's players are: {', '.join([player.name for player in self.players])}."
            " Who will be the last one standing?"
        )
        print(f"Let the game begin! May The Box be with you!\n")
        for turn in range(1, HARDCORE_START + 1):
            self.turn = turn
            self.one_day()
            input("\nPress enter to advance to the next day!")
        while self.turn >= HARDCORE_START:
            self.turn += 1
            self.one_day(hardcore=True)
            input("\nPress enter to advance to the next day!")


@plac.annotations(box_items=plac.Annotation(help="Number of items in the box", type=int))
def main(box_items: int):
    game = TheBox(box_items=box_items)
    game.play()


if __name__ == "__main__":
    plac.call(main)
