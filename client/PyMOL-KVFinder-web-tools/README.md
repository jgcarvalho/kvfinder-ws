# Guide for developers

Welcome to PyMOL KVFinder-web Tools guide, which aims to aid developers with relevant information about its operation.

1. [Download & Installation](README.md#Download\ &\ Installation)
2. [Code Description](README.md#Code\ Description)
    - Threads
    - Classes
    - HTTP Responses


## Download & Installation

Download the PyMOL KVFinder-web Tools from [here](https://github.com/jvsguerra/kvfinder-ws/releases/download/v0.1/PyMOL-KVFinder-web-tools.zip).

## Code Description

### Threads

The KVFinder Web Tools has two threads:

- **Graphical User Interface (GUI)** thread: `class PyMOLKVFinderWebTools(QMainWindow)` that handles the interface objects, slots, signals and functions;

- **Worker** thread: `class Worker(QThread)` that checks constantly the jobs sent to KVFinder-web server (https://server-url) and automatically downloads them when completed.

#### GUI thread

#### Worker thread


### Classes 

1. PyMOL KVFinder Web Tools

2. Worker

3. Form

4. Message

5. Job

### Common HTTP Responses:

Responses (`QNetwork.QNetworkReply.error()`) from KVFinder-web server when `QtNetwork.AccessManager()` sents a `.get()` or `.post()` request:

- **0**: No Error - Sucessfull GET/POST request;

- **1**: Connection Refused Error - KVFinder-web server is currently offline;

- **203**: Content Not Found Error - The remote content was not found at KVFinder-web server;

- **299**: Unknown Content Error - The request entity is larger than limits defined by KVFinder-web server.
