# AndroidADBFileTransfer
This repo aims at providing convenient and fast exportation of media files from Android devices to Mac. It relies on Android Debug Bridge, and thus require Debuggable Mode to be enabled on your devices.

# How to use
1. copy the `adb` executable file to one of the env PATHs. Use `which adb` to make sure the file is successfully added to your environment.
2. Execute `main.app`. For security concerns, use `pyinstaller` to compile your own app.

# Why am I doing this?
I've tried OpenMTP and Android File Transfer to copy media files from my Android devices to Mac, but neither of them are very satisfying.

Android File Transfer suffers from extremely unstable connection, while OpenMTP opening speed of folders with lots of data is too slow. In addition, OpenMTP supports badly at freely selecting multiple files to export.
