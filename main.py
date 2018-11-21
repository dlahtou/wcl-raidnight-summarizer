from raid_night_summarizer import RaidnightData, complete_report, get_best_ilvl_avg_improvement

if __name__ == '__main__':
    raidlist = ['2cHFAgv6GPyZ1Tfj']

    for raid_id in raidlist:
        raidnight = RaidnightData(raid_id, 'MyDudes')

        complete_report(raidnight, 'MyDudes', f'reports/{raidnight.name}.txt', raid_id, improved=True)

        print(get_best_ilvl_avg_improvement(raidnight, 'MyDudes', 5))