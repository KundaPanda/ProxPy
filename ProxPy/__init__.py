from threading import current_thread, active_count
from time import sleep
from toolz import unique
import tkinter as tk
from tkinter import filedialog
from enum import Enum
from requests import request
from requests.exceptions import RequestException, ProxyError, Timeout
from concurrent.futures import as_completed, ThreadPoolExecutor as ThreadPool
import re
from bs4 import BeautifulSoup

# TODO: COMMENTS

name = "ProxPy"

_root = tk.Tk()
_root.withdraw()
_resetting = False
_checked = []
_host_ip = ""

proxy_stats = {
    "suc": 0,
    "fail": 0,
    "alive": 0,
    "dead": 0
}


class ProxyType(Enum):
    """
    enum specifying type of proxies being used
    """

    socks5h = 0
    socks5 = 1
    https = 2
    http = 3


class Judge(Enum):
    """
    Proxy judge enum
    """

    def __new__(cls, *args, **kwargs):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, url, number):
        self.url = url
        self.number = number

    azenv = "https://azenv.net", 0
    proxyjudge = "http://proxyjudge.info", 1


class Options:
    """
    options holder, you can set all the possible things here
    """

    def __init__(self, username="", password="", judge=Judge.azenv, proxy_check_threads=50,
                 check_timeout=4,
                 debug=False,
                 show_progress=True,
                 workers_per_proxy=5):
        self.judge = judge
        self.proxy_check_threads = proxy_check_threads
        self.check_timeout = check_timeout
        self.debug = debug
        self.username = username
        self.password = password
        self.show_progress = show_progress
        self.workers_per_proxy = workers_per_proxy


opts = Options()


class Proxy:
    """
    class for one proxy, holds all workers bound to it, banned/dead status, raw address in a string and address formatted according to requests module
    """

    def __init__(self, proxy_address, proxy_type: ProxyType = ProxyType.https, user=None, password=None):
        self.proxy = proxy_address
        self.dead = False
        self.banned = False
        self.workers = []
        self.dict_proxy = {
            "http": f"{proxy_type.name}://{user}:{password}@{proxy_address}",
            "https": f"{proxy_type.name}://{user}:{password}@{proxy_address}",
        } if user != "" and password != "" else {
            "http": f"{proxy_type.name}://{proxy_address}",
            "https": f"{proxy_type.name}://{proxy_address}",
        }
        self.type = proxy_type

    def __hash__(self):
        return self.proxy.__hash__()


class ProxyList:
    """
    Holder of proxy lists for all supported proxy types
    """
    def __init__(self):
        self.size = 0
        self.dict = {
            ProxyType.http: [],
            ProxyType.https: [],
            ProxyType.socks5: [],
            ProxyType.socks5h: [],
        }

    def add_proxy(self, proxy: str, proxy_type: ProxyType = ProxyType.https):
        """
        add a proxy from string to the list
        :param proxy: proxy in string format
        :param proxy_type: type of proxy
        :return: None
        """
        self.dict[proxy_type].append(Proxy(proxy, proxy_type, opts.username, opts.password))
        self.size += 1

    def add_proxy_class(self, proxy: Proxy):
        """
        add a proxy as an instance of Proxy class
        :param proxy: proxy to be added, must have Proxy.type set!
        :return: None
        """
        self.dict[proxy.type].append(proxy)
        self.size += 1

    def clear_proxies(self, proxy_type: ProxyType = ProxyType.https):
        """
        clears a proxy list of specific type
        :param proxy_type: type of proxy list to clear
        :return: None
        """
        self.size -= len(self.dict[proxy_type])
        self.dict[proxy_type] = []

    def update_size(self):
        """
        recalculate the number of proxies in total (after removing, adding without using the add_proxy method)
        :return: None
        """
        self.size = 0
        for plist in self.dict.values():
            self.size += len(plist)


proxy_list = ProxyList()


