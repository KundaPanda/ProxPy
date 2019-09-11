# ProxPy
*This is a work-in-progress python module that serves as a wrapper around requests with proxy support*

*I do not hold any responsibility for any actions taken using this module*

---
ProxPy allows you to effortlessly use multiple proxies imported from a text file without having to deal with any configuration.

Multithreading is fully supported with automatic proxy assignment to each thread, ban/dead detection, multiple workers per proxy and recycling after all proxies have been marked as dead or banned.

## Currently supported proxies:

* **http**
* **https**
* **socks5** (socks5h)

## Variables:
```python
class ProxyType(Enum):
    """
    enum specifying type of proxies being used
    """
    
    socks5h = 0
    socks5 = 1
    https = 2
    http = 3
```
```python
class Judge(Enum):
    """
    Proxy judge enum
    """
    
    azenv = "https://azenv.net"
    proxyjudge = "http://proxyjudge.info"
```
```python
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
```
```python
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
        }
        self.type = proxy_type
```
```python
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

    #
    # ---**METHODS**---
    #
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
```
```python
# Internal variables:
# these are used by all the functions, can be accessed freely, should not be modified directly

proxy_list = ProxyList()
opts = Options()

_root = tk.Tk()
_resetting = False
_checked = []
_host_ip = ""

proxy_stats = {
    "suc": 0,
    "fail": 0,
    "alive": 0,
    "dead": 0
}
```
## Methods:
#### **All with simplified functionality**

```python
def prequest(method, url, **kwargs):
    """
    Sends a request to url with method method, using proxy bound to current thread
    :param method: 'post' / 'get' / 'put' / ...
    :param url: target url
    :param kwargs: additional arguments (headers, payload, ...), if session is specified, it will be used to send the request
    :return: requests.request
    """
    return request(method, url, **kwargs)
```
```python
def ppost(url, params=None, **kwargs):
    """
    send POST request to a url with a proxy bound to current thread
    :param url: target url
    :param params: request parameters
    :param kwargs: additional arguments (headers, payload, ...), if session is specified, it will be used to send the request
    :return: requests.models.Response
    """
    return prequest("post", url, params=params, **kwargs)
```
```python
def pget(url, params=None, **kwargs):
    """
    send GET request to a url with a proxy bound to current thread
    :param url: target url
    :param params: request parameters
    :param kwargs: additional arguments (headers, payload, ...), if session is specified, it will be used to send the request
    :return: requests.models.Response
    """
    return prequest("get", url, params=params, **kwargs)
```
```python
def get_external_ip(p: Proxy = None):
    """
    determines the current external ip being used to connect to the internet
    :param p: proxy to connect through
    :return: None if connection error, else ipv4 in string
    """
    return ipv4 if connection.ok else None
```
```python
def check_proxy(prx: str):
    """
    checks a proxy in string format [0-255].[0-255].[0-255].[0-255]:[0-65535]
    :param prx: proxy as a string
    :return: True if valid format else False
    """
    return True of proxy.valid_format else False
```
```python
def get_new_proxy(dead=False, banned=False):
    """
    binds a new proxy from the internal proxy list to the current thread while possibly marking the old one as banned or dead
    :param dead: current proxy dead?
    :param banned: current proxy banned?
    :return: None
    """
    this_thread.bind_new_proxy(get_proxy_from_list())
```
```python
def test_proxy(prx: Proxy):
    """
    checks if proxy is working and anonymous
    :param prx: proxy: Proxy class
    :return: Proxy if working else False
    """
    return prx if prx.working else False
```
```python
def parse_proxies(proxy_file, proxy_type: ProxyType = ProxyType.https):
    """
    parses proxies from a file
    :param proxy_type: type of proxies to be parsed
    :param proxy_file: VALID path to a text file containing proxies
    :return: None
    """
    for valid_proxy in proxy_file:
        proxies.append(proxy)
```
```python

def check_proxies():
    """
    checks all the parsed proxies - all the types
    :return: None
    """
    for proxy in proxies:
        if proxy.not_working:
            proxies.remove(proxy)
```
```python
def reset_proxies():
    """
    resets all the proxies, locks other threads from doing so as well
    :return: None
    """
    for proxy in proxies:
        proxy.banned, proxy.dead = False, False
```
```python
def get_proxy():
    """
    returns the first available proxy from proxies list, resets if all banned
    :return: Proxy class or None if proxy list is empty
    """
    for proxy in proxies:
        if proxy.available:
            return proxy
```
```python
def update_options(options):
    """
    changes internal options to provided ones
    :param options: Options class with all options set
    :return: None
    """
    global opts
    opts = options
```
```python
def open_proxy_file(proxy_type: ProxyType = ProxyType.https):
    """
    opens a file dialog to choose the proxy file, parses it afterwards
    :return: None
    """
    parse_proxies(open_file_dialog())
```

## Please note: 
As this is an early release, reverse compatibility will most likely NOT be present at the moment

Some things may crash / behave oddly - if so, please report them on github