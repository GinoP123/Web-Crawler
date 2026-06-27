#!/bin/zsh

cd $(dirname "$0")

resize -s 60 44

if [[ $(ps -a | grep .ipynb | grep -v grep) == '' ]]; then
	winID="$(osascript -e 'id of window 1 of app "Terminal"')"
	ttab jupyter notebook $(realpath ./crawler.ipynb)
	osascript <<EOS
tell app "Terminal"
    set frontmost of windows whose id = $winID to true
    activate
end tell
EOS
fi

python3 ./_shell.py
