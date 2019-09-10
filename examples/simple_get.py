import proxpy

my_options = proxpy.Options(proxy_check_threads=200, check_timeout=5, judge=proxpy.Judge.azenv, show_progress=True)

proxpy.update_options(my_options)
proxpy.open_proxy_file()
proxpy.check_proxies()

print(f"Alive: {proxpy.proxy_stats['alive']}, Dead: {proxpy.proxy_stats['dead']}")
print("Proxy list length: ", len(proxpy.proxies))

response = proxpy.pget("https://www.google.com", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0"}, max_retries=20)

print(response.status_code)
with open("google.html", "w+") as afile:
    afile.writelines(response.text)
