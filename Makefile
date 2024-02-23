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

run: ui-build
	-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-ps aux | grep "dfakeseeder.py" | awk '{print $$2}' | xargs kill -9
	echo "Running program..."
	{ \
		cd d_fake_seeder && \
		gtk-launch dfakeseeder &; \
	}

run-debug: ui-build
	-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-ps aux | grep "dfakeseeder.py" | awk '{print $$2}' | xargs kill -9
	echo "Running program..."
	{ \
		cd d_fake_seeder && \
		LOG_LEVEL=INFO /usr/bin/python3 dfakeseeder.py; \
	}

valgrind: ui-build
	-ln -s $$(pwd)/d_fake_seeder/dfakeseeder.desktop ~/.local/share/applications/dfakeseeder.desktop 2>/dev/null
	-ps aux | grep "dfakeseeder.py" | awk '{print $$2}' | xargs kill -9
	echo "Running program..."
	{ \
		cd d_fake_seeder && \
		valgrind --tool=memcheck --leak-check=full /usr/bin/python3 dfakeseeder.py; \
	}

xprod-wmclass:
	xprop WM_CLASS

rpm:
	sudo dnf install -y rpm-build rpmlint python3-setuptools
	rm -rvf ./rpmbuild
	mkdir -vp ./rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
	cp -r dfakeseeder.spec ./rpmbuild/SPECS
	cp -r config ./rpmbuild/SOURCE
	cp -r d_fake_seeder/images ./rpmbuild/SOURCE
	cp -r d_fake_seeder/lib ./rpmbuild/SOURCE
	cp -r d_fake_seeder/ui ./rpmbuild/SOURCE
	cp -r d_fake_seeder/dfakeseeder.py ./rpmbuild/SOURCE
	cp -r d_fake_seeder/dfakeseeder.desktop ./rpmbuild/SOURCE
	rpmbuild -ba ~/rpmbuild/SPECS/dfakeseeder.spec
	# sudo dnf install ~/rpmbuild/RPMS/<architecture>/python-example-1.0-1.<architecture>.rpm
	# rpmlint

deb:
	sudo apt-get install dpkg dpkg-dev fakeroot
	rm -rvf ./debbuild
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
	#sudo dpkg -i debbuild.deb

docker:
	docker build -t dfakeseeder .
	docker run --rm -it --net=host --env="DISPLAY" --volume="$$HOME/.Xauthority:/root/.Xauthority:rw" dfakeseeder