def prequest(method, url, **kwargs):
    """
    Sends a request to url with method method, using proxy bound to current thread
    :param method: 'post' / 'get' / 'put' / ...
    :param url: target url
    :param kwargs: additional arguments (headers, payload, ...), if session is specified, it will be used to send the request
    :return: requests.models.Response
    """
    if "proxy" not in current_thread().__dict__:
        get_new_proxy()
    kwargs["proxies"] = current_thread().__dict__["proxy"].dict_proxy
    if "session" in kwargs.keys():
        session = kwargs["session"]
        del kwargs["session"]
    else:
        session = None
    if "max_retries" in kwargs.keys():
        max_retries = kwargs["max_retries"]
        del kwargs["max_retries"]
    else:
        max_retries = 50
    retries = 0
    while True:
        try:
            if session:
                response = session.request(method, url, **kwargs)
            else:
                response = request(method, url, **kwargs)
            return response
        except (Timeout, ProxyError):
            if opts.debug:
                print(f"Proxy {current_thread().__dict__['proxy'].proxy} dead, getting a new one.")
            get_new_proxy(dead=True)
            retries += 1
            if max_retries == retries:
                raise ConnectionError
            continue


def pget(url, params=None, **kwargs):
    """
    send GET request to a url with a proxy bound to current thread
    :param url: target url
    :param params: request parameters
    :param kwargs: additional arguments (headers, payload, ...), if session is specified, it will be used to send the request
    :return: requests.models.Response
    """
    kwargs.setdefault('allow_redirects', True)
    return prequest("get", url, params=params, **kwargs)


def ppost(url, params=None, **kwargs):
    """
    send POST request to a url with a proxy bound to current thread
    :param url: target url
    :param params: request parameters
    :param kwargs: additional arguments (headers, payload, ...), if session is specified, it will be used to send the request
    :return: requests.models.Response
    """
    kwargs.setdefault('allow_redirects', True)
    return prequest("get", url, params=params, **kwargs)


def _choose_from_enum(en, request_text="Please choose from following options:", default_number=0):
    """
    show a menu for the user to choose from different enum possibilities
    :param en: enum to choose from
    :param request_text: request to be shown to the user
    :param default_number: default enum value to be chosen
    :return: en(default_number)
    """
    print(request_text)
    if len(en) == 0:
        return None
    if default_number >= len(en):
        default_number = 0
    for e in en:
        print(f"{e.value} -> {e.name}")
    try:
        selection_num = int(input(f"Please select (default = {default_number}) -> "))
        if 0 <= selection_num < len(en):
            return en(selection_num)
    except ValueError:
        pass
    return en(default_number)


def _choose_from_list(lst: list, request_text="Please choose from following options:", default_number=0):
    """
    show a menu for the user to choose from different list items
    :param lst: list to choose from
    :param request_text: request to be shown to the user
    :param default_number: item at this index in the list will be chosen as default
    :return: lst[default_number]
    """
    print(request_text)
    if len(lst) == 0:
        return None
    if default_number >= len(lst):
        default_number = 0
    for i in range(len(lst)):
        print(f"{i} -> {lst[i]}")
    try:
        selection_num = int(input(f"Please select (default = {default_number}) -> "))
        if 0 <= selection_num < len(lst):
            return lst[selection_num]
    except ValueError:
        pass
    return lst[default_number]


def get_external_ip(p: Proxy = None):
    """
    determines the current external ip being used to connect to the internet
    :param p: proxy to connect through
    :return: None if connection error, else ipv4 in string
    """
    global opts
    try:
        if p:
            response = request("get", opts.judge.url, timeout=opts.check_timeout, proxies=p.dict_proxy)
        else:
            if __name__ == '__main__':
                print("Getting your IP address, please hold up")
            response = request("get", opts.judge.url, timeout=opts.check_timeout)
        soup = BeautifulSoup(response.text, 'html.parser').pre.text
        args = re.split('\n| = ', soup)
        for i in range(len(args)):
            if args[i] == "REMOTE_ADDR":
                return args[i + 1]
    except RequestException:
        if opts.debug and p is None:
            print("Please make sure you have access to the internet and try again.")
    return None


