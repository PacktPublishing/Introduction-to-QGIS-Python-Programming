RESOURCE_FILES = resources.py

default: compile

compile: $(RESOURCE_FILES)

%.py : %.qrc
	export PATH="/Applications/QGIS.app/Contents/MacOS/bin:$PATH"; export PYTHONPATH="/Applications/QGIS.app/Contents/Resources/python"; pyrcc4 -o $@ $<

%.py : %.ui
	export PATH="/Applications/QGIS.app/Contents/MacOS/bin:$PATH"; export PYTHONPATH="/Applications/QGIS.app/Contents/Resources/python"; pyuic4 -o $@ $<

clean:
	rm $(RESOURCE_FILES)
	rm *.pyc



