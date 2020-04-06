from sharpy.knowledges import Knowledge


class GatherPoint:
    def __init__(self, knowledge: Knowledge):
        self.zone_index = 0
        self.starting_from = 0
        self.ending_to = 0
        self.percentage = 0
