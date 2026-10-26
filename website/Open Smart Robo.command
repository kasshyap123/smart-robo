#!/bin/zsh
# Double-click this file in Finder to view the local Smart Robo website.
cd -- "${0:A:h}" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  print 'Python 3 is required to open the local website.'
  print 'You can use Open Live Website.webloc instead.'
  read '?Press Return to close.'
  exit 1
fi
python3 scripts/local-preview.py
if [[ $? -ne 0 ]]; then
  print '\nThe local website could not start. Read the message above.'
  read '?Press Return to close.'
fi
