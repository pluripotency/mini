import json
import sys
import re
from termios import tcflush, TCIFLUSH
import toml
from .ansi_colors import red, green, brown, blue, purple, cyan, white, light_red, light_green, yellow, light_blue, pink, light_cyan
from . import misc

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
    exp = misc.ipv4_exp_str
    if with_prefix:
        message += '/prefix'
        exp = misc.ipv4_with_prefix_exp_str
    if default_value:
        message += f'(default:{default_value})'
    return get_input(exp, message + ': ', default_value=default_value)

def get_y_n(message, default=False, color=yellow):
    y_n = ' [Y/n]?: ' if default else ' [y/N]?: '
    if callable(color):
        msg = color(message + y_n)
    else:
        msg = message + y_n
    user_input = get_input('y|n|Y|N|', msg, 'input y or n')
    if re.match('y|Y', user_input):
        return True
    elif re.match('n|N', user_input):
        return False
    else:
        return default

def getlist(li, color=cyan):
    item_list = []
    for i, l in enumerate(li):
        index = i+1
        if index < 10:
            head = ' '+str(index)+', '
        else:
            head = str(index)+', '
        pad = 10 - len(l)
        l += ' ' * pad
        item_list += [head + color(l)]
        if index % 5 == 0:
            print(' '.join(item_list))
            item_list = []
    print(' '.join(item_list))

def getvlist(li, color=cyan):
    for i, l in enumerate(li):
        print(str(i + 1) + ', ' + color(l))

def choose_num(menu_list, message=green('Please select number.'), vertical=True, append_exit=False, append_back=False, color=cyan):
    while True:
        print(message)
        if append_exit and append_back:
            print(yellow('0 or q to exit, b to back'))
        elif append_exit:
            print(yellow('0 or q to exit'))
        elif append_back:
            print(yellow('b to back'))
        if vertical:
            getvlist(menu_list, color)
        else:
            getlist(menu_list, color)
        tcflush(sys.stdin, TCIFLUSH)
        num = input('>> ')
        if append_exit and num in ('q', '0'):
            print('Exit selected.')
            sys.exit(0)
        elif append_back and num in ('b'):
            print('Back selected.')
            return None # False is evaluated as 0
        elif re.match(r'\d+', num):
            index = int(num) - 1
            if 0 <= index < len(menu_list):
                print(white('Selected : ') + cyan(menu_list[index]))
                return index
            print(red('Please input existing number!!'))
            continue
        print(red('Please input number!'))

def select_2nd(entries, message=green('Please select number.'), vertical=True, append_exit=True, append_back=False, color=cyan):
    menu_list = list(map(lambda n: n[0], entries))
    index = choose_num(menu_list, message=message, vertical=vertical, append_exit=append_exit, append_back=append_back, color=color)
    if isinstance(index, int):
        if callable(entries[index][1]):
            return entries[index][1]()
        return entries[index][1]
    return False

USER_DEF_TOML_STR = r'''
[username]
type = 'string'
[password]
type = 'string'
expr = '\w+'
[sudoers]
type = 'bool'
[sudoers.skip_on]
username = [
    'root'
]
'''
USER_DEFAULT_TOML_STR = '''
username = 'worker'
password = 'password'
sudors = true
'''

def get_obj_by_definition(input_definition, default_values, by_toml=False, color=cyan):
    """
    ex) input_definition: ex_user_definition
    ex) default_values: ex_default_user
    """
    if by_toml:
        input_definiion = toml.loads(input_definiion)
        default_values = toml.loads(default_values)
    obj = {}
    for k, v in input_definition.items():
        if 'type' in v:
            v_type = v['type']
            if 'skip_on' in v:
                skip = False
                for sk, sv in v['skip_on'].items():
                    if obj[sk] in sv:
                        skip = True
                if skip:
                    continue
            message = k
            if 'message' in v:
                message = v['message']
            if v_type == 'string':
                exp = r'\w.'
                if 'exp' in v:
                    exp = v['exp']
                if k in default_values:
                    default_value = default_values[k]
                    obj[k] = get_input(exp, f'{message}(default={default_value}):', default_value=default_value)
                else:
                    obj[k] = get_input(exp, f'{message}:')
            elif v_type == 'int':
                exp = r'\d+'
                if 'exp' in v:
                    exp = v['exp']
                if k in default_values:
                    default_value = default_values[k]
                    value_str = get_input(exp, f'{message}(default={default_value}):', default_value=default_value)
                else:
                    value_str = get_input(exp, f'{message}:')
                obj[k] = int(value_str)
            elif v_type == 'bool':
                if k in default_values:
                    default_value = default_values[k]
                    obj[k] = get_y_n(f'{message}(default={default_value}):', default=default_value)
                else:
                    obj[k] = get_y_n(f'{message}:')
    print(color(toml.dumps(obj)))
    if get_y_n('OK?'):
        return obj
    else:
        return None

class Selection:
    def __init__(self, menu_type, output_dir='/tmp/plur_history'):
        if not menu_type:
            self.error('menu_type is needed')
        self.menu_type= misc.sanitize_to_file_name(menu_type)
        self.title = None
        self.selected_list = []

        prepare_result = misc.prepare_dir_if_not_exists(output_dir)
        if not prepare_result:
            self.error(f'couldn\'t prepare dir: {output_dir}')
        self.output_dir = output_dir

    def error(self, err):
        print('error in menu.Selection', err)
        exit(1)

    def append(self, value):
        self.selected_list.append(value)

    def set_title(self, title):
        self.title = misc.sanitize_to_file_name(title)
        print('set selection: menu_type:' + self.menu_type + ' title:' + self.title)

    def input_title(self):
        self.set_title(get_input(message='Selection Name: '))

    def create_file_name(self):
        return self.menu_type + '_' + self.title + '.sel'

    def create_file_path(self):
        return self.output_dir + '/' + self.create_file_name()

    def save(self):
        if not self.title:
            self.input_title()
        misc.open_write(self.create_file_path(), json.dumps(self.selected_list, indent=2), 'w')

    def load(self, title):
        self.set_title(title)
        loaded_json = misc.read_json(self.create_file_path())
        if loaded_json:
            self.selected_list = loaded_json
        else:
            self.error(f'couldn\'t load: {self.create_file_path()}')
