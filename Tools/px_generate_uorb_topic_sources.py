#!/usr/bin/env python
#############################################################################
#
#   Copyright (C) 2013-2015 PX4 Development Team. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name PX4 nor the names of its contributors may be
#    used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
#############################################################################

"""
px_generate_uorb_topic_sources.py
Generates cpp source files for uorb topics from .msg (ROS syntax)
message files
"""
from __future__ import print_function
import os
import shutil
import filecmp
import argparse

try:
        import em
        import genmsg.template_tools
except ImportError as e:
        print("python import error: ", e)
        print('''
Required python packages not installed.

On a Debian/Ubuntu system please run:

  sudo apt-get install python-empy
  sudo pip install catkin_pkg

On MacOS please run:
  sudo pip install empy catkin_pkg

On Windows please run:
  easy_install empy catkin_pkg
''')
        exit(1)

__author__ = "Sergey Belash, Thomas Gubler"
__copyright__ = "Copyright (C) 2013-2014 PX4 Development Team."
__license__ = "BSD"
__email__ = "againagainst@gmail.com, thomasgubler@gmail.com"

TEMPLATE_FILE = 'msg.cpp.template'
OUTPUT_FILE_EXT = '.cpp'
PACKAGE = 'px4'
TOPICS_TOKEN = '# TOPICS '


def get_multi_topics(filename):
        """
        Get TOPICS names from a "# TOPICS" line
        """
        ofile = open(filename, 'r')
        text = ofile.read()
        result = []
        for each_line in text.split('\n'):
                if each_line.startswith (TOPICS_TOKEN):
                        topic_names_str = each_line.strip()
                        topic_names_str = topic_names_str.replace(TOPICS_TOKEN, "")
                        result.extend(topic_names_str.split(" "))
        ofile.close()
        return result


def generate_source_from_file(filename, outputdir, templatedir):
        """
        Converts a single .msg file to a uorb source file
        """
        # print("Generating sources from {0}".format(filename))
        msg_context = genmsg.msg_loader.MsgContext.create_default()
        full_type_name = genmsg.gentools.compute_full_type_name(PACKAGE, os.path.basename(filename))
        spec = genmsg.msg_loader.load_msg_from_file(msg_context, filename, full_type_name)
        topics = get_multi_topics(filename)
        if len(topics) == 0:
            topics.append(spec.short_name)
        em_globals = {
            "file_name_in": filename,
            "spec": spec,
            "topics": topics
        }

                # Make sure output directory exists:
        if not os.path.isdir(outputdir):
                os.makedirs(outputdir)

        template_file = os.path.join(templatedir, TEMPLATE_FILE)
        output_file = os.path.join(outputdir, spec.short_name + OUTPUT_FILE_EXT)

        if os.path.isfile(output_file):
            return False

        ofile = open(output_file, 'w')
        # todo, reuse interpreter
        interpreter = em.Interpreter(output=ofile, globals=em_globals, options={em.RAW_OPT:True,em.BUFFERED_OPT:True})
        if not os.path.isfile(template_file):
            ofile.close()
            os.remove(output_file)
            raise RuntimeError("Template file msg.cpp.template not found in template dir %s" % (templatedir))
        interpreter.file(open(template_file)) #todo try
        interpreter.shutdown()
        ofile.close()
        print("{0}: new source file".format(output_file))
        return True


def convert_dir(inputdir, outputdir, templatedir):
        """
        Converts all .msg files in inputdir to uORB sources
        """
        for f in os.listdir(inputdir):
                # Ignore hidden files
                if f.startswith("."):
                        continue

                fn = os.path.join(inputdir, f)
                # Only look at actual files
                if not os.path.isfile(fn):
                        continue

                generate_source_from_file(fn, outputdir, templatedir)

        return True


if __name__ == "__main__":
        parser = argparse.ArgumentParser(description='Convert msg files to uorb sources')
        parser.add_argument('-d', dest='dir', help='directory with msg files')
        parser.add_argument('-f', dest='file', help="files to convert (use only without -d)", nargs="+")
        parser.add_argument('-e', dest='templatedir', help='directory with template files',)
        parser.add_argument('-o', dest='outputdir', help='output directory for source files')
        args = parser.parse_args()

        if args.file is not None:
                for f in args.file:
                        generate_source_from_file(f, args.outputdir, args.templatedir)
        elif args.dir is not None:
                convert_dir(args.dir, args.outputdir, args.templatedir)
