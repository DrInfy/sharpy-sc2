import math
import numpy as np
from scipy.spatial.distance import cdist, euclidean
from math import pi
from typing import List

from sc2.position import Point2
from sc2.units import Units

pi2 = 2 * math.pi

OLD_TICKS: float = 16.0
NEW_TICKS: float = 22.4

def to_new_ticks(time_value: float) -> float:
    return time_value / OLD_TICKS * NEW_TICKS

def to_old_ticks(time_value: float) -> float:
    return time_value / NEW_TICKS * OLD_TICKS

def points_on_circumference(center: Point2, radius, n=10) -> List[Point2]:
    """Calculates all points on the circumference of a circle. n = number of points."""
    points = [
        (
            center.x + (math.cos(2 * pi / n * x) * radius),  # x
            center.y + (math.sin(2 * pi / n * x) * radius)  # y

        ) for x in range(0, n)]

    point2list = list(map(lambda t: Point2(t), points))
    return point2list


def points_on_circumference_sorted(center: Point2, closest_to: Point2, radius, n=10) -> List[Point2]:
    """Calculates all points on the circumference of a circle, and sorts the points so that first one
    on the list has shortest distance to closest_to parameter."""
    points = points_on_circumference(center, radius, n)

    closest_point = closest_to.closest(points)
    closest_point_index = points.index(closest_point)

    sorted_points = []

    # Points from closest point to the end
    sorted_points.extend(points[closest_point_index:])

    # Points from start of list to closest point (closest point not included)
    sorted_points.extend(points[0:closest_point_index])

    return sorted_points

def line_angle(from_point: Point2, to_point: Point2):
    return point_angle(to_point - from_point)

def point_angle(point: Point2) -> float:
    """
        (x,y) = (1,0) => -pi /2
        (x,y) = (0,-1) => 0
        (x,y) = (0,1) => pi
        (x,y) = (-1,0) =>  pi / 2
    """
    if point.y == 0:
        if point.x > 0:
            return math.pi * 0.5
        if point.x < 0:
            return math.pi * -0.5
        return 0

    angle = -math.atan(point.x / point.y)
    if point.y >= 0:
        angle += math.pi
    return angle

def point_from_angle(angle: float) -> Point2:
    return Point2((math.sin(angle), -math.cos(angle)))

def wrap_angle(angle:float) -> float:
    angle = angle % pi2

    if angle < -math.pi:
        angle += pi2
    elif angle > math.pi:
        angle -= pi2

    return angle

def angle_distance(angle1: float, angle2:float):
    angle1 = wrap_angle(angle1)
    angle2 = wrap_angle(angle2)
    d = abs(angle2 - angle1)
    if d <= math.pi:
        return d
    if angle1 < angle2:
        return abs(angle2 - (angle1 + pi2))
    return abs(angle2 + pi2 - angle1)

def point_normalize(point: Point2) -> Point2:
    if point.x == 0 and point.y == 0:
        return point
    l = math.sqrt(point.x ** 2 + point.y ** 2)

    return Point2((point.x / l, point.y / l))

def spiral(N, M):
    """Creates a spiral Point2 generator, use for example 3,3 or 5,5 to create 3x3 matrix or 5x5 matrix"""
    x,y = 0,0
    dx, dy = 0, -1

    for dumb in range(N*M):
        if abs(x) == abs(y) and [dx,dy] != [1,0] or x>0 and y == 1-x:
            dx, dy = -dy, dx            # corner, change direction

        if abs(x)>N/2 or abs(y)>M/2:    # non-square
            dx, dy = -dy, dx            # change direction
            x, y = -y+dx, x+dy          # jump

        yield Point2((x, y))
        x, y = x+dx, y+dy


def compute_euclidean_distance_matrix(locations):
    """Creates callback to return distance between points."""
    distances = {}
    for from_counter, from_node in enumerate(locations):
        distances[from_counter] = {}
        for to_counter, to_node in enumerate(locations):
            if from_counter == to_counter:
                distances[from_counter][to_counter] = 0
            else:
                # Euclidean distance
                distances[from_counter][to_counter] = (int(
                    math.hypot((from_node[0] - to_node[0]),
                               (from_node[1] - to_node[1]))))
    return distances


def unit_geometric_median(units: Units, accuracy=0.5) -> Point2:
    """ Calculates geometric median based on units, returns (0,0) if no units exist """
    if len(units) == 0:
        return Point2((0, 0))

    final_array = np.array([np.array([unit.position.x, unit.position.y]) for unit in units])

    result = geometric_median(final_array, accuracy)
    return Point2(result)


def geometric_median(X, eps=1e-5):
    """
    Calculates geometric median based on points
    :param X: 2D numpy array / matrix
    :param eps: epsilon for accuracy
    :return: numpy array with 2 floats
    """
    y = np.mean(X, 0)

    for i in range(30): # Just to make sure that no endless loops happen
        D = cdist(X, [y])
        nonzeros = (D != 0)[:, 0]

        Dinv = 1 / D[nonzeros]
        Dinvs = np.sum(Dinv)
        W = Dinv / Dinvs
        T = np.sum(W * X[nonzeros], 0)

        num_zeros = len(X) - np.sum(nonzeros)
        if num_zeros == 0:
            y1 = T
        elif num_zeros == len(X):
            return y
        else:
            R = (T - y) * Dinvs
            r = np.linalg.norm(R)
            rinv = 0 if r == 0 else num_zeros/r
            y1 = max(0, 1-rinv)*T + min(1, rinv)*y

        if euclidean(y, y1) < eps:
            return y1

        y = y1
    return y


def two_opt(cities,improvement_threshold):
    """2-opt Algorithm adapted from https://en.wikipedia.org/wiki/2-opt"""

    # Calculate the euclidian distance in n-space of the route r traversing cities c, ending at the path start.
    path_distance = lambda r,c: np.sum([np.linalg.norm(c[r[p]]-c[r[p-1]]) for p in range(len(r))])
    # Reverse the order of all elements from element i to element k in array r.
    two_opt_swap = lambda r,i,k: np.concatenate((r[0:i],r[k:-len(r)+i-1:-1],r[k+1:len(r)]))

    route = np.arange(cities.shape[0]) # Make an array of row numbers corresponding to cities.
    improvement_factor = 1 # Initialize the improvement factor.
    best_distance = path_distance(route,cities) # Calculate the distance of the initial path.
    while improvement_factor > improvement_threshold: # If the route is still improving, keep going!
        distance_to_beat = best_distance # Record the distance at the beginning of the loop.
        for swap_first in range(1,len(route)-1): # From each city except the first and last,
            for swap_last in range(swap_first+1,len(route)): # to each of the cities following,
                new_route = two_opt_swap(route,swap_first,swap_last) # try reversing the order of these cities
                new_distance = path_distance(new_route,cities) # and check the total distance with this modification.
                if new_distance < best_distance: # If the path distance is an improvement,
                    route = new_route # make this the accepted best route
                    best_distance = new_distance # and update the distance corresponding to this route.
        improvement_factor = 1 - best_distance/distance_to_beat # Calculate how much the route has improved.

    return route # When the route is no longer improving substantially, stop searching and return the route.
