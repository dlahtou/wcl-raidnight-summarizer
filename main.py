from raid_night_summarizer import RaidnightData, complete_report, get_best_ilvl_avg_improvement
import argparse
from os.path import realpath, dirname, join
from os import pardir

if __name__ == '__main__':
    basedir = dirname(realpath(__file__))
    print(basedir)

    parser = argparse.ArgumentParser(description='Generate reports for warcraftlogs raid data')
    parser.add_argument('code', type=str, 
                        help="the 16-character string identifier for a report")
    parser.add_argument('-dir', type=str,
                        help="the name of the directory containing raid json files")

    args = parser.parse_args()

    raid_folder = join(basedir, args.dir if args.dir else 'MyDudes')

    raidlist = [args.code]

    for raid_id in raidlist:
        raidnight = RaidnightData(raid_id, raid_folder)

        complete_report(raidnight, raid_folder, join(basedir, f'reports/{raidnight.name}.txt'), raid_id, improved=True)

        print(get_best_ilvl_avg_improvement(raidnight, raid_folder, 5))