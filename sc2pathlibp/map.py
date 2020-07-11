from .sc2pathlib import Map
import numpy as np
from typing import List, Optional, Tuple
from .choke import Choke
from .mappings import MapsType
# from sc2 import Point2

class Sc2Map:
    def __init__(self, 
        pathing_grid: np.ndarray,
        placement_grid: np.ndarray,
        height_map: np.ndarray,
        playable_area: 'sc2.position.Rect'):

        self._overlord_spots: Optional[List[Tuple[float, float]]] = None
        self._chokes: Optional[List[Choke]] = None
        
        self.height_map = height_map
        self._map = Map(
            np.swapaxes(pathing_grid, 0, 1),
            np.swapaxes(placement_grid, 0, 1),
            np.swapaxes(height_map, 0, 1), 
            playable_area.x, 
            playable_area.y, 
            playable_area.x + playable_area.width, 
            playable_area.y + playable_area.height
            )

    @property
    def overlord_spots(self)-> List[Tuple[float, float]]:
        if self._overlord_spots is not None:
            return self._overlord_spots
        self._overlord_spots = self._map.overlord_spots
        return self._overlord_spots
    
    @property
    def chokes(self)-> List[Choke]:
        if self._chokes is not None:
            return self._chokes
        self._chokes = self._map.chokes
        return self._chokes

    def enable_colossus_map(self, enabled: bool):
        self._map.influence_colossus_map = enabled
    
    def enable_reaper_map(self, enabled: bool):
        self._map.influence_reaper_map = enabled

    def add_walk_influence(self, points: List['sc.Point2'], influence: float, range: float = 3):
        """
        Influence applied fades up until the specified range
        """
        self._map.add_influence_walk(points, influence, range)

    def add_tank_influence(self, points: List['sc.Point2'], influence: float, tank_min_range: float = 3, tank_max_range: float = 14.5):
        """
        :param tank_min_range: Tank minimum range is 2, adding both unit radiuses to that and we'll estimate it to be 3.
        :param tank_max_range: Same for max range, 13, but but with unit radius, let's say it's 14.5 instead to err on the safe side
        """
        self._map.add_influence_flat_hollow(points, influence, tank_max_range, tank_max_range)
    
    def add_pure_ground_influence(self, points: List['sc.Point2'], influence: float, full_range: float, fade_max_range: float):
        """
        Use this for units that have different ground attack compared to air attack, like Tempests.
        """
        self._map.add_influence_fading(MapsType.PureGround, points, influence, full_range, fade_max_range)

    def add_ground_influence(self, points: List['sc.Point2'], influence: float, full_range: float, fade_max_range: float):
        self._map.add_influence_fading(MapsType.Ground, points, influence, full_range, fade_max_range)

    def add_air_influence(self, points: List['sc.Point2'], influence: float, full_range: float, fade_max_range: float):
        self._map.add_influence_fading(MapsType.Air, points, influence, full_range, fade_max_range)

    def add_both_influence(self, points: List['sc.Point2'], influence: float, full_range: float, fade_max_range: float):
        self._map.add_influence_fading(MapsType.Both, points, influence, full_range, fade_max_range)

    def plot(self, image_name: str = "map", resize: int = 4):
        """
        Uses cv2 to draw current pathing grid.
        
        requires opencv-python

        :param path: list of points to colorize
        :param image_name: name of the window to show the image in. Unique names update only when used multiple times.
        :param resize: multiplier for resizing the image
        :return: None
        """

        image = np.array(self._map.draw_climbs(), dtype=np.uint8)
        image = np.rot90(image, 1)
        image = np.multiply(image, 42)
        self.plot_image(image, image_name, resize)

    def plot_chokes(self, image_name: str = "map", resize: int = 4):
        """
        Uses cv2 to draw current pathing grid.
        
        requires opencv-python

        :param path: list of points to colorize
        :param image_name: name of the window to show the image in. Unique names update only when used multiple times.
        :param resize: multiplier for resizing the image
        :return: None
        """

        image = np.array(self._map.draw_chokes(), dtype=np.uint8)
        image = np.rot90(image, 1)
        # image = np.multiply(image, 42)
        self.plot_image(image, image_name, resize)

    def plot_image(self, image, image_name: str = "map", resize: int = 4):
        import cv2
        resized = cv2.resize(image, dsize=None, fx=resize, fy=resize, interpolation=cv2.INTER_NEAREST)
        cv2.imshow(image_name, resized)
        cv2.waitKey(1)