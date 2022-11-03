from sxm_tmk.core.conda.cache import CondaCache, PackageCacheExtractor
from sxm_tmk.core.custom_types import Packages
from sxm_tmk.core.dependency import Package, PinnedPackage


def test_cache_extractor_without_conditions(cache_with_numpy, numpy_package):
    a_cache = CondaCache(cache_dir=cache_with_numpy)
    pkg_extractor = PackageCacheExtractor(a_cache)

    assert len(pkg_extractor.extract_packages(numpy_package, [])) == 92


def test_cache_extractor_one_condition(cache_with_numpy, numpy_package):
    a_cache = CondaCache(cache_dir=cache_with_numpy)
    conditions: Packages = [Package(name="python", version="3.8.9", build_number=None, build=None)]
    pkg_extractor = PackageCacheExtractor(a_cache)
    assert len(pkg_extractor.extract_packages(numpy_package, conditions)) == 37


def test_cache_extractor_two_conditions(cache_with_numpy, numpy_package):
    a_cache = CondaCache(cache_dir=cache_with_numpy)
    conditions: Packages = [
        Package(name="python", version="3.8.9", build_number=None, build=None),
        Package(name="libcxx", version="11.8.2", build_number=None, build=None),
    ]
    pkg_extractor = PackageCacheExtractor(a_cache)
    assert len(pkg_extractor.extract_packages(numpy_package, conditions)) == 26


def test_cache_extractor_two_conditions_version_restrict_hard(cache_with_numpy, numpy_package):
    a_cache = CondaCache(cache_dir=cache_with_numpy)
    pkg_extractor = PackageCacheExtractor(a_cache)
    conditions: Packages = [
        Package(name="python", version="3.8.9", build_number=None, build=None),
        Package(name="libcxx", version="11.8.2", build_number=None, build=None),
    ]

    numpy_package.version = "1.19.5"
    numpy_1_19_5: Packages = [
        Package(name="numpy", version="1.19.5", build_number=3, build="py38he594345_3"),
        Package(name="numpy", version="1.19.5", build_number=2, build="py38hbf7bb01_2"),
        Package(name="numpy", version="1.19.5", build_number=1, build="py38h9e6c65a_1"),
        Package(name="numpy", version="1.19.5", build_number=1, build="py38hbf7bb01_1"),
        Package(name="numpy", version="1.19.5", build_number=0, build="py38h9e6c65a_0"),
    ]

    assert numpy_1_19_5 == pkg_extractor.extract_packages(numpy_package, conditions)


def test_cache_extractor_two_conditions_version_restrict(cache_with_numpy, numpy_package):
    a_cache = CondaCache(cache_dir=cache_with_numpy)
    pkg_extractor = PackageCacheExtractor(a_cache)
    conditions: Packages = [
        Package(name="python", version="3.8.9", build_number=None, build=None),
        Package(name="libcxx", version="11.8.2", build_number=None, build=None),
    ]

    pin_numpy_at_1_19_5 = PinnedPackage.from_specifier(numpy_package.name, "1.19.5", "==1.19.5")
    numpy_1_19_5: Packages = [
        Package(name="numpy", version="1.19.5", build_number=3, build="py38he594345_3"),
        Package(name="numpy", version="1.19.5", build_number=2, build="py38hbf7bb01_2"),
        Package(name="numpy", version="1.19.5", build_number=1, build="py38h9e6c65a_1"),
        Package(name="numpy", version="1.19.5", build_number=1, build="py38hbf7bb01_1"),
        Package(name="numpy", version="1.19.5", build_number=0, build="py38h9e6c65a_0"),
    ]

    assert numpy_1_19_5 == pkg_extractor.extract_pinned_packages(pin_numpy_at_1_19_5, conditions)


def test_cache_extractor_unknown_package(tmp_path, numpy_package):
    a_cache = CondaCache(cache_dir=tmp_path)
    pkg_extractor = PackageCacheExtractor(a_cache)
    numpy_pin_at_1_19_5 = PinnedPackage.from_specifier(numpy_package.name, "1.19.5", "==1.19.5")

    assert not pkg_extractor.extract_pinned_packages(numpy_pin_at_1_19_5, [])
    assert not pkg_extractor.extract_packages(numpy_package, [])
