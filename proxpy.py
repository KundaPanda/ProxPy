from threading import current_thread, active_count
from time import sleep
from toolz import unique
import tkinter as tk
from tkinter import filedialog
from enum import Enum
from requests import request
from requests.exceptions import RequestException, ProxyError, Timeout
from concurrent.futures import ThreadPoolExecutor as ThreadPool
import re
from bs4 import BeautifulSoup

# TODO: COMMENTS

name = "ProxPy"

root = tk.Tk()
root.withdraw()

checked = []
proxies = []
resetting = False
proxy_stats = {
    "suc": 0,
    "fail": 0,
    "alive": 0,
    "dead": 0
}
host_ip = ""


class ProxyType(Enum):
    http = 0
    https = 1
    socks5 = 2
    socks5h = 3


class Judge(Enum):
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
    def __init__(self, proxy_type=ProxyType.https, username="", password="", judge=Judge.azenv, proxy_check_threads=50,
                 check_timeout=4,
                 debug=False,
                 show_progress=True):
        self.judge = judge
        self.proxy_check_threads = proxy_check_threads
        self.check_timeout = check_timeout
        self.debug = debug
        self.proxy_type = proxy_type
        self.username = username
        self.password = password
        self.show_progress = show_progress


opts = Options()


class Proxy:
    def __init__(self, proxy_address, proxy_type=ProxyType.https.name, user=None, password=None):
        self.proxy = proxy_address
        self.dead = False
        self.banned = False
        self.workers = []
        self.dict_proxy = {
            "http": f"{proxy_type}://{user}:{password}@{proxy_address}",
            "https": f"{proxy_type}://{user}:{password}@{proxy_address}",
        } if user != "" and password != "" else {
            "http": f"{proxy_type}://{proxy_address}",
            "https": f"{proxy_type}://{proxy_address}",
        }

    def __hash__(self):
        return self.proxy.__hash__()


def prequest(method, url, **kwargs):
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
        max_retries = len(proxies)
    retries = 0
    while True:
        try:
            if session:
                response = session.request(method, url, **kwargs)
            else:
                response = request(method, url, **kwargs)
            return response
        except (Timeout, ProxyError):
            get_new_proxy(dead=True)
            retries += 1
            if max_retries == retries:
                raise ConnectionError
            continue


def pget(url, params=None, **kwargs):
    kwargs.setdefault('allow_redirects', True)
    return prequest("get", url, params=params, **kwargs)


def ppost(url, params=None, **kwargs):
    kwargs.setdefault('allow_redirects', True)
    return prequest("get", url, params=params, **kwargs)


def choose_from_enum(en, request_text="Please choose from following options:", default_number=0):
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


def choose_from_list(lst: list, request_text="Please choose from following options:", default_number=0):
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
        if opts.debug:
            print("Please make sure you have access to the internet and try again.")
    return None


def check_proxy(prx: str):
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
    global opts
    if "proxy" in current_thread().__dict__.keys():
        if opts.debug:
            print("Proxy down.", current_thread().__dict__["proxy"].proxy)
        if dead:
            current_thread().__dict__["proxy"].dead = True
        if banned:
            current_thread().__dict__["proxy"].banned = True
        current_thread().__dict__["proxy"].workers.remove(current_thread())
    new = get_proxy()
    new.workers.append(current_thread())
    current_thread().__dict__["proxy"] = new


def test_proxy(prx: Proxy):
    global opts
    ip = get_external_ip(prx)
    if not ip:
        if opts.debug:
            print("Proxy not working.")
    elif ip != host_ip:
        return prx
    elif opts.debug:
        print("Proxy Non-Anonymous, skipping.")
    return False


def proxy_on_checked(future):
    global checked
    if not future.result():
        proxy_stats["dead"] += 1
    else:
        proxy_stats["alive"] += 1
        checked.append(future.result())
    if opts.show_progress:
        update_proxy_stats()


def parse_proxies(proxy_file):
    global proxies, proxy_stats, opts
    if __name__ == '__main__':
        opts.proxy_type = choose_from_enum(ProxyType, "Please choose type of proxies:", 1).name
    if __name__ == '__main__':
        opts.username = input("Please enter username for proxies (blank for no login) -> ")
        if opts.username != "":
            opts.password = input("Please enter password for proxies -> ")
    with open(proxy_file) as p_file:
        for line in p_file.readlines():
            line = line.strip()
            if check_proxy(line):
                proxies.append(Proxy(line, opts.proxy_type.name, opts.username, opts.password))
                proxy_stats["suc"] += 1
            else:
                proxy_stats["fail"] += 1
    proxies = list(unique(proxies, key=lambda x: x.__hash__()))
    if opts.show_progress:
        print(f"\nSuccessfully parsed: {proxy_stats['suc'] - proxy_stats['dead']} proxies.")


def check_proxies():
    global proxies, checked, host_ip
    if __name__ == "__main__":
        opts.judge = choose_from_enum(Judge, "Please select a proxy judge:")
    host_ip = get_external_ip()
    with ThreadPool(max_workers=opts.proxy_check_threads) as pool:
        for proxy in proxies:
            pool.submit(test_proxy, proxy).add_done_callback(proxy_on_checked)
    proxies = checked
    if opts.show_progress:
        print()


def print_proxy_stats():
    global proxy_stats
    print(
        f"\nImported: {proxy_stats['suc']} | Dumped: {proxy_stats['fail']} | Dead: {proxy_stats['dead']} | Alive: {proxy_stats['alive']} | Running threads: {active_count() - 1} ",
        end="")


def update_proxy_stats():
    global proxy_stats
    print(
        f"\rImported: {proxy_stats['suc']} | Dumped: {proxy_stats['fail']} | Dead: {proxy_stats['dead']} | Alive: {proxy_stats['alive']} | Running threads: {active_count() - 1} ",
        end="")


def reset_proxies():
    global proxies, resetting, opts
    if resetting:
        while resetting:
            sleep(0.5)
        return
    resetting = True
    if opts.debug:
        print("Resetting proxies..")
    for p in proxies:
        p.banned = False
        p.dead = False
    resetting = False


def get_proxy():
    global proxies, opts
    i = 0
    while len(proxies[i].workers) >= 5 or proxies[i].dead or proxies[i].banned:
        i += 1
        if i >= len(proxies):
            if opts.debug:
                print("Out of proxies", end="")
            reset_proxies()
            i = 0
    if opts.debug:
        print(f"New proxy {proxies[i].proxy}")
    return proxies[i]


def open_proxy_file(options=opts):
    global proxies, opts
    opts = options
    if __name__ == '__main__':
        print(
            "--------IMPORTANT--------\nRequired proxy format - '0.0.0.0:0', one per line ONLY\n--------IMPORTANT--------")
    proxies_file = filedialog.askopenfilename(title="Select proxy file.", filetypes=[("Text files", "*.txt")])
    parse_proxies(proxies_file)


if __name__ == '__main__':
    open_proxy_file()
