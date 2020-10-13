from setuptools import setup

setup(name='programaker-toggl-service',
      version='0.0.1',
      description='Programaker service to interact with toggl.com',
      author='kenkeiras',
      author_email='kenkeiras@codigoparallevar.com',
      license='Apache License 2.0',
      packages=['programaker_toggl_service'],
      scripts=['bin/programaker-toggl-service'],
      include_package_data=True,
      install_requires = [
          'togglpy',
          'programaker_bridge',
          'xdg',
      ],
      zip_safe=False)
