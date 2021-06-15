import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(name='behavior_machine',
                 version='0.3.5',
                 description='An implementation of a behavior tree + hierarchical state machine hybrid.',
                 long_description=long_description,
                 long_description_content_type="text/markdown",
                 author='Xiang Zhi Tan',
                 url='https://github.com/CMU-TBD/behavior_machine',
                 author_email='zhi.tan@ri.cmu.edu',
                 packages=setuptools.find_packages(),
                 install_requires=[
                 ],
                 license='MIT',
                 python_requires='>=3.6')
