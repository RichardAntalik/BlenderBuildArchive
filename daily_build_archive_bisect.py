import os
import sys
import datetime
import subprocess

storage_path = 'storage/'
build_info_stamp_filename = 'archive_build_info.txt'

dirs = sorted(os.listdir(storage_path))

print('Bisect daily builds')
print('Usage:')
print('  good <date>\t Use date of last checked build if none is given')
print('  bad <date>\t Use date of last checked build if none is given')
print('  date is in YYYY-MM-DD format')
print('-----------------------------------------------------------------')
print(len(dirs), 'builds in archive.')
print()
print()

good = None
bad = None
bad_index = None
good_index = None
is_done = False
current_index = len(dirs) - 1
current = dirs[current_index]

# Only print once.
print('Oldest build:', dirs[0])
print('Latest build:', current)

while not is_done:

    command_list = input().split(' ')
    command = command_list[0]
    if len(command_list) > 1:
        arg = command_list[1]
    else:
        arg = None

    if command == 'end' or command == 'e':
        sys.exit()

    if command == 'good' or command == 'g':
        if arg:
            if arg in dirs:
                good_index = dirs.index(arg)
            else:
                print('date', arg, 'not found')
                good_index = None
        else:
            good_index = current_index
        if good_index is not None:
            if bad_index and bad_index <= good_index:
                print("Nothing to bisect - Bad date can not be earlier than good date")
                good = None
            else:
                good = dirs[good_index]
                print(good, 'is good')

    if command == 'bad'  or command == 'b':
        if arg:
            if arg in dirs:
                bad_index = dirs.index(arg)
            else:
                print('date', arg, 'not found')
                bad_index = None
        else:
            bad_index = current_index
        if bad_index is not None:
            if good_index and bad_index <= good_index:
                print("Nothing to bisect - Bad date can not be earlier than good date")
                bad = None
            else:
                bad = dirs[bad_index]
                print(bad, 'is bad')

    # We are set up for actual bisecting.
    if good and bad:
        num_todo = bad_index - good_index
        current_index = good_index + round((num_todo - 0.5) / 2)
        current = dirs[current_index]
        print('Bisecting', num_todo, 'builds.', 'Current build is', current)

        if bad_index - good_index <= 1:
            is_done = True
            print('Bisecting done. bad commit is between', good, bad)
            sys.exit
            
        blender_executable = os.path.join(storage_path, current, "blender.exe")
        subprocess.call(blender_executable)
