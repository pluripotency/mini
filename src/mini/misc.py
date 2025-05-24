import os
import sys
import stat
import re
import shutil
import json
import datetime
import pprint
import toml
from mini import ansi_colors
pp = pprint.PrettyPrinter()

def print_flush(msg):
    print(msg, flush=True)

def prettyprint(data):
    pp.pprint(data)

def sanitize_to_file_name(command):
    return re.sub(r'\s|\.', '_', re.sub('/|:|', '', command))

def is_file(file_path):
    return os.path.isfile(file_path)

def now():
    return datetime.datetime.now()

def now_debug():
    return now().strftime('%X.%f')

def stdout(msg, cr=True, escape_ansi=False):
    if escape_ansi:
        msg = ansi_colors.rm_color(msg)
    if cr:
        print(msg)
    else:
        sys.stdout.write(msg)

def to_ymd_str(separator='/'):
    return '%Y' + separator + '%m' + separator + '%d'

def to_hms_str(separator=':', additional=''):
    return '%H' + separator + '%M' + separator + '%S' + additional

def to_ymd_hms_str(ymd_sep='/', hms_sep=':', ymd_hms_sep=' '):
    return to_ymd_str(ymd_sep) + ymd_hms_sep + to_hms_str(hms_sep)

def format_time(dt, format_str):
    return dt.strftime(format_str)

def get_ymd(dt):
    return format_time(dt, to_ymd_str(''))

def get_hms_f(dt):
    return format_time(dt, to_hms_str('', '_%f'))

def create_timestamp_str():
    return now().strftime('%Y%m%d_%H%M%S')

def del_indent_lines(string):
    sp = string.split('\n')
    last_line = sp[len(sp)-1]
    indent_group= re.search(r'^(\s+)', last_line)
    indent = len(indent_group[0])
    return [line[indent:] for line in sp[1:len(sp)-1]]

def del_indent(string):
    return '\n'.join(del_indent_lines(string))

def try_io_func(func, f_name):
    try:
        return func()
    except OSError as e:
        print_flush(ansi_colors.red(f'OSError in {f_name}: {e}'))
        return False
    except Exception as e:
        print_flush(ansi_colors.red(f'Exception in {f_name}: {e}'))
        return False

class FakeWriter:
    def __init__(self):
        pass
    def write(self, message):
        pass
    def flush(self):
        pass
    def close(self):
        pass

class ForkWriter:
    def __init__(self, file_path=None, write_mode='a'):
        self.file_path = file_path
        if file_path:
            create_dir_if_not_exist(file_path)
            self.file = open(os.path.expanduser(file_path), write_mode)
        else:
            self.file = FakeWriter()

    def write(self, s):
        self.file.write(s)

    def flush(self):
        self.file.flush()

    def close(self):
        self.file.flush()
        self.file.close()

def create_dir_if_not_exist(file_path):
    os.makedirs(os.path.dirname(os.path.expanduser(file_path)), exist_ok=True)

def delete_file_path(file_path):
    def func():
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    return try_io_func(func, f'delete_file_path: path {file_path}')

def delete_all_in_dir(dir_path):
    def func():
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            delete_file_path(file_path)
    return try_io_func(func, f'delete_all_in_dir: path {dir_path}')

def prepare_dir(dir_path, clear=False):
    def func():
        if dir_path == '/':
            print_flush(ansi_colors.red('err in prepare_dir: prepare / is not allowed.'))
            sys.exit(1)
        else:
            if os.path.isdir(dir_path):
                if clear:
                    delete_all_in_dir(dir_path)
                else:
                    return
            else:
                os.makedirs(dir_path)
    return try_io_func(func, f'prepare_dir: path {dir_path}')

def prepare_clean_dir(dir_path):
    prepare_dir(dir_path, clear=True)

def open_read(file_path):
    def func():
        with open(file_path, 'r') as f:
            return f.read()
    return try_io_func(func, f'open_read: path: {file_path}')

def open_write(file_path, contents, write_mode='w'):
    def func():
        with open(file_path, write_mode) as f:
            f.write(contents)
        return True
    return try_io_func(func, f'open_write: path: {file_path}')

def read_toml(file_path):
    def func():
        with open(file_path, 'r') as f:
            translated = toml.load(f)
        return translated
    return try_io_func(func, f'read_toml: path: {file_path}')

def read_json(file_path):
    def func():
        data = open_read(file_path)
        return json.loads(data)
    return try_io_func(func, f'read_json: path: {file_path}')

def write_json(file_path, json_contents, indent=2):
    def func():
        return open_write(file_path, json.dumps(json_contents, indent=indent))
    return try_io_func(func, f'write_json: path: {file_path}')

def read_lines(file_path):
    def func():
        data = open_read(file_path)
        return re.split('\n', data)
    return try_io_func(func, f'read_lines: path: {file_path}')

