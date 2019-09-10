# ProxPy
Python proxy module for requests, supports multithreading and http/https/socks proxies

TODO: readme ...

This is a work-in-progress project for adding simple web requests using a proxylist with multiple threads.
Uses python's requests module so all return values are the same.
Useful for applications which require multiple threads running different proxies without the hassle of managing workers per proxy, assigning these proxies and parsing them from files.
Also includes a multithreaded checker.
