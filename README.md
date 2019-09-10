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
    http = 0
    https = 1
    socks5 = 2
    socks5h = 3
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
    def __init__(self, 
                 proxy_type=ProxyType.https,
                 username="", 
                 password="", 
                 judge=Judge.azenv, 
                 proxy_check_threads=50,
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
```
```python
class Proxy:
    """
    class for one proxy, holds all workers bound to it, banned/dead status, raw address in a string and address formatted according to requests module
    """
    def __init__(self, proxy_address, proxy_type=ProxyType.https.name, user=None, password=None):
        self.proxy = proxy_address
        self.dead = False
        self.banned = False
        self.workers = []
        self.dict_proxy = {
            "http": f"{proxy_type}://{user}:{password}@{proxy_address}",
            "https": f"{proxy_type}://{user}:{password}@{proxy_address}",
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
def parse_proxies(proxy_file):
    """
    parses proxies from a file
    :param proxy_file: VALID path to a text file containing proxies
    :return: None
    """
    for valid_proxy in proxy_file:
        proxies.append(proxy)
```
```python

def check_proxies():
    """
    checks all the parsed proxies
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
    returns the first available proxy from proxies list
    :return: Proxy class
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
def open_proxy_file():
    """
    opens a file dialog to choose the proxy file, parses it afterwards
    :return: None
    """
    parse_proxies(open_file_dialog())
```

## Please note: 
As this is an early release, reverse compatibility will most likely NOT be present at the moment

Some things may crash / behave oddly - if so, please report them on github