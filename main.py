from raid_night_summarizer import *

if __name__ == '__main__':
    raidlist = ['Rz2DtHrZ4wKF7nXh']

    for raid_id in raidlist:
        raidnight = RaidnightData(raid_id, 'MyDudes')
        print(raidnight.raid_name)

        print(get_best_raid_overall_parse(raidnight,3))
        print(get_best_raid_ilvl_parse(raidnight,3))
        print(get_best_ilvl_parse(raidnight,3))

        print(raidnight.get_name())


        complete_report(raidnight, 'MyDudes', f'reports/{raidnight.name}.txt', raid_id, improved=True)