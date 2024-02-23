clearlog:
	truncate -s 0 my_log_file.log

lint: clearlog
	black -v .

icons: lint
	{ \
		for X in 16 32 48 64 96 128 192 256; do \
			mkdir -vp $(HOME)/.icons/hicolor/$${X}x$${X}/apps; \
			mkdir -vp $(HOME)/.local/share/icons/hicolor/$${X}x$${X}/apps; \
			cp -f $$(pwd)/images/dfakeseeder.png $(HOME)/.local/share/icons/hicolor/$${X}x$${X}/apps/; \
			rm -f $(HOME)/.local/share/icons/hicolor/$${X}x$${X}/dfakeseeder.png; \
			cp -f $$(pwd)/images/dfakeseeder.png $(HOME)/.icons/hicolor/$${X}x$${X}/apps/; \
			rm -f $(HOME)/.icons/hicolor/$${X}x$${X}/dfakeseeder.png; \
		done; \
	}
	{ \
		cd $(HOME)/.local/share/icons/ && \
		gtk-update-icon-cache -t -f hicolor; \
		cd $(HOME)/.icons/ && \
		gtk-update-icon-cache -t -f hicolor; \
	}

ui-build: icons
	echo "Building UI..."
	xmllint --xinclude ui/ui.xml > ui/generated.xml
	sed -i 's/xml:base="[^"]*"//g' ui/generated.xml

run: ui-build
	-ln -s $$(pwd)/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-ps aux | grep "dfakeseeder.py" | awk '{print $$2}' | xargs kill -9
	echo "Running program..."
	gtk-launch dfakeseeder &

run-debug: ui-build
	-ln -s $$(pwd)/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-ps aux | grep "dfakeseeder.py" | awk '{print $$2}' | xargs kill -9
	echo "Running program..."
	LOG_LEVEL=INFO /usr/bin/python3 dfakeseeder.py

valgrind: ui-build
	-ln -s $$(pwd)/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-ps aux | grep "dfakeseeder.py" | awk '{print $$2}' | xargs kill -9
	echo "Running program..."
	valgrind --tool=memcheck --leak-check=full /usr/bin/python3 dfakeseeder.py

preferences:
	echo "Running program..."
	python3 preferences.py

xprod-wmclass:
	xprop WM_CLASS