class Browser:
    @staticmethod
    def __init__(platform, browser):
        return [platform, browser, ""]

    @staticmethod
    def macOS(browser):
        return ["macos", browser, ""]

    @staticmethod
    def windows(browser):
        return ["windows", browser, ""]

    @staticmethod
    def ubuntu(browser):
        return ["ubuntu", browser, ""]