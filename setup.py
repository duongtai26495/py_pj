from setuptools import setup

APP = ['AdsReport_v1.py']
DATA_FILES = []

OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'bthf.icns',
    'packages': ['tkcalendar'],
    'excludes': ['packaging'],  # Loại trừ package packaging
    'plist': {
        'CFBundleName': 'ReportQuangCao',
        'CFBundleShortVersionString': '1.0',
        'CFBundleIdentifier': 'com.marcom.baocaquangcao',
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
