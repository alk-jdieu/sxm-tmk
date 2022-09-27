import pytest

from sxm_tmk.core.dependency import Constraint, Dependency, DependencyChecker


@pytest.mark.parametrize(
    ("version", "proposal", "result"),
    [
        ("==1.0.0", "1.0.0", True),
        ("==1.0.1", "1.0.0", False),
        (">=1.0.0", "1.0.0", True),
        (">=1.0.0", "1.0.1", True),
        (">=1.0.0", "0.9.0", False),
        (">1.0.0", "1.0.0", False),
        (">1.0.0", "1.0.1", True),
        (">1.0.0", "0.9.0", False),
        ("<=1.0.0", "1.0.0", True),
        ("<=1.0.0", "1.0.1", False),
        ("<=1.0.0", "0.9.0", True),
        ("<1.0.0", "1.0.0", False),
        ("<1.0.0", "1.0.1", False),
        ("<1.0.0", "0.9.0", True),
    ],
)
def test_dependency_checker(version, proposal, result):
    a_dep = Dependency("thing", proposal)
    a_constraint = DependencyChecker("thing", Constraint(version=version))
    if result:
        assert a_constraint.match(a_dep)
    else:
        assert not a_constraint.match(a_dep)


def test_dependency_checker_multiple_proposal():
    deps = [Dependency("thing", f"1.{i}.{i%2}") for i in range(10)]
    deps.extend([Dependency("thingpy", f"1.{i}.0") for i in range(10)])
    deps.extend([Dependency("thing", f"0.{i}.0") for i in range(10)])
    a_constraint = DependencyChecker("thing", Constraint(version=">=1.4.2"))
    a_constraint_py = DependencyChecker("thingpy", Constraint(version="==1.4.0"))
    a_constraint_not_solvable = DependencyChecker("what", Constraint(version="==1.4.0"))

    matching_deps = list(a_constraint.filter_matching_propositions(deps))
    assert matching_deps == [Dependency("thing", f"1.{i}.{i%2}") for i in range(5, 10)]
    assert len(list(a_constraint_py.filter_matching_propositions(deps))) == 1
    assert not list(a_constraint_not_solvable.filter_matching_propositions(deps))


def test_compare_dependency():
    a, b = Dependency("apkg", "1.0.0"), Dependency("apkg", ">1.0.0")
    assert a == b
    b = Dependency("apkg", ">1.0.1")
    assert a != b
