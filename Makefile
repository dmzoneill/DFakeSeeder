clearlog:
	truncate -s 0 d_fake_seeder/log.log

lint: clearlog
	black -v .

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
	jq '.torrents = {}' d_fake_seeder/config/settings.json > temp.json && mv temp.json d_fake_seeder/config/settings.json

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

rpm:
	- sudo dnf install -y rpm-build rpmlint python3-setuptools
	- sudo apt install -y rpm rpmlint python3-setuptools
	rm -rvf ./rpmbuild
	mkdir -p ./rpmbuild/BUILD ./rpmbuild/BUILDROOT ./rpmbuild/RPMS ./rpmbuild/SOURCES ./rpmbuild/SPECS ./rpmbuild/SRPMS
	cp -r dfakeseeder.spec ./rpmbuild/SPECS/
	cp -r d_fake_seeder/images ./rpmbuild/SOURCE/
	cp -r d_fake_seeder/lib ./rpmbuild/SOURCE/
	cp -r d_fake_seeder/ui ./rpmbuild/SOURCE/
	cp -r d_fake_seeder/dfakeseeder.py ./rpmbuild/SOURCE/
	cp -r d_fake_seeder/dfakeseeder.desktop ./rpmbuild/SOURCE/
	tar -czvf rpmbuild/SOURCES/DFakeSeeder-1.0.tar.gz d_fake_seeder/ 
	rpmbuild -ba rpmbuild/SPECS/dfakeseeder.spec

rpm-install: rpm
	sudo dnf install rpmbuild/RPMS/<architecture>/python-example-1.0-1.<architecture>.rpm
	rpmlint

deb:
	sudo apt-get install dpkg dpkg-dev fakeroot
	sudo rm -rvf ./debbuild
	mkdir -vp ./debbuild/DEBIAN
	cp control ./debbuild/DEBIAN
	mkdir -vp ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/config ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/images ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/lib ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/ui ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/dfakeseeder.py ./debbuild/opt/dfakeseeder
	cp -r d_fake_seeder/dfakeseeder.desktop ./debbuild/opt/dfakeseeder
	sudo chown -R root:root debbuild
	fakeroot dpkg-deb --build debbuild
	dpkg -c debbuild.deb
	dpkg -I debbuild.deb

deb-install: deb	
	sudo dpkg -i debbuild.deb

docker:
	docker build -t dfakeseeder .
	docker run --rm -it --net=host --env="DISPLAY" --volume="$$HOME/.Xauthority:/root/.Xauthority:rw" dfakeseeder

clean:
	sudo rm -rvf debbuild
	sudo rm -rvf rpmbuild
	sudo rm -rvf *.deb
	sudo rm -rvf *.rpm
	$(MAKE) lint

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