import pytest

from releasewarrior.helpers import validate_graphid


@pytest.mark.parametrize("graphid,expected", [
    ('UZ1SzyoKQuCQWNw5DD3Wew', True),
    ('H8sEEXySSqSQdAcbaM8VjA', True),
    ('', False),  # Empty
    ('H8sEEXySSqS$dAcbaM8VjA', False),  # Invalid characters
    ('H8sEEXySSqSQdAcbaM8Vj', False),  # Too short
    ("u'H8sEEXySSqSQdAcbaM8VjA", False),  # Too long, releaserunner's unicode output
    (u'UZ1SzyoKQuCQWNw5DD3Wew', True),  # Releaserunner displays unicode output
])
def test_validate_graphid(graphid, expected):
    assert validate_graphid(graphid) == expected
