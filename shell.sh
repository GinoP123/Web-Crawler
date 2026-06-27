#!/bin/zsh

resize -s 60 44

if [[ $(ps -a | grep .ipynb | grep -v grep) == '' ]]; then
	winID="$(osascript -e 'id of window 1 of app "Terminal"')"
	/Users/ginoprasad/Scripts/FileSearch/open /Users/ginoprasad/Job_Applications/web_crawler/web_logger.ipynb
	osascript <<EOS
tell app "Terminal"
    set frontmost of windows whose id = $winID to true
    activate
end tell
EOS
fi

/Users/ginoprasad/Job_Applications/web_crawler/_shell.py
