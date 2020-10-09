from setuptools import setup

setup(name='plaza-toggl-service',
      version='0.0.1',
      description='Plaza service to interact with toggl.com',
      author='kenkeiras',
      author_email='kenkeiras@codigoparallevar.com',
      license='Apache License 2.0',
      packages=['plaza_toggl_service'],
      scripts=['bin/plaza-toggl-service'],
      include_package_data=True,
      install_requires = [
          'togglpy',
          'programaker_bridge',
          'xdg',
      ],
      zip_safe=False)
