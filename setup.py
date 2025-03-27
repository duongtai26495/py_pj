from setuptools import setup

APP = ['automation_get_attendance_v2.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,  # Hữu ích nếu bạn muốn truyền tham số từ dòng lệnh
    'packages': [],          # Nếu cần include các package khác, thêm tên chúng vào đây
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
