class DPS_Parse(object):
    def __init__(self, player_name="None", overall_parse=0, ilvl_parse=0, boss_name="None", fight_duration=0):
        self.player_name = player_name
        self.overall_parse = overall_parse
        self.ilvl_parse = ilvl_parse
        self.boss_name = boss_name
        self.fight_duration = fight_duration
    
    def from_tuple(self, build_tuple):
        self.player_name, self.overall_parse, self.ilvl_parse, self.boss_name, self.fight_duration = list(build_tuple)
    
    def make_tuple(self):
        return self.__members()
    
    def __members(self):
        return (self.player_name, self.overall_parse, self.ilvl_parse, self.boss_name, self.fight_duration)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__members() == other.__members()
        else:
            return False

    def __hash__(self):
        return hash(self.__members())

    def __repr__(self):
        return repr(self.__members())