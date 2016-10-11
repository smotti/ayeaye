from setuptools import setup

setup(name='ayeaye',
    version='1.0',
    packages=['ayeaye'],
    description='MedicusTek notification service',
    author='John.Liu, Jordan.Lin, William.Ott',
    author_email='john.liu@medicustek.com, jordan.lin@medicustek.com, william.ott@medicustek.com',
    scripts=['ayeaye/ayeaye'],
    package_dir={'ayeaye': 'ayeaye'},
    package_data={'ayeaye': ['schema.sql']},
    data_files=[('/usr/bin', ['ayeaye/ayeaye']),
                ('/etc/systemd/system', ['resources/ayeaye.service']),
                ('/etc/systemd/system/ayeaye.service.d', ['resources/ayeaye.conf'])
                ('/var/lib/medicustek/ayeaye', ['requirements.txt'])]
#    install_requires=['arrow', 'flask', 'flask-cors']
    )
