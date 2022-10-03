import pytest

from sxm_tmk.core.dependency import BrokenVersionSpecifier, PinnedPackage


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
