from raid_night_summarizer import RaidnightData, complete_report

if __name__ == '__main__':
    raidlist = ['Rz2DtHrZ4wKF7nXh']

    for raid_id in raidlist:
        raidnight = RaidnightData(raid_id, 'MyDudes')

        complete_report(raidnight, 'MyDudes', f'reports/{raidnight.name}.txt', raid_id, improved=True)