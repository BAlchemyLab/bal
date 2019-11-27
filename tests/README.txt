How to use:

  tests directory should be run as a package via python -m tests command.
  In order to execute scripts, they should be appended to given command with a dot.
  Example: python -m tests.test
  This would run test.py script.

  Why:

    This procedure allows python to import bal scripts, otherwise tests directory had
    to be an upper directory of bal directory.
