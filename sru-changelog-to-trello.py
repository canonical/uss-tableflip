#!/usr/bin/env python
"""Parse a changelog into trello checklist markdown for SRUs."""

import argparse
import re


def get_parser():
   parser = argparse.ArgumentParser()
   parser.add_argument('-c', '--changelog', required=True, help='Changelog file to parser')
   return parser


def main():
  parser = get_parser()
  args = parser.parse_args()
  with open(args.changelog, 'rb') as stream:
    content = stream.read()

  section_marker = 'cloud-init ('
  section_count = 0
  for item in content.split('- '):
    if section_marker in item:
        section_count += 1
        if section_count > 1:
            break
        continue
    # strip all whitespace/newlines
    changelog_item = ' '.join(item.split())
    m = re.match(r'.*\(LP: #(?P<bugs>[\d ,#]+)\).*', changelog_item)
    if m:
        bugnums = m.group('bugs').split(', #')
        bug_prefix = ''.join([
            '[LP: #{bug}](http://pad.lv/{bug}) '.format(bug=bugnum)
            for bugnum in bugnums])
        # Strip bug details from end and put it as markdown in prefix
        summary = re.sub(r'\(LP:[^)]+\)', '', changelog_item)
        print(' - {0} {1}'.format(bug_prefix, summary))

if __name__ == '__main__':
    main()
