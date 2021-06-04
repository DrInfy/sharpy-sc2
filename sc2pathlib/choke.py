from typing import Tuple, List

class Choke:
    main_line: Tuple[Tuple[float, float], Tuple[float, float]]
    lines: List[Tuple[Tuple[int, int], Tuple[int, int]]]
    side1: List[Tuple[int, int]]
    side2: List[Tuple[int, int]]
    pixels: List[Tuple[int, int]]
    min_length: float