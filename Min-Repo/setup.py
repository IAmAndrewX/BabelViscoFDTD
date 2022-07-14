from setuptools import setup, Extension, find_packages, Command
import subprocess
from setuptools import setup
from setuptools.command.build_ext import build_ext as _build_ext
from os import path
import sys, sysconfig
import os


class build_ext(_build_ext):
      def finalize_options(self):
            print("Building Metal...")
            command=['xcrun','-sdk', 'macosx', 'metal','-c','metal.metal','-o', 'metal.air']
            subprocess.check_call(command)
            command=['xcrun','-sdk', 'macosx', 'metallib', 'metal.air','-o', 'metal.metallib']
            subprocess.check_call(command)
            print("Building Swift...")
            command=['swiftc','-emit-library','func.swift']
            subprocess.check_call(command)
            _build_ext.finalize_options(self)
            # Prevent numpy from thinking it is still in its setup process:
            __builtins__.__NUMPY_SETUP__ = False
            import numpy
            self.include_dirs.append(numpy.get_include())        



def FunctionCompiler():
      command=['swift','build','-c', 'release']

if __name__ == "__main__":
      FunctionCompiler()
      setup(name = 'myModule', version = 1, cmdclass={'build_ext':build_ext},
            setup_requires=['numpy'], ext_modules= [Extension('myModule', ['commands.c'], extra_objects = ["libfunc.dylib"])])




