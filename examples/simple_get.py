import ProxPy

my_options = ProxPy.Options(proxy_check_threads=500, check_timeout=5, judge=ProxPy.Judge.azenv, show_progress=True, workers_per_proxy=6, debug=True)

ProxPy.update_options(my_options)
ProxPy.open_proxy_file(proxy_type=ProxPy.ProxyType.https)
ProxPy.check_proxies()

print(f"Alive: {ProxPy.proxy_stats['alive']}, Dead: {ProxPy.proxy_stats['dead']}")
print("Proxy list length: ", ProxPy.proxy_list.size)

response = ProxPy.pget("https://google.com", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0"}, timeout=5, max_retries=8)

print(response.status_code)
with open("google.html", "w+") as afile:
    afile.writelines(response.text)
