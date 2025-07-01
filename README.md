# AndroidADBFileTransfer
This repo aims to provide convenient and fast exportation of media files from **Android devices to a Mac**. It relies on Android Debug Bridge, and thus requires Developer Mode to be enabled on your devices. If you don't know how to enable that, please refer to [Enable Developer Options | Google](https://developer.android.com/studio/debug/dev-options)

# How to use
1. Copy the `adb` executable file to one of the env PATHs. Use `which adb` to verify that the file has been successfully added to your environment.
2. Execute `main.app`. For security concerns, use `pyinstaller` to compile your own app.

# Why am I doing this?
I've tried OpenMTP and Android File Transfer to copy media files from my Android devices to my Mac, but neither of them has been satisfactory.

Android File Transfer suffers from extremely unstable connections, while OpenMTP's opening speed of folders with lots of data is too slow. Additionally, OpenMTP struggles to freely select multiple files for export.