def get_only_file_list(dir_path):
    def func():
        extracted_dir_path = os.path.expanduser(dir_path)
        only_file_list = [f for f in os.listdir(extracted_dir_path) if os.path.isfile(os.path.join(extracted_dir_path, f))]
        return only_file_list
    return try_io_func(func, f'get_only_file_list: dir_path: {dir_path}')

def create_log_params(each_task_name, log_base_params, append=False):
    log_parent_dir = log_base_params['log_parent_dir']
    task_name      = log_base_params['task_name']
    enable_output  = log_base_params['enable_output']
    each_task_log_dir = f'{log_parent_dir}/logs_{task_name}/{each_task_name}'
    if append:
        return {
            'log_dir': each_task_log_dir
            , 'enable_stdout': enable_output
            , 'output_log_append_path': f'{each_task_log_dir}/output.log'
            , 'dont_truncate': False
            , 'debug_color': True
            , 'debug_log_append_path': f'{each_task_log_dir}/debug.log'
        }
    return {
        'log_dir': each_task_log_dir
        , 'enable_stdout': enable_output
        , 'output_log_file_path': f'{each_task_log_dir}/output.log'
        , 'dont_truncate': False
        , 'debug_color': True
        , 'debug_log_file_path': f'{each_task_log_dir}/debug.log'
    }

def is_locked(lock_dir_path, fname_header, delta_second=300):
    if not os.path.exists(lock_dir_path):
        return False
    allow_delta = datetime.timedelta(seconds=delta_second)
    file_list = os.listdir(lock_dir_path)
    flag = False
    for fname in file_list:
        if fname.startswith(fname_header):
            dt_str = fname[len(fname_header)+1:]
            sp = dt_str.split('_')
            if re.match(r'\d{8}', sp[0]) and re.match(r'\d{6}', sp[1]):
                year = int(sp[0][:4])
                month = int(sp[0][4:6])
                day = int(sp[0][6:])
                hour = int(sp[1][:2])
                minute = int(sp[1][2:4])
                second = int(sp[1][4:])
                # timestamp = f'{year}/{month}/{day} {hour}:{minute}:{second}'
                parsed_dt = datetime.datetime(year, month, day, hour, minute, second)
                if datetime.datetime.now() - parsed_dt < allow_delta:
                    print_flush(ansi_colors.red(f'operation is locked: {fname_header}'))
                    flag = True
                else:
                    # delete expired lockfile
                    deleting_file_path = f'{lock_dir_path}/{fname}'
                    os.remove(deleting_file_path)
    return flag

def create_lock(lock_dir_path, fname_header, timestamp=None):
    """
    fname ex) test_20200101_120030
    """
    os.makedirs(lock_dir_path, exist_ok=True)
    if not timestamp:
        timestamp = datetime.datetime.now()
    lock_file_path = f'{lock_dir_path}/{fname_header}_' + timestamp.strftime("%Y%m%d_%H%M%S")
    with open(lock_file_path, 'w') as f:
        f.write('lock')

def test_lock():
    locktest_dir = '/tmp/locktest'
    fname_header = 'locktest'
    now = datetime.datetime.now()
    ago_6min = now-datetime.timedelta(seconds=360)
    ago_4min = now-datetime.timedelta(seconds=240)
    [create_lock(locktest_dir, fname_header, timestamp=ts) for ts in [
        # None,
        ago_4min,
        ago_6min,
    ]]

    print_flush(is_locked(locktest_dir, fname_header))

mask_list = [
    '0',  # 0
    '128',  # 1
    '192',  # 2
    '224',  # 3
    '240',  # 4
    '248',  # 5
    '252',  # 6
    '254',  # 7
    '255',  # 8
]
IPV4_EXP_STR = r'((1[0-9][0-9]|[1-9]?[0-9]|2[0-4][0-9]|25[0-5])\.){3}(1[0-9][0-9]|[1-9]?[0-9]|2[0-4][0-9]|25[0-5])'
SEG_EXP = '(255|254|252|248|240|224|192|128|0)'
EXP_255_255_255_X = r'((255\.){3}' + SEG_EXP + r')'
EXP_255_255_X_0 = r'((255\.){2}' + SEG_EXP + r'\.0)'
EXP_255_X_0_0 = r'((255\.)' + SEG_EXP + r'(\.0+){2})'
EXP_X_0_0_0 = r'(' + SEG_EXP + r'(\.0+){3})'
NETMASK_EXP_STR = '(' + EXP_255_255_255_X + '|' + EXP_255_255_X_0 + '|' + EXP_255_X_0_0 + '|' + EXP_X_0_0_0 + ')'
IPV4_WITH_PREFIX_EXP_STR = IPV4_EXP_STR + '/(1[0-9]|2[0-9]|3[0-2]|[0-9])'
IPV4_ROUTE_EXP_STR = IPV4_WITH_PREFIX_EXP_STR + ' via ' + IPV4_EXP_STR

def is_ipv4(may_ipv4_str):
    return re.search('^' + IPV4_EXP_STR + '$', may_ipv4_str)

