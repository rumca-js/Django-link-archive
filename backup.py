"""
"""
from workspace import get_workspaces
from linkarchivetools import Backup, parse_backup_commandline


def main():
    # TODO support for get_workspaces
    parser, args = parse_backup_commandline()
    b = Backup(args=args)
    b.process()


if __name__ == "__main__":
    main()
