from raid_night_summarizer import RaidnightData
from collections import defaultdict
import pandas as pd
import numpy as np

ignore_specs = {'Monk-Mistweaver',
                'Paladin-Holy',
                'Druid-Restoration',
                'Priest-Discipline',
                'Priest-Holy',
                'Shaman-Restoration',
                'Warrior-Protection',
                'Paladin-Protection',
                'Monk-Brewmaster',
                'DeathKnight-Blood',
                'Druid-Guardian'}

def rank_dps(raidnights):
    '''
    Returns an ordered list of dps player names, from highest average dps rank across all bosses to lowest

    Parameters:
    raidnights: a list of RaidnightData objects, representing the raids within a single lockout to be analyzed
    '''

    if not isinstance(raidnights, list):
        raidnights = [raidnights]

    # construct a dictionary with k:v :: player:list_of_ranks  e.g. Bradney:[1,1,2,4,2]
    player_ranks = defaultdict(list)
    for raidnight in raidnights:
        for fight in raidnight.damage_done.keys():
            if fight[:6] != 'Heroic':
                continue
            # instantiate dict for fight
            fight_damage_values = dict()

            # store player:damage in fight dict
            fight_entries = raidnight.damage_done[fight]['entries']
            for player in fight_entries:
                if player['icon'] in ignore_specs:
                    continue
                player_name = player['name']
                player_damage = player['total']
                fight_damage_values[player_name] = player_damage
            
            # rank player damage values and store rank in player_ranks
            ## note that this does not handle cases where players have exactly the same total damage, though this is unlikely
            for rank, player in enumerate(sorted(fight_damage_values, key=fight_damage_values.get, reverse=True), start=1):
                player_ranks[player].append(rank)

    ranked_dps = sorted(player_ranks, key=lambda x: np.mean(player_ranks[x]))

    return ranked_dps

def get_topn_dps_overall(raidnights, n=3):
    return rank_dps(raidnights)[:n]

def all_ilvl_parses_df(raidnights):
    '''
    Looks through the given raidnights, and returns a dataframe containing all dps players and their ilvl parses for each boss

    Parameters:
        raidnights (list of RaidnightData objects)

    
    Returns:
        pandas dataframe, rows are players, columns are bosses, entries are ilvl parses
    '''

    # best way to construct? assign all bosses in all raidnights to column of dataframe?
    # each row contains a unique player and lockout number?

    # setup dataframe by finding all unique players&bosses in all raidnights
    bosses = []
    players = set()
    lockouts = set()

    for raidnight in raidnights:
        lockouts.add(raidnight.get_raid_lockout_period())

        for fight_name in raidnight.parse_scrapes.keys():
            if fight_name not in bosses:
                bosses.append(fight_name)

            for player in raidnight.parse_scrapes[fight_name]:
                players.add(player)

    names_lockouts = pd.MultiIndex.from_product([players, lockouts], names=['Player', 'Lockout'])

    df = pd.DataFrame(np.nan, index=names_lockouts,columns=bosses)

    for raidnight in raidnights:
        lockout = raidnight.get_raid_lockout_period()

        for fight_name in raidnight.parse_scrapes.keys():
            fight_dict = raidnight.parse_scrapes[fight_name]
            for player in fight_dict.keys():
                df.loc[(player, lockout), fight_name] = fight_dict[player]['ilvl-performance']

    return df

def qualified_parses(parse_df):
    best_parses = parse_df.groupby(level='Player').max()

    qualified_parses = best_parses[best_parses.median(axis=1) >= 25]

    return qualified_parses

def unqualified_parses(parse_df):
    best_parses = parse_df.groupby(level='Player').max()

    qualified_parses = best_parses[best_parses.median(axis=1) < 25]

    return qualified_parses

# make a list of dictionaries for every parse

if __name__ == '__main__':
    raid_strings = ['CNMdqH1fDjGZAp8V', 'mJdfV7QjkC8avTWM']
    raidnights = [RaidnightData(x, 'MyDudes') for x in raid_strings]
    
    n = 5
    for raidnight in raidnights:
        print(f'Top {n} for raidnight {raidnight.wcl_string}:')
        print(get_topn_dps_overall(raidnight, n))

    parse_df = all_ilvl_parses_df(raidnights)

    #print(get_qualified_parses(parse_df))

    print(unqualified_parses(parse_df))