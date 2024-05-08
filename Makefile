deb_package_name := $(shell cat control | grep Package | sed 's/Package: //')
rpm_package_name := $(shell cat dfakeseeder.spec | grep Name | cut -d: -f 2 | tr -d ' ')
package_version := $(shell cat control | grep Version | sed 's/Version: //')
DEB_FILENAME := $(deb_package_name)_$(package_version).deb
RPM_FILENAME := $(rpm_package_name)-$(package_version)

required:
	pip3 install -r requirements.txt


clearlog: required
	truncate -s 0 d_fake_seeder/log.log

lint: clearlog
	echo "Running lint commands..."
	black -v --line-length=90 .
	flake8 --max-line-length=90
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

translatepy:
	xgettext --verbose --language=Python --keyword=_ --output=d_fake_seeder/locale/dfakeseederpy.pot d_fake_seeder/dfakeseeder.py
	#msginit --no-translator --output-file=d_fake_seeder/locale/en_US/LC_MESSAGES/en_USpy.po --input=d_fake_seeder/locale/dfakeseederpy.pot --locale=en_US
	#msgfmt --output-file=d_fake_seeder/locale/en_US/LC_MESSAGES/dfakeseederpy.mo d_fake_seeder/locale/en_US/LC_MESSAGES/en_USpy.po

translatexml:
	xgettext --keyword=translatable --language=Glade --from-code=UTF-8 --output=d_fake_seeder/locale/dfakeseederxml.pot d_fake_seeder/ui/generated.xml
	msginit --no-translator --output-file=d_fake_seeder/locale/en_US/LC_MESSAGES/en_USxml.po --input=d_fake_seeder/locale/dfakeseederxml.pot --locale=en_US
	msgfmt --output-file=d_fake_seeder/locale/en_US/LC_MESSAGES/dfakeseederxml.mo d_fake_seeder/locale/en_US/LC_MESSAGES/en_USxml.po

translate:
	rm -rvf d_fake_seeder/locale/
	mkdir -vp locale/en_US/LC_MESSAGES/
	mkdir -vp d_fake_seeder/locale/en_US/LC_MESSAGES/
	$(MAKE) translatepy
	#$(MAKE) translatexml

test:
	DFS_PATH=$$(pwd)/d_fake_seeder pytest -vvv tests/

flatpak: clean
	flatpak-builder build-dir ie.fio.dfakeseeder manifest.json