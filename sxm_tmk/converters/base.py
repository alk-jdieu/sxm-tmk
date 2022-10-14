from sxm_tmk.core.dependency import PinnedPackage


class Base:
    def __init__(self):
        self.__ssl = {"1.1": PinnedPackage.from_specifier("openssl", None, "<1.2.1a")}

    def get_openssl_profile(self) -> PinnedPackage:
        return self.__ssl["1.1"]
