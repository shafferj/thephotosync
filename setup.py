try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='photosync',
    version='0.1',
    description='',
    author='',
    author_email='',
    url='',
    install_requires=[
        "Pylons>=1.0",
        "SQLAlchemy>=0.5",
        "MySQL-python",
        "flickrapi",
        "gdata",
        "pycurl",
        "beanstalkc",
        "PyYAML",
        "functional",
    ],
    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'photosync': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors={'photosync': [
    #        ('**.py', 'python', None),
    #        ('templates/**.mako', 'mako', {'input_encoding': 'utf-8'}),
    #        ('public/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['PasteScript', 'Pylons'],
    entry_points="""
    [paste.app_factory]
    main = photosync.config.middleware:make_app

    [paste.app_install]
    main = photosync.installer:PhotosyncInstaller

    [paste.paster_command]
    runworker = photosync.worker.commands:RunWorkerCommand
    migrate = photosync.migrations.commands:RunMigrationCommand
    kick = photosync.commands:KickCommand
    """,
)
