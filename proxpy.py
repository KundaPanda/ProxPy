from threading import current_thread, active_count
from time import sleep
from toolz import unique
import tkinter as tk
from tkinter import filedialog
from enum import Enum
from requests import get, post, session
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor as ThreadPool
import re
from bs4 import BeautifulSoup

root = tk.Tk()
root.withdraw()

proxies = []
resetting = False
debug = False
proxy_stats = {
    "suc": 0,
    "fail": 0,
    "dead": 0
}
timeout = 6
check_timeout = 4
judges = [
    "https://azenv.net",
    "http://proxyjudge.info"
]
judge = judges[0]
host_ip = ""
proxy_check_threads = 50
checked = []


class ProxyType(Enum):
    http = 0
    https = 1
    socks4 = 2
    socks5 = 3


class Proxy:
    def __init__(self, proxy_address, proxy_type=ProxyType.https.name, user=None, password=None):
        self.proxy = proxy_address
        self.dead = False
        self.banned = False
        self.workers = []
        if user and password:
            self.dict_proxy = {
                "http": f"{proxy_type}://{user}:{password}@{proxy_address}",
                "https": f"{proxy_type}://{user}:{password}@{proxy_address}",
            }
        else:
            self.dict_proxy = {
                "http": f"{proxy_type}://{proxy_address}",
                "https": f"{proxy_type}://{proxy_address}",
            }

    def __hash__(self):
        return self.proxy.__hash__()


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
    try:
        if p:
            response = get(judge, timeout=check_timeout, proxies=p.dict_proxy)
        else:
            print("Getting your IP address, please hold up")
            response = get(judge, timeout=check_timeout)
        soup = BeautifulSoup(response.text, 'html.parser').pre.text
        args = re.split('\n| = ', soup)
        for i in range(len(args)):
            if args[i] == "REMOTE_ADDR":
                return args[i + 1]
    except RequestException:
        if debug:
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


def pretty_print_post(req):
    print('{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))


def get_proxy_thread(dead=False, banned=False):
    if "proxy" in current_thread().__dict__.keys():
        if debug:
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
    global judge
    ip = get_external_ip(prx)
    if not ip:
        if debug:
            print("Proxy not working.")
    elif ip != host_ip:
        return prx
    elif debug:
        print("Proxy Non-Anonymous, skipping.")
    return False


def proxy_on_checked(future):
    global checked
    if not future.result():
        proxy_stats["dead"] += 1
    else:
        checked.append(future.result())
    update_proxy_stats(True)


def parse_proxies(proxy_file, show_progress, test_proxies):
    global proxies, proxy_stats, judge, host_ip
    proxy_type = choose_from_enum(ProxyType, "Please choose type of proxies:", 1).name
    if test_proxies:
        judge = choose_from_list(judges, "Please select a proxy judge:")
        host_ip = get_external_ip()
    username = input("Please enter username for proxies (blank for no login) -> ")
    password = None
    if username != "":
        password = input("Please enter password for proxies -> ")
    else:
        username = None
    if show_progress:
        print("--- Starting proxy checking ---")
        print_proxy_stats(test_proxies)
    with open(proxy_file) as p_file:
        for line in p_file.readlines():
            line = line.strip()
            if check_proxy(line):
                proxies.append(Proxy(line, proxy_type, username, password))
                proxy_stats["suc"] += 1
            else:
                proxy_stats["fail"] += 1
            if show_progress:
                update_proxy_stats(test_proxies)
    if test_proxies:
        with ThreadPool(max_workers=proxy_check_threads) as pool:
            for proxy in proxies:
                pool.submit(test_proxy, proxy).add_done_callback(proxy_on_checked)
        proxies = checked
    proxies = list(unique(proxies, key=lambda x: x.__hash__()))
    if show_progress:
        print("--- Done checking proxies ---")
        print(f"\nSuccessfully parsed: {proxy_stats['suc'] - proxy_stats['dead']} proxies.")


def print_proxy_stats(test_proxies):
    global proxy_stats
    print(
        f"\nImported: {proxy_stats['suc']} | Dumped: {proxy_stats['fail']} {'| Dead: {}'.format(proxy_stats['dead']) if test_proxies else ''} {'| Alive: {}'.format(len(checked)) if test_proxies else ''} | Running threads: {active_count() - 1} ",
        end="")


def update_proxy_stats(test_proxies):
    global proxy_stats
    print(
        f"\rImported: {proxy_stats['suc']} | Dumped: {proxy_stats['fail']} {'| Dead: {}'.format(proxy_stats['dead']) if test_proxies else ''}  {'| Alive: {}'.format(len(checked)) if test_proxies else ''} | Running threads: {active_count() - 1} ",
        end="")


def reset_proxies():
    global proxies, resetting
    if resetting:
        while resetting:
            sleep(0.5)
        return
    resetting = True
    if debug:
        print("Resetting proxies..")
    for p in proxies:
        p.banned = False
        p.dead = False
    resetting = False


def get_proxy():
    global proxies
    i = 0
    while len(proxies[i].workers) >= 5 or proxies[i].dead or proxies[i].banned:
        i += 1
        if i >= len(proxies):
            if debug:
                print("Out of proxies", end="")
            reset_proxies()
            i = 0
    if debug:
        print(f"New proxy {proxies[i].proxy}")
    return proxies[i]


def open_proxy_file(test_proxies=True, show_progress=True):
    global proxies
    print("--------IMPORTANT--------\nRequired proxy format - '0.0.0.0:0', one per line ONLY\n--------IMPORTANT--------")
    proxies_file = filedialog.askopenfilename(title="Select proxy file.", filetypes=[("Text files", "*.txt")])
    parse_proxies(proxies_file, show_progress, test_proxies)


if __name__ == '__main__':
    open_proxy_file()
