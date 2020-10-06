# Guide for developers

Welcome to PyMOL KVFinder-web Tools guide, which aims to aid developers with relevant information about its operation.

1. [Download & Installation](#Download\ &\ Installation)
    - [PyMOL Installation](#PyMOL\ Installation)
2. [Code Description](#Code\ Description)
    - Threads
    - Classes
    - HTTP Responses

---

## Download & Installation

[PyMOL v2](https://pymol.org/2/) is required if you wish to use PyMOL KVFinder-web Tools. If necessary, refer to this [section](#PyMOL\ Installation) for installing PyMOL.

Follow these steps to install PyMOL KVFinder-web Tools:

- Download the latest release of PyMOL KVFinder-web Tools from [here](https://github.com/jvsguerra/kvfinder-ws/releases/download/v0.1/PyMOL-KVFinder-web-tools.zip).

    1. Open PyMOL;
    2. Go to **Plugin** menu &rarr; **Plugin Manager**;
    3. The **Plugin Manager** window will open, go to the **Install New Plugin** tab;
    4. Under **Install from local file** group, click on **Choose file...**;
    5. The **Install Plugin** window will open, select the `PyMOL-KVFinder-web-Tools.zip`;
    6. The **Select plugin directory** window will open, select `/home/user/.pymol/startup` and click **OK**;
    7. The **Confirm** window will open, click on **OK**;
    8. The **Sucess** window will open, confirming that the plugin has been installed;
    9. Restart PyMOL;
    10. **PyMOL KVFinder-web Tools** is ready to use under **Plugin** menu.


Or, if you clone this [repository](https://github.com/jvsguerra/kvfinder-ws), instead of selecting PyMOL-KVFinder-web-Tools.zip (Step 5), user must select `__init__.py` of PyMOL-KVFinder-web-Tools directory

2. Install the necessary Python modules from [requirements.txt](https://github.com/jvsguerra/kvfinder-ws/blob/master/client/requirements.txt) file.

```bash
pip3 install -r requirements.txt
```

---

## PyMOL Installation

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
