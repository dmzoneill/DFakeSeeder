deb_package_name := $(shell cat control | grep Package | sed 's/Package: //')
rpm_package_name := $(shell cat dfakeseeder.spec | grep Name | cut -d: -f 2 | tr -d ' ')
package_version := $(shell cat control | grep Version | sed 's/Version: //')
DEB_FILENAME := $(deb_package_name)_$(package_version).deb
RPM_FILENAME := $(rpm_package_name)-$(package_version)

required:
ifdef CI
	pip3 install -r requirements.txt
else
	pip3 install -r requirements.txt --break-system-packages
endif


clearlog: required
	truncate -s 0 d_fake_seeder/log.log

lint: clearlog
	echo "Running lint commands..."
	black -v --line-length=120 .
	flake8 --max-line-length=120
	find . -iname "*.py" -exec isort --profile=black --df {} \;

icons: lint
	{ \
		for X in 16 32 48 64 96 128 192 256; do \
			mkdir -vp $(HOME)/.icons/hicolor/$${X}x$${X}/apps; \
			mkdir -vp $(HOME)/.local/share/icons/hicolor/$${X}x$${X}/apps; \
			cp -f $$(pwd)/d_fake_seeder/images/dfakeseeder.png $(HOME)/.local/share/icons/hicolor/$${X}x$${X}/apps/; \
			cp -f $$(pwd)/d_fake_seeder/images/dfakeseeder.png $(HOME)/.icons/hicolor/$${X}x$${X}/apps/; \
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
	xmllint --xinclude d_fake_seeder/ui/ui.xml > d_fake_seeder/ui/generated.xml
	sed -i 's/xml:base="[^"]*"//g' d_fake_seeder/ui/generated.xml

clean_settings:
	jq '.torrents = {}' ~/.config/dfakeseeder/settings.json > temp.json && mv temp.json ~/.config/dfakeseeder/settings.json

run: ui-build
	-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-ps aux | grep "dfakeseeder.py" | awk '{print $$2}' | xargs kill -9
	echo "Running program..."
	{ \
		cd d_fake_seeder && \
		gtk-launch dfakeseeder; \
	}
	$(MAKE) clean_settings;

run-debug: ui-build
	-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-ps aux | grep "dfakeseeder.py" | awk '{print $$2}' | xargs kill -9
	echo "Running program..."
	{ \
		cd d_fake_seeder && \
		LOG_LEVEL=INFO DFS_PATH=$$(pwd) /usr/bin/python3 dfakeseeder.py; \
	}
	$(MAKE) clean_settings;

run-debug-docker: ui-build
	-docker build \
		--build-arg USER_ID=$$(id -u) \
		--build-arg GROUP_ID=$$(id -g) \
		-t dfakeseeder .

	-docker ps -a -q --filter "name=dfakeseeder" | xargs -r docker rm -f

	xhost +local:root
	-docker run --privileged -it --rm \
	    --name dfakeseeder \
	    -e LOG_LEVEL=INFO \
	    -e DFS_PATH=/app \
	    -e DISPLAY=$$DISPLAY \
	    -v $$HOME/.config/dfakeseeder:/home/dfakeseeder/.config/dfakeseeder \
		-v $$HOME/Downloads:/home/dfakeseeder/Downloads \
	    -v $$(pwd):/app \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
	    dfakeseeder
	xhost -local:root

	$(MAKE) clean_settings;

clean:
	- sudo rm -rvf log.log
	- sudo rm -rvf d_fake_seeder/log.log
	- sudo rm -rvf dist
	- sudo rm -rvf .pytest_cache
	- sudo find . -type d -iname __pycache__ -exec rm -rf {} \;
	- sudo rm -rvf debbuild
	- sudo rm -rvf rpmbuild
	- sudo rm -rvf *.deb
	- sudo rm -rvf *.rpm
	- sudo rm -rvf tools/translations/*.backup
	- sudo rm -rvf tools/translations/*_fallbacks_to_translate.json
	$(MAKE) lint

valgrind: ui-build
	-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-ps aux | grep "dfakeseeder.py" | awk '{print $$2}' | xargs kill -9
	echo "Running program..."
	{ \
		cd d_fake_seeder && \
		valgrind --tool=memcheck --leak-check=full /usr/bin/python3 dfakeseeder.py; \
	}
	$(MAKE) clean_settings;

xprod-wmclass:
	xprop WM_CLASS

rpm: clean
    
	- sudo dnf install -y rpm-build rpmlint python3-setuptools python3-setuptools
	rm -rvf ./rpmbuild
	mkdir -p ./rpmbuild/BUILD ./rpmbuild/BUILDROOT ./rpmbuild/RPMS ./rpmbuild/SOURCES ./rpmbuild/SPECS ./rpmbuild/SRPMS
	cp -r dfakeseeder.spec ./rpmbuild/SPECS/
	cp -r d_fake_seeder/images ./rpmbuild/SOURCE/
	cp -r d_fake_seeder/lib ./rpmbuild/SOURCE/
	cp -r d_fake_seeder/ui ./rpmbuild/SOURCE/
	cp -r d_fake_seeder/dfakeseeder.py ./rpmbuild/SOURCE/
	cp -r d_fake_seeder/dfakeseeder.desktop ./rpmbuild/SOURCE/
	tar -czvf rpmbuild/SOURCES/$(RPM_FILENAME).tar.gz d_fake_seeder/ 
	rpmbuild --define "_topdir `pwd`/rpmbuild" -v -ba ./rpmbuild/SPECS/dfakeseeder.spec

rpm-install: rpm
	sudo dnf install rpmbuild/RPMS/<architecture>/python-example-1.0-1.<architecture>.rpm
	rpmlint

deb: clean
	sudo apt-get install dpkg dpkg-dev fakeroot
	sudo rm -rvf ./debbuild
	mkdir -vp ./debbuild/DEBIAN
	cp control ./debbuild/DEBIAN
	mkdir -vp ./debbuild/opt/dfakeseeder
	mkdir -vp ./debbuild/usr/share/applications/
	cp -r d_fake_seeder/dfakeseeder.desktop ./debbuild/usr/share/applications/
	cp -r d_fake_seeder/config ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/images ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/lib ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/ui ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/dfakeseeder.py ./debbuild/opt/dfakeseeder
	sed 's#dfakeseeder.py#/opt/dfakeseeder/dfakeseeder.py#g' -i ./debbuild/usr/share/applications/dfakeseeder.desktop
	touch ./debbuild/DEBIAN/postinst

	echo "#!/bin/bash -x" >> ./debbuild/DEBIAN/postinst
	echo "for X in 16 32 48 64 96 128 192 256; do " >> ./debbuild/DEBIAN/postinst
	echo "mkdir -vp \$$HOME/.icons/hicolor/\$${X}x\$${X}/apps " >> ./debbuild/DEBIAN/postinst
	echo "mkdir -vp \$$HOME/.local/share/icons/hicolor/\$${X}x\$${X}/apps " >> ./debbuild/DEBIAN/postinst
	echo "cp -f /opt/dfakeseeder/d_fake_seeder/images/dfakeseeder.png \$$HOME/.local/share/icons/hicolor/\$${X}x\$${X}/apps/ " >> ./debbuild/DEBIAN/postinst
	echo "cp -f /opt/dfakeseeder/d_fake_seeder/images/dfakeseeder.png \$$HOME/.icons/hicolor/\$${X}x\$${X}/apps/ " >> ./debbuild/DEBIAN/postinst
	echo "done " >> ./debbuild/DEBIAN/postinst
	echo "cd \$$HOME/.local/share/icons/ && \\" >> ./debbuild/DEBIAN/postinst
	echo "gtk-update-icon-cache -t -f hicolor; \\" >> ./debbuild/DEBIAN/postinst
	echo "cd \$$HOME/.icons/ && \\" >> ./debbuild/DEBIAN/postinst
	echo "gtk-update-icon-cache -t -f hicolor; " >> ./debbuild/DEBIAN/postinst
	chmod 755 ./debbuild/DEBIAN/postinst

	sudo chown -R root:root debbuild
	fakeroot dpkg-deb --build debbuild $(DEB_FILENAME)

	dpkg -c $(DEB_FILENAME)
	dpkg -I $(DEB_FILENAME)

deb-install: deb	
	sudo dpkg -i $(DEB_FILENAME)

xhosts:
	xhost +local:

docker: xhosts
	docker build -t dfakeseeder .
	docker run --rm --net=host --env="DISPLAY" --volume="\$$HOME/.Xauthority:/root/.Xauthority:rw" --volume="/tmp/.X11-unix:/tmp/.X11-unix" -it dfakeseeder

docker-hub: xhosts
	docker run --rm --net=host --env="DISPLAY" --volume="\$$HOME/.Xauthority:/root/.Xauthority:rw" --volume="/tmp/.X11-unix:/tmp/.X11-unix" -it feeditout/dfakeseeder

docker-ghcr: xhosts
	docker run --rm --net=host --env="DISPLAY" --volume="\$$HOME/.Xauthority:/root/.Xauthority:rw" --volume="/tmp/.X11-unix:/tmp/.X11-unix" -it ghcr.io/dfakeseeder

# Translation management using tools/translation_build_manager.py
translate-build:
	echo "Building translations using translation manager..."
	python3 tools/translation_build_manager.py --build

translate-extract:
	echo "Extracting translatable strings..."
	python3 tools/translation_build_manager.py --extract

translate-clean:
	echo "Cleaning translation files..."
	python3 tools/translation_build_manager.py --clean

# Tray application targets
run-tray: ui-build
	echo "Running tray application only..."
	{ \
		cd d_fake_seeder && \
		LOG_LEVEL=INFO DFS_PATH=$$(pwd) /usr/bin/python3 dfakeseeder_tray.py; \
	}

run-tray-debug: ui-build
	echo "Running tray application with debug output..."
	{ \
		cd d_fake_seeder && \
		LOG_LEVEL=DEBUG DFS_PATH=$$(pwd) /usr/bin/python3 dfakeseeder_tray.py; \
	}

run-with-tray: ui-build
	echo "Running main application with tray (backgrounded)..."
	-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-ps aux | grep "dfakeseeder.py\|dfakeseeder_tray.py" | awk '{print $$2}' | xargs kill -9
	{ \
		cd d_fake_seeder && \
		LOG_LEVEL=INFO DFS_PATH=$$(pwd) /usr/bin/python3 dfakeseeder.py & \
		sleep 3 && \
		LOG_LEVEL=INFO DFS_PATH=$$(pwd) /usr/bin/python3 dfakeseeder_tray.py; \
	}
	$(MAKE) clean_settings;

run-debug-with-tray: ui-build
	echo "Running main application with tray (debug mode)..."
	-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-ps aux | grep "dfakeseeder.py\|dfakeseeder_tray.py" | awk '{print $$2}' | xargs kill -9
	{ \
		cd d_fake_seeder && \
		LOG_LEVEL=DEBUG DFS_PATH=$$(pwd) /usr/bin/python3 dfakeseeder.py & \
		sleep 5 && \
		LOG_LEVEL=DEBUG DFS_PATH=$$(pwd) /usr/bin/python3 dfakeseeder_tray.py; \
	}
	$(MAKE) clean_settings;

test:
	DFS_PATH=$$(pwd)/d_fake_seeder cd d_fake_seeder/ && pytest -vvv .

test-docker:
	-docker build \
		--build-arg USER_ID=$$(id -u) \
		--build-arg GROUP_ID=$$(id -g) \
		-t dfakeseeder .

	-docker ps -a -q --filter "name=dfakeseeder" | xargs -r docker rm -f

	-docker run --privileged -it --rm \
	    --name dfakeseeder \
	    -e LOG_LEVEL=INFO \
	    -e DFS_PATH=/app \
	    -e DISPLAY=$$DISPLAY \
		-e PYTHONPATH=/app/d_fake_seeder/ \
	    -v $$HOME/.config/dfakeseeder:/home/dfakeseeder/.config/dfakeseeder \
		-v $$HOME/Downloads:/home/dfakeseeder/Downloads \
	    -v $$(pwd):/app \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
	    dfakeseeder \
	    pytest -s -x -vvv .

flatpak: clean
	flatpak-builder build-dir ie.fio.dfakeseeder manifest.json