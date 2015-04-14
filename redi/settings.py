import ConfigParser
import io


class SettingsParser(object):
    def __init__(self):
        self.__settings = {}

    def add_setting(self, name, **kwargs):
        self.__settings[name] = Setting(name, **kwargs)

    def parse(self, stream):
        parser = ConfigParser.ConfigParser()
        try:
            parser.readfp(stream)
        except ConfigParser.MissingSectionHeaderError:
            default_section = "[%s]\n" % ConfigParser.DEFAULTSECT
            stream.seek(0)
            parser.readfp(io.BytesIO(default_section + stream.read()))

        return Settings(self.__settings, parser)


class Settings(object):
    def __init__(self, settings, parser):
        self.__settings = settings
        self.__parser = parser

        for name, setting in settings.iteritems():
            if not setting.required:
                continue
            try:
                parser.get(ConfigParser.DEFAULTSECT, name)
            except ConfigParser.NoOptionError:
                raise MissingRequiredSettingError()

        for setting in settings.itervalues():
            try:
                self[setting.name]
            except ValueError:
                raise TypeError()

    def __getitem__(self, item):
        setting = self.__settings[item]
        return setting.get(self.__parser.get(ConfigParser.DEFAULTSECT, item))


class Setting(object):
    def __init__(self, name, **kwargs):
        self.__name = name
        self.__required = bool(kwargs.get('required', False))
        self.__type = kwargs.get('type', str)

    @property
    def name(self):
        return self.__name

    @property
    def required(self):
        return self.__required

    def get(self, value):
        return self.__type(value)


class MissingRequiredSettingError(Exception):
    pass


class TypeError(Exception):
    pass