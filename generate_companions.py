#!/usr/bin/env python3

import argparse
import os
from collections import namedtuple
from typing import List
import re

# This script is designed to find all files within a Scala codebase which contain case classes and automatically
# generate and append a companion object which contains the names of each field in the case class as a string.
# This can be used to do psuedo type-safe access of arbitrary Columns on a DataFrame in Spark.
#
# Eg. if a file contained
# ```
# case class AliasInfo(
#     alias: String,
#     mcc_restriction: Seq[Int],
#     regex_match: Boolean,
#     source: String,
#     brand_bounded: Boolean)
# ```
# The result would be:
#
# ```
# case class AliasInfo(
#     alias: String,
#     mcc_restriction: Seq[Int],
#     regex_match: Boolean,
#     source: String,
#     brand_bounded: Boolean)
#
#  object AliasInfo {
#     val alias: String = "alias",
#     val mcc_restriction: String = "mcc_restriction",
#     val regex_match: String = "regex_match,
#     val source: String = "source",
#     val brand_bounded: String = "brand_bounded")
# }
# ```
#
#  So far only the validation checks and regex match to find all files containing case classes have been written.
#  Next step is the code generation.


def parse_args():
    parser = argparse.ArgumentParser(description="""Generate companion objects for Scala case classes. The companion
                                                    objects shall have only String fields which are the names of the
                                                    fields themselves in order to enable type safe DataFrame access.""")
    parser.add_argument('--base-path',  '-p', required=True,    type=str, help='Path to the root of the repository.')
    parser.add_argument('--dry-run',    '-d', required=False,   type=bool, help="""Run generator and output the final result to an 
                                                                 adjacent directory rather than overwriting existing
                                                                 code""")
    parser.add_argument('--verbose',    '-v', required=False,   action='store_true')
    parser.add_argument('--unsafe',    '-u', required=False,   action='store_true')


    args = parser.parse_args()

    Params = namedtuple('Params', 'base_path dry_run verbose unsafe')

    return Params(base_path=args.base_path.rstrip('/') + '/',
                  dry_run=args.dry_run,
                  verbose=args.verbose,
                  unsafe=args.unsafe)


def validate_repo_exists(path: str) -> bool:
    """Peforms some sanity checks to ensure that we are not dumping code in a directory we shouldn't be"""

    directory_exists = os.path.isdir(path)
    source_controlled = os.path.exists(path + ".git")  # TODO add mercurial and svn

    files = os.listdir(path)
    build_files = ['build.sbt', 'build.scala', 'version.sbt', "pom.xml", 'gradle.properties', 'gradlew']
    has_build_files = any(f in build_files for f in files)

    return directory_exists and source_controlled and has_build_files


def get_all_scala_source_filepaths(path: str) -> List[str]:
    scala_source_paths = []

    for (dirpath, dirnames, filenames) in os.walk(path):
        for fname in filenames:
            if fname.endswith('.scala'):
                scala_source_paths.append(dirpath + '/' + fname)

    return scala_source_paths


def contains_case_class_by_substr(filepath: str) -> bool:
    with open(filepath) as f:
        return f.read().find('case class') > 0


def contains_case_class_by_regex(filepath: str) -> bool:
    whitespace = '[\s\r\n]*'
    scala_type = '[\w|\[\]]+'
    symbol = '[\w]+'

    argument_with_type = symbol + whitespace + ':' + whitespace + scala_type

    # regex pattern to match the appearance of a case class
    # Full pattern for regex testing:
    # case class[\s\r\n]*[\w|\[\]]+[\s\r\n]*\([\s\r\n]*[\w]+[\s\r\n]*:[\s\r\n]*[\w|\[\]]+[\s\r\n]*(,[\s\r\n]*[\w]+[\s\r\n]*:[\s\r\n]*[\w|\[\]]+[\s\r\n]*)*[\s\r\n]*\)
    pattern = 'case class' + whitespace + scala_type + whitespace + '\(' + \
              whitespace + argument_with_type + whitespace + \
              '(,' + whitespace + argument_with_type + whitespace + ')*' + whitespace + \
              '\)'

    regex = re.compile(pattern)

    with open(filepath) as f:
        return regex.search(f.read()) is not None


if __name__ == "__main__":
    args = parse_args()

    repo_exists = validate_repo_exists(args.base_path)

    if not (args.unsafe or repo_exists):
        raise FileNotFoundError("""The directory you selected either does not exist, is not a git repo, or does not 
        contain build files at the top level which would indicate it is a Scala project. Use --unsafe to ignore this
        error if that is ok.""")
    else:
        source_paths = get_all_scala_source_filepaths(args.base_path)
        likely_case_class_paths = filter(lambda path: contains_case_class_by_substr(path), source_paths)
        # the case class could be mentioned in a comment, lets be really sure its source code

        case_class_paths = filter(lambda path: contains_case_class_by_regex(path), likely_case_class_paths)

        for path in case_class_paths:
            print(path)


def test_regex() -> bool:
    testString = """case class AliasInfo(
    alias: String,
    mcc_restriction: Seq[Int],
    regex_match: Boolean,
    source: String,
    brand_bounded: Boolean)"""

    # Should print 'True'
    print(contains_case_class_by_regex(testString))