def is_ipv4_with_prefix(may_ipv4_with_prefix_str):
    return re.search('^' + IPV4_WITH_PREFIX_EXP_STR + '$', may_ipv4_with_prefix_str)

def is_ipv4_route(may_ipv4_route_str):
    return re.search('^' + IPV4_ROUTE_EXP_STR + '$', may_ipv4_route_str)

def is_ipv4_route_list(may_ipv4_route_list_str):
    return re.search('^' + IPV4_ROUTE_EXP_STR + r'(\n' + IPV4_ROUTE_EXP_STR + r')*\n?$', may_ipv4_route_list_str)

def is_ip_in_network(network, ip):
    """
    >>> is_ip_in_network('192.168.5.0/24', '192.168.100.1')
    False
    >>> is_ip_in_network('192.168.128.0/22', '192.168.131.1')
    True
    >>> is_ip_in_network('192.168.128.0/22', '192.168.132.1')
    False

    """
    sp = network.split('/')
    net_ip = sp[0]
    prefix_num = int(sp[1])
    quo, rem = prefix_num // 8, prefix_num % 8
    if quo > 0:
        start_octs = '.'.join(net_ip.split('.')[:quo]) + '.'
        if not ip.startswith(start_octs):
            return False
    if rem == 0:
        return True
    net_oct = int(net_ip.split('.')[quo])
    ip_oct = int(ip.split('.')[quo])
    net_oct_end = net_oct + 2 ** (8 - rem) - 1
    if net_oct <= ip_oct <= net_oct_end:
        return True
    return False

def prefix_to_netmask(prefix):
    """
    >>> prefix_to_netmask('16')
    '255.255.0.0'
    >>> prefix_to_netmask('20')
    '255.255.240.0'
    >>> prefix_to_netmask('1')
    '128.0.0.0'
    >>> prefix_to_netmask('0')
    '0.0.0.0'
    >>> prefix_to_netmask('32')
    '255.255.255.255'
    """
    if re.match(r'\d{1,2}', prefix):
        int_prefix = int(prefix)
        if 0 <= int_prefix <= 32:
            sho = int_prefix // 8
            mod = int_prefix % 8
            subnet_mask = ''
            for i in range(sho):
                subnet_mask += '.255'
            for j, k in enumerate(range(4-sho)):
                if j == 0:
                    subnet_mask += f'.{mask_list[mod]}'
                else:
                    subnet_mask += '.0'
            return subnet_mask[1:]
    print_flush(f'err invalid prefix: {prefix}')
    sys.exit(1)

def netmask_to_prefix(netmask):
    """
    >>> netmask_to_prefix('255.255.255.248')
    '29'
    >>> netmask_to_prefix('255.255.192.0')
    '18'
    >>> netmask_to_prefix('')
    False
    >>> netmask_to_prefix('2.255.192.0')
    False
    """
    if re.match('^' + NETMASK_EXP_STR + '$', netmask):
        adder = 0
        for seg in  netmask.split('.'):
            found_index = find_index_of_value(mask_list, seg)
            if found_index == -1:
                return False
            adder += found_index
        return str(adder)
    return False

def find(item_list, func):
    """
    >>> find(['melon', 'apple', 'mapple'], lambda item: re.search('apple', item))
    'apple'
    >>> find(['melon', 'apple', 'mapple'], lambda item: re.search('ringo', item))
    False
    """
    for item in item_list:
        if func(item):
            return item
    return False

def find_index(item_list, func):
    """
    >>> find_index(['apple', 'linux', 'windows'], lambda item: item == 'linux')
    1
    """
    for index, item in enumerate(item_list):
        if func(item):
            return index
    return -1

def find_index_of_value(value_list, value):
    """
    >>> find_index_of_value(['apple', 'linux', 'windows'], 'linux')
    1
    """
    return find_index(value_list, lambda item: item == value)

def filter(item_list, func):
    """
    >>> filter(['apple', 'linux', 'windows'], lambda item: item != 'linux')
    ['apple', 'windows']
    """
    filtered = []
    for item in item_list:
        if func(item):
            filtered.append(item)
    return filtered

def map(item_list, func):
    new_list_obj = []
    for item in item_list:
        new_list_obj.append(func(item))
    return new_list_obj

def concat_dict(args):
    """
    >>> a = {'a': 'this is a'}
    >>> b = {'b': 'this is b'}
    >>> c = {'c': 'this is c'}
    >>> concat_dict([a, b, c])
    {'a': 'this is a', 'b': 'this is b', 'c': 'this is c'}
    """
    x = args[0]
    if len(args) == 1:
        return x
    return dict(x, **concat_dict(args[1:]))

def write_file_list(file_list):
    for item in file_list:
        filepath = item[0]
        contents = item[1]
        open_write(filepath, contents)
        if re.search(r'.+\.sh$', filepath):
            st = os.stat(filepath)
            os.chmod(filepath, st.st_mode | stat.S_IEXEC)
