# noinspection PyUnresolvedReferences
from .sc2pathlib import Map
import numpy as np
from typing import List, Optional, Tuple, Union
from .choke import Choke
from .mappings import MapsType, MapType


class Sc2Map:
    __slots__ = ['_overlord_spots', '_chokes', 'heuristic_accuracy', 'height_map', '_map']

    def __init__(
        self,
        pathing_grid: np.ndarray,
        placement_grid: np.ndarray,
        height_map: np.ndarray,
        playable_area: "sc2.position.Rect",
    ):

        self._overlord_spots: Optional[List[Tuple[float, float]]] = None
        self._chokes: Optional[List[Choke]] = None
        self.heuristic_accuracy = 1  # Octile distance / set to 2 for optimal accuracy but less performance

        self.height_map = height_map
        self._map = Map(
            np.swapaxes(pathing_grid, 0, 1),
            np.swapaxes(placement_grid, 0, 1),
            np.swapaxes(height_map, 0, 1),
            playable_area.x,
            playable_area.y,
            playable_area.x + playable_area.width,
            playable_area.y + playable_area.height,
        )

    @property
    def map(self) -> Map:
        """
        In case you need to call the rust object directly.
        """
        return self._map

    @property
    def overlord_spots(self) -> List[Tuple[float, float]]:
        if self._overlord_spots is not None:
            return self._overlord_spots
        self._overlord_spots = self._map.overlord_spots
        return self._overlord_spots

    @property
    def chokes(self) -> List[Choke]:
        if self._chokes is not None:
            return self._chokes
        self._chokes = self._map.chokes
        return self._chokes


    def reset(self):
        self._map.reset()

    def calculate_zones(self, sorted_base_locations: List[Tuple[float, float]]):
        """
        Use this on initialization to calculate zones.
        Zones start from 1 onwards.
        Zone 0 is empty zone.
        """
        self._map.calculate_zones(sorted_base_locations)

    def get_zone(self, position: Tuple[float, float]) -> int:
        """
        Zones start from 1 onwards.
        Zone 0 is empty zone.
        """
        return self._map.get_zone(position)
    
    def calculate_connections(self, start: Tuple[float, float]):
        """
        Calculates ground connections to a single point in the map.
        Use `is_connected` the check if a location is connected.
        """
        self._map.calculate_connections(start)

    def is_connected(self, start: Tuple[float, float]) -> bool:
        """
        Check if a point is connected to earlier start position used in `calculate_connections`
        If `calculate_connections` was not run, returns False.
        """
        return self._map.is_connected(start)

    def remove_connection(self, start: Tuple[float, float]) -> bool:
        """
        Remove a 'connection' from location. This can be used to disable warp-ins in certain areas.
        """
        return self._map.remove_connection(start)
    

    def normalize_influence(self, value: int):
        self._map.normalize_influence(value)

    def enable_colossus_map(self, enabled: bool):
        self._map.influence_colossus_map = enabled

    def enable_reaper_map(self, enabled: bool):
        self._map.influence_reaper_map = enabled

    def create_block(self, center: Union[Tuple[float, float], List[Tuple[float, float]]], size: Tuple[int, int]):
        if isinstance(center, list):
            self._map.create_blocks(center, size)
        else:
            self._map.create_block(center, size)

    def remove_block(self, center: Union[Tuple[float, float], List[Tuple[float, float]]], size: Tuple[int, int]):
        if isinstance(center, list):
            self._map.remove_blocks(center, size)
        else:
            self._map.remove_block(center, size)

    def add_walk_influence(self, points: List["sc.Point2"], influence: float, range: float = 3):
        """
        Influence applied fades up until the specified range
        """
        self._map.add_influence_walk(points, influence, range)

    def add_tank_influence(
        self, points: List["sc.Point2"], influence: float, tank_min_range: float = 2.5, tank_max_range: float = 14.5
    ):
        """
        :param tank_min_range: Tank minimum range is 2, adding both unit radiuses to that and we'll estimate it to be 2.5.
        :param tank_max_range: Same for max range, 13, but but with unit radius, let's say it's 14.5 instead to err on the safe side
        """
        self._map.add_influence_flat_hollow(points, influence, tank_min_range, tank_max_range)

    def add_pure_ground_influence(
        self, points: List["sc.Point2"], influence: float, full_range: float, fade_max_range: float
    ):
        """
        Use this for units that have different ground attack compared to air attack, like Tempests.
        """
        self._map.add_influence_fading(MapsType.PureGround, points, influence, full_range, fade_max_range)

    def add_ground_influence(
        self, points: List["sc.Point2"], influence: float, full_range: float, fade_max_range: float
    ):
        self._map.add_influence_fading(MapsType.Ground, points, influence, full_range, fade_max_range)

    def add_air_influence(self, points: List["sc.Point2"], influence: float, full_range: float, fade_max_range: float):
        self._map.add_influence_fading(MapsType.Air, points, influence, full_range, fade_max_range)

    def add_both_influence(self, points: List["sc.Point2"], influence: float, full_range: float, fade_max_range: float):
        self._map.add_influence_fading(MapsType.Both, points, influence, full_range, fade_max_range)

    def current_influence(self, map_type: MapType, position: Tuple[float, float]):
        """
        Finds the current influence in the position
        """
        return self._map.current_influence(map_type, position)

    def add_influence_without_zones(self, zones: List[int], value: float):
        """
        Add specified amount of influence to areas that not within specified zones.
        This can be useful in making sure units do not follow enemies outside main.
        Zones start from 1 onwards.
        Zone 0 is empty zone.
        """
        self._map.add_influence_without_zones(zones, int(value))
    

    def find_path(
        self, map_type: MapType, start: Tuple[float, float], end: Tuple[float, float], large: bool = False
    ) -> Tuple[List[Tuple[int, int]], float]:
        """
        Finds a path ignoring influence.

        :param start: Start position in float tuple
        :param end: Start position in float tuple
        :param large: Unit is large and requires path to have width of 2 to pass
        :return: Tuple of points and total distance.
        """

        if large:
            return self._map.find_path_large(map_type, start, end, self.heuristic_accuracy)
        return self._map.find_path(map_type, start, end, self.heuristic_accuracy)

    def find_path_influence(
        self, map_type: MapType, start: Tuple[float, float], end: Tuple[float, float], large: bool = False
    ) -> Tuple[List[Tuple[int, int]], float]:
        """
        Finds a path that takes influence into account

        :param start: Start position in float tuple
        :param end: Start position in float tuple
        :param large: Unit is large and requires path to have width of 2 to pass
        :return: Tuple of points and total distance including influence.
        """

        if large:
            return self._map.find_path_influence_large(map_type, start, end, self.heuristic_accuracy)
        return self._map.find_path_influence(map_type, start, end, self.heuristic_accuracy)

    def safest_spot(
        self, map_type: MapType, destination_center: Tuple[float, float], walk_distance: float
    ) -> Tuple[Tuple[int, int], float]:
        return self._map.lowest_influence_walk(map_type, destination_center, walk_distance)

    def lowest_influence_in_grid(
        self, map_type: MapType, destination_center: Tuple[float, float], radius: int
    ) -> Tuple[Tuple[int, int], float]:
        return self._map.lowest_influence(map_type, destination_center, radius)

    def find_low_inside_walk(
        self, map_type: MapType, start: Tuple[float, float], target: Tuple[float, float], distance: Union[int, float]
    ) -> Tuple[Tuple[int, int], float]:
        """
        Finds a compromise where low influence matches with close position to the start position.

        This is intended for finding optimal position for unit with more range to find optimal position to fight from
        :param start: This is the starting position of the unit with more range
        :param target: Target that the optimal position should be optimized for
        :param distance: This should represent the firing distance of the unit with more range
        :return: Tuple for position and influence distance to reach the destination
        """
        # start_int = (round(start[0]), round(start[1]))
        # target_int = (round(target[0]), round(target[1]))
        return self._map.find_low_inside_walk(map_type, start, target, distance)

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
        image = np.multiply(image, 42)
        self.plot_image(image, image_name, resize)

    

    def plot_ground_map(self, path: List[Tuple[int, int]], image_name: str = "ground_map", resize: int = 4):
        image = np.array(self._map.ground_pathing, dtype=np.uint8)

        for point in path:
            image[point] = 255
        self.plot_image(image, image_name, resize)

    def plot_air_map(self, path: List[Tuple[int, int]], image_name: str = "air_map", resize: int = 4):
        image = np.array(self._map.air_pathing, dtype=np.uint8)

        for point in path:
            image[point] = 255
        self.plot_image(image, image_name, resize)
    
    def plot_reaper_map(self, path: List[Tuple[int, int]], image_name: str = "air_map", resize: int = 4):
        image = np.array(self._map.reaper_pathing, dtype=np.uint8)

        for point in path:
            image[point] = 255
        self.plot_image(image, image_name, resize)

    def plot_colossus_map(self, path: List[Tuple[int, int]], image_name: str = "air_map", resize: int = 4):
        image = np.array(self._map.colossus_pathing, dtype=np.uint8)

        for point in path:
            image[point] = 255
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
        # image = np.multiply(image, 42)
        self.plot_image(image, image_name, resize)

    def plot_zones(self, image_name: str = "map", resize: int = 4):
        image = np.array(self._map.draw_zones(), dtype=np.uint8)
        # image = np.multiply(image, 42)
        self.plot_image(image, image_name, resize)

    def plot_image(self, image, image_name: str = "map", resize: int = 4):
        import cv2
        image = np.rot90(image, 1)

        resized = cv2.resize(image, dsize=None, fx=resize, fy=resize, interpolation=cv2.INTER_NEAREST)
        cv2.imshow(image_name, resized)
        cv2.waitKey(1)