def check_proxy(prx: str):
    """
    checks a proxy in string format [0-255].[0-255].[0-255].[0-255]:[0-65535]
    :param prx: proxy as a string
    :return: True if valid format else False
    """
    spl = prx.split(".")
    if len(spl) != 4:
        return False
    try:
        if 0 < int(spl[0]) < 256 and 0 <= int(spl[1]) < 256 and 0 <= int(spl[2]) < 256:
            last = spl[3].split(":")
            if len(last) != 2:
                return False
            if 0 <= int(last[0]) < 256 and 0 < int(last[1]) < 65536:
                return True
    except TypeError:
        return False
    return False


def get_new_proxy(dead=False, banned=False):
    """
    binds a new proxy from the internal proxy list to the current thread while possibly marking the old one as banned or dead
    :param dead: current proxy dead?
    :param banned: current proxy banned?
    :return: None
    """
    global opts
    if "proxy" in current_thread().__dict__.keys():
        if dead:
            current_thread().__dict__["proxy"].dead = True
        if banned:
            current_thread().__dict__["proxy"].banned = True
        current_thread().__dict__["proxy"].workers.remove(current_thread())
    new = get_proxy()
    new.workers.append(current_thread())
    current_thread().__dict__["proxy"] = new


def test_proxy(prx: Proxy):
    """
    checks if proxy is working and anonymous
    :param prx: proxy: Proxy class
    :return: Proxy if working else False
    """
    global opts
    ip = get_external_ip(prx)
    if not ip:
        if opts.debug:
            print(f"Proxy {prx.proxy} not working.")
    elif ip != _host_ip:
        return prx
    elif opts.debug:
        print("Proxy Non-Anonymous, skipping.")
    return False


def proxy_on_checked(future, threads: int):
    """
    callback for check threads, not to be called otherwise, updates stats and proxy list (checked list)
    :param threads: number of threads currently running, passed from threadpoolexecutor
    :param future: future object handling the current proxy check
    :return: None
    """
    global _checked
    if not future.result():
        proxy_stats["dead"] += 1
    else:
        proxy_stats["alive"] += 1
        _checked.append(future.result())
    if opts.show_progress:
        update_proxy_stats(threads)


def parse_proxies(proxy_file, proxy_type: ProxyType = ProxyType.https):
    """
    parses proxies from a file
    :param proxy_type: type of proxies to be parsed
    :param proxy_file: VALID path to a text file containing proxies
    :return: None
    """
    global proxy_list, proxy_stats, opts
    if __name__ == '__main__':
        opts.proxy_type = _choose_from_enum(ProxyType, "Please choose type of proxies:", 1).name
    if __name__ == '__main__':
        opts.username = input("Please enter username for proxies (blank for no login) -> ")
        if opts.username != "":
            opts.password = input("Please enter password for proxies -> ")
    with open(proxy_file) as p_file:
        for line in p_file.readlines():
            line = line.strip()
            if check_proxy(line):
                proxy_list.add_proxy(line, proxy_type)
                proxy_stats["suc"] += 1
            else:
                proxy_stats["fail"] += 1
    proxy_list.dict[proxy_type] = list(unique(proxy_list.dict[proxy_type], key=lambda x: x.__hash__()))
    proxy_list.update_size()
    if opts.show_progress:
        print(f"\nSuccessfully parsed: {proxy_stats['suc'] - proxy_stats['dead']} {proxy_type.name} proxies.")


