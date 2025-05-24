import sys
from termios import tcflush, TCIFLUSH
from mini.ansi_colors import re, red, cyan, white, green, yellow
from mini import misc

def get_input(expression=r'\w+', message='Please input: ', err_message='invalid value.', default_value=None):
    while True:
        tcflush(sys.stdin, TCIFLUSH)
        user_input = input(message)
        if user_input == '' and default_value is not None:
            return default_value
        if re.match(expression, user_input):
            return user_input
        print(red(err_message))

def get_ipv4(default_value=None, with_prefix=False):
    message = 'Please input ipv4'
    exp = misc.IPV4_EXP_STR
    if with_prefix:
        message += '/prefix'
        exp = misc.IPV4_WITH_PREFIX_EXP_STR
    if default_value:
        message += f'(default:{default_value})'
    return get_input(exp, message + ': ', default_value=default_value)

def get_y_n(message, default=False):
    y_n = '[y/N]?: '
    if default:
        y_n = '[Y/n]?: '
    user_input = get_input('y|n|Y|N|', message + y_n, 'input y or n')
    if re.match('y|Y', user_input):
        return True
    if re.match('n|N', user_input):
        return False
    return default

def getlist(li):
    menu = []
    for i, l in enumerate(li):
        index = i+1
        if index < 10:
            head = ' '+str(index)+', '
        else:
            head = str(index)+', '
        pad = 10 - len(l)
        l += ' ' * pad
        menu += [head + cyan(l)]
        if index % 5 == 0:
            print(' '.join(menu))
            menu = []
    print(' '.join(menu))

def getvlist(li, color=cyan):
    for i, l in enumerate(li):
        print(str(i + 1) + ', ' + color(l))

def choose_num(menu_list, message=green('Please select number.'), vertical=True, append_exit=False, color=cyan):
    while True:
        print(message)
        if append_exit:
            print(yellow('0 or q to exit'))
        if vertical:
            getvlist(menu_list, color)
        else:
            getlist(menu_list)
        tcflush(sys.stdin, TCIFLUSH)
        num = input('>> ')
        if append_exit and num in ('q', '0'):
            print('Exit selected.')
            sys.exit(0)
        elif re.match(r'\d+', num):
            index = int(num) - 1
            if len(menu_list) > index >= 0:
                print(white('Selected : ') + cyan(menu_list[index]))
                return index
            print(red('Please input existing number!!'))
        print(red('Please input number!'))

def select_2nd(entries, menu_mesg=green('Please select number.'), vertical=True, append_exit=True):
    menu_list = list(map(lambda n: n[0], entries))
    index = choose_num(menu_list, menu_mesg, vertical, append_exit)
    if callable(entries[index][1]):
        return entries[index][1]()
    return entries[index][1]
