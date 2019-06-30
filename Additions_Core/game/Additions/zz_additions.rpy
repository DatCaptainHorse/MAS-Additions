# This file handles all things MAS additions
# Yes, I know string comparisons are bad. I barely use Python, I dont know how to do things "correctly" until I learn more.
# This system should be replaced by a proper Submod API ASAP.

init python:
    import os
    from ConfigParser import SafeConfigParser

    parser = SafeConfigParser()

    additions = [] # For additions settings menu
    
    additionsPath = "Additions/additions.ini"

    # Registers a MAS addition
    #	@param idTag - additions "tag", used to identify, compare dependencies and such. Should not be changed once chosen!
    #   @param additionName - additions name, just a visual niceyness
    #   @param additionVersion - additions version
    def registerAddition(idTag, additionName, additionVersion):
        foundInifile = False
        for dirpath,subdirs,files in os.walk('.'):
            for name in files:
                if name == 'additions.ini':
                    foundInifile = True
                    break

        if not foundInifile: # Dirty, but works
            for dirpath,subdirs,files in os.walk('.'):
                if dirpath == 'game':
                    creator = open(os.path.join(dirpath, additionsPath), 'w')
                    creator.close()
                    break

        parser.read(renpy.loader.transfn(additionsPath))

        if parser.has_section(idTag):
            if not idTag in additions:
                additions.append((idTag, additionName, additionVersion))
        else:
            parser.add_section(idTag)
            parser.set(idTag, 'ver', additionVersion)
            parser.set(idTag, 'name', additionName)
            parser.set(idTag, 'enabled', 'true')
            parser.set(idTag, 'first', 'true')

            with open(renpy.loader.transfn(additionsPath), 'w') as additionconfig:
                parser.write(additionconfig)

            if not idTag in additions:
                additions.append((idTag, additionName, additionVersion))

    # Enables addition
    def enableAddition(idTag):
        parser.read(renpy.loader.transfn(additionsPath))
        if parser.has_section(idTag):
            parser.set(idTag, 'enabled', 'true')
            parser.set(idTag, 'first', 'true') # Assume addition reload or something
            with open(renpy.loader.transfn(additionsPath), 'w') as additionconfig:
                parser.write(additionconfig)

    # Disables addition
    def disableAddition(idTag):
        parser.read(renpy.loader.transfn(additionsPath))
        if parser.has_section(idTag):
            parser.set(idTag, 'enabled', 'false')
            with open(renpy.loader.transfn(additionsPath), 'w') as additionconfig:
                parser.write(additionconfig)

    # Returns true if addition with the tag is enabled
    # or false if it is disabled or does not exist
    def additionIsEnabled(idTag):
        parser.read(renpy.loader.transfn(additionsPath))
        if parser.has_section(idTag):
            return parser.getboolean(idTag, 'enabled')
        else:
            return False

    # Returns true if the additions is being run the first time since enabling it
    def isAdditionFirstRun(idTag):
        parser.read(renpy.loader.transfn(additionsPath))
        if parser.has_section(idTag):
            result = parser.getboolean(idTag, 'first')
            if result is True:
                parser.set(idTag, 'first', 'false')
                with open(renpy.loader.transfn(additionsPath), 'w') as additionconfig:
                    parser.write(additionconfig)
                return True
            else:
                return False
        else:
            return False