def check_proxies():
    """
    checks all the parsed proxies - all the types
    :return: None
    """
    global proxy_list, _checked, _host_ip
    if __name__ == "__main__":
        opts.judge = _choose_from_enum(Judge, "Please select a proxy judge:")
    _host_ip = get_external_ip()
    with ThreadPool(max_workers=opts.proxy_check_threads) as pool:
        for proxy_type in ProxyType:
            if len(proxy_list.dict[proxy_type]) == 0:
                continue
            futures = {pool.submit(test_proxy, proxy): proxy for proxy in proxy_list.dict[proxy_type]}
            # for proxy in proxy_list.dict[proxy_type]:
            #     pool.submit(test_proxy, proxy).add_done_callback(proxy_on_checked)
            if opts.show_progress:
                print(f"\nCurrently checking {proxy_type.name} proxies:")
            for future in as_completed(futures):
                proxy_on_checked(future, len(pool._threads))
            proxy_list.dict[proxy_type] = _checked
            _checked = []
            proxy_list.update_size()
    if opts.show_progress:
        print()


def print_proxy_stats():
    """
    prints out current progress in checking proxies, called first in code
    :return: None
    """
    global proxy_stats
    print(
        f"\nImported: {proxy_stats['suc']} | Dumped: {proxy_stats['fail']} | Dead: {proxy_stats['dead']} | Alive: {proxy_stats['alive']} | Running threads: 0 ",
        end="")


def update_proxy_stats(threads: int):
    """
    prints out current progress in checking proxies, called by finished threads
    :return: None
    """
    global proxy_stats
    print(
        f"\rImported: {proxy_stats['suc']} | Dumped: {proxy_stats['fail']} | Dead: {proxy_stats['dead']} | Alive: {proxy_stats['alive']} | Running threads: {threads} ",
        end="")


def reset_proxies():
    """
    resets all the proxies, locks other threads from doing so as well
    :return: None
    """
    global proxy_list, _resetting, opts
    if _resetting:
        while _resetting:
            sleep(0.5)
        return
    _resetting = True
    if opts.debug:
        print("Resetting proxies..")
    for proxy_type in ProxyType:
        for p in proxy_list.dict[proxy_type]:
            p.banned = False
            p.dead = False
    _resetting = False


def get_proxy():
    """
    returns the first available proxy from proxies list, resets if all banned
    :return: Proxy class or None if proxy list is empty
    """
    global proxy_list, opts
    if proxy_list.size == 0:
        return None
    while 1:
        for proxy_type in ProxyType:
            for i in range(len(proxy_list.dict[proxy_type])):
                if len(proxy_list.dict[proxy_type][i].workers) < opts.workers_per_proxy and not \
                        proxy_list.dict[proxy_type][i].dead and not proxy_list.dict[proxy_type][i].banned:
                    if opts.debug:
                        print(f"New proxy {proxy_list.dict[proxy_type][i].proxy}")
                    return proxy_list.dict[proxy_type][i]
        if opts.debug:
            print("Out of proxies", end="")
        if 1.2 * opts.workers_per_proxy * (active_count() - 1) >= proxy_list.size:
            # do not reset proxies when there are more threads than proxies possibly available to them, up to 20% banned is ok
            # will change this later to something more sophisticated
            sleep(0.5)
            continue
        reset_proxies()


def update_options(options):
    """
    changes internal options to provided ones
    :param options: Options class with all options set
    :return: None
    """
    global opts
    opts = options


def open_proxy_file(proxy_type: ProxyType = ProxyType.https):
    """
    opens a file dialog to choose the proxy file, parses it afterwards
    :return: None
    """
    global proxy_list
    if __name__ == '__main__':
        print(
            "--------IMPORTANT--------\nRequired proxy format - '0.0.0.0:0', one per line ONLY\n--------IMPORTANT--------")
    proxies_file = filedialog.askopenfilename(title="Select proxy file.", filetypes=[("Text files", "*.txt")])
    parse_proxies(proxies_file, proxy_type)


if __name__ == '__main__':
    """
    ^^
    """
    open_proxy_file()
