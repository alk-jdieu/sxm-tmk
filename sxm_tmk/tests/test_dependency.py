import pytest

from sxm_tmk.core.dependency import (
    BrokenVersionSpecifier,
    Constraint,
    InvalidConstraintSpecification,
    InvalidVersion,
    NotComparablePackage,
    Package,
    PinnedPackage,
    clean_version,
)


@pytest.mark.parametrize(
    ("specifier", "version"),
    [
        ("==1.0.1", "1.0.0"),
        (">=1.0.0", "0.9.0"),
        (">1.0.0", "1.0.0"),
        (">1.0.0", "0.9.0"),
        ("<=1.0.0", "1.0.1"),
        ("<1.0.0", "1.0.0"),
        ("<1.0.0", "1.0.1"),
    ],
)
def test_pinned_package_broken_specifiers(specifier, version):
    match_str = f'Broken specifier: version "{version}" does not fulfil specifier "{specifier}" contract.'
    with pytest.raises(BrokenVersionSpecifier, match=match_str):
        PinnedPackage.make("thing", version=version, specifier=specifier)


@pytest.mark.parametrize(
    ("specifier", "version"),
    [
        ("==1.0.0", "1.0.0"),
        (">=1.0.0", "1.0.0"),
        (">=1.0.0", "1.0.1"),
        (">1.0.0", "1.0.1"),
        ("<=1.0.0", "1.0.0"),
        ("<=1.0.0", "0.9.0"),
        ("<1.0.0", "0.9.0"),
    ],
)
def test_pinned_package(specifier, version):
    PinnedPackage.make("thing", version=version, specifier=specifier)


def test_invalid_dependency_raises_when_parsing_version():
    pkg = Package(name="test", version="invalid.version", build_number=None, build=None)
    with pytest.raises(InvalidVersion, match='Version "invalid.version" is invalid'):
        pkg.parse_version()


def test_cannot_make_compare_key_on_package():
    with pytest.raises(
        NotComparablePackage, match='Package "test" cannot be compared to another package: no version information found'
    ):
        Package("test", version=None, build_number=None, build=None).compare_key()


def test_invalid_constraint():
    with pytest.raises(InvalidConstraintSpecification, match='Specifier "1.2.3" is invalid.'):
        Constraint("test", "1.2.3")


@pytest.mark.parametrize(
    ("version", "result"),
    [
        (">=1.2.3", "1.2.3"),
        (">=1.2.3e", "1.2.3.5"),
        ("<=1.2.3", "1.2.3"),
        ("<=1.2.3e", "1.2.3.5"),
        ("==1.2.3", "1.2.3"),
        ("==1.2.3e", "1.2.3.5"),
        ("!=1.2.3", "1.2.3"),
        ("!=1.2.3e", "1.2.3.5"),
        ("~=1.2.3", "1.2.3"),
        ("~=1.2.3e", "1.2.3.5"),
        (">1.2.3", "1.2.3"),
        (">1.2.3e", "1.2.3.5"),
        ("<1.2.3", "1.2.3"),
        ("<1.2.3e", "1.2.3.5"),
        ("=1.2.3", "1.2.3"),
        ("=1.2.3e", "1.2.3.5"),
    ],
)
def test_clean_version(version, result):
    assert clean_version(version) == result
