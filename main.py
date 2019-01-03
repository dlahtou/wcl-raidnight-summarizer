from raid_night_summarizer import RaidnightData, complete_report, get_best_ilvl_avg_improvement
import argparse
from os.path import realpath, dirname, join, isdir
from os import pardir, mkdir

if __name__ == '__main__':
    # Setup filepaths
    basedir = dirname(realpath(__file__))
    if not isdir(join(basedir, 'reports')):
        mkdir(join(basedir, 'reports'))
    raid_folder = join(basedir, args.dir if args.dir else 'MyDudes')

    # Input arguments
    parser = argparse.ArgumentParser(description='Generate reports for warcraftlogs raid data')
    parser.add_argument('code', type=str, 
                        help="the 16-character string identifier for a report")
    parser.add_argument('-dir', type=str,
                        help="the name of the directory containing raid json files")

    args = parser.parse_args()

    # Create list of raid codes to lookup on warcraftlogs
    raidlist = [args.code]

    # Generate output file for each raid code
    for raid_id in raidlist:
        raidnight = RaidnightData(raid_id, raid_folder)
        out_path = join(basedir, f'reports/{raidnight.name}.txt')

        complete_report(raidnight, raid_folder, out_path, raid_id, improved=True)

        # optional logging of most-improved raiders
        print(get_best_ilvl_avg_improvement(raidnight, raid_folder, 5))