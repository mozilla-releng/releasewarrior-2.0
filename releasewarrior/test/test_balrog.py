import pytest

from unittest.mock import MagicMock

from releasewarrior import balrog


def test_get_release_blob(monkeypatch):
    requests_mock = MagicMock()
    response_mock = MagicMock()
    response_mock.json.return_value = {'some blob'}
    requests_mock.get.return_value = response_mock
    monkeypatch.setattr(balrog, 'requests', requests_mock)
    assert balrog.get_release_blob('firefox-61.0.2-build1') == {'some blob'}
    requests_mock.get.assert_called_with(
        'https://aus5.mozilla.org/api/v1/releases/firefox-61.0.2-build1',
        verify=True,
        timeout=4
    )


@pytest.mark.parametrize('name_prefix, returned_value, expected_releases, expected_params', ((
    None,
    {
        'names': [
            'firefox-61.0.2-build1',
            'firefox-61.0.2-build1-No-WNP',
        ],
    },
    [
        'firefox-61.0.2-build1',
        'firefox-61.0.2-build1-No-WNP',
    ],
    {
        'product': 'firefox',
        'name_prefix': 'firefox-61.0.2-build1',
        'names_only': True
    }
), (
    'firefox',
    {
        'names': [
            'firefox-60.0-build1',
            'firefox-61.0-build1',
            'firefox-61.0.2-build1',
            'firefox-61.0.2-build1-No-WNP',
        ],
    },
    [
        'firefox-60.0-build1',
        'firefox-61.0-build1',
        'firefox-61.0.2-build1',
        'firefox-61.0.2-build1-No-WNP',
    ],
    {
        'product': 'firefox',
        'name_prefix': 'firefox',
        'names_only': True
    }
)))
def test_get_releases(
    monkeypatch, name_prefix, returned_value, expected_releases, expected_params
):
    requests_mock = MagicMock()
    response_mock = MagicMock()
    response_mock.json.return_value = returned_value
    requests_mock.get.return_value = response_mock
    monkeypatch.setattr(balrog, 'requests', requests_mock)
    assert balrog.get_releases('firefox-61.0.2-build1', name_prefix) == expected_releases
    requests_mock.get.assert_called_with(
        'https://aus5.mozilla.org/api/v1/releases',
        verify=True,
        params=expected_params,
        timeout=4
    )


@pytest.mark.parametrize('returned_releases, raises', ((
    (['firefox-61.0.2-build1'], False),
    (['firefox-61.0.2-build1', 'firefox-61.0.2-build1-No-WNP'], True),
    ([], True),
)))
def test_ensure_blob_name_exists_on_balrog(monkeypatch, returned_releases, raises):
    monkeypatch.setattr(balrog, 'get_releases', lambda _: returned_releases)
    if raises:
        with pytest.raises(balrog.BalrogError):
            balrog.ensure_blob_name_exists_on_balrog('firefox-61.0.2-build1')
    else:
        balrog.ensure_blob_name_exists_on_balrog('firefox-61.0.2-build1')


@pytest.mark.parametrize('orig_blob, wnp_url, for_channels, for_locales, for_version, raises, \
expected_blob', ((
    {
        'name': 'firefox-61.0.2-build1',
        'updateLine': [],
    },
    'https://whats.new.page',
    'release-localtest, release-cdntest, release',
    'en-US, fr, de',
    '<61.0',
    False,
    {
        'name': 'firefox-61.0.2-build1',
        'updateLine': [{
            'fields': {
                'actions': 'showURL',
                'openURL': 'https://whats.new.page',
            },
            'for': {
                'channels': ['release-localtest', 'release-cdntest', 'release'],
                'locales': ['en-US', 'fr', 'de'],
                'versions': ['<61.0'],
            },
        }],
    },
), (
    {
        'name': 'firefox-61.0.2-build1',
        'updateLine': [{
            'fields': {
                'actions': 'showURL',
                'openURL': 'https://old.whats.new.page',
            },
            'for': {'locales': ['en-UK']},
        }],
    },
    'https://whats.new.page',
    'release-localtest, release-cdntest, release',
    'en-US, fr, de',
    '<61.0',
    False,
    {
        'name': 'firefox-61.0.2-build1',
        'updateLine': [{
            'fields': {
                'actions': 'showURL',
                'openURL': 'https://whats.new.page',
            },
            'for': {
                'channels': ['release-localtest', 'release-cdntest', 'release'],
                'locales': ['en-US', 'fr', 'de'],
                'versions': ['<61.0'],
            },
        }],
    },
), (
    {
        'name': 'firefox-61.0.2-build1',
        'updateLine': [{
            'fields': {
                'actions': 'showURL',
                'openURL': 'https://whats.new.page',
            },
            'for': {'locales': ['en-US', 'fr', 'de']},
        }, {
            'fields': {
                'actions': 'showURL',
                'openURL': 'https://second-whats.new.page',
            },
            'for': {'locales': ['zh-CN', 'zh-TW', 'en-CA']}
        }],
    },
    'https://whats.new.page',
    'release-localtest, release-cdntest, release',
    'en-US, fr, de',
    '<61.0',
    True,
    None,
)))
def test_craft_wnp_blob(
    orig_blob, wnp_url, for_channels, for_locales, for_version, raises, expected_blob
):
    if raises:
        with pytest.raises(NotImplementedError):
            balrog.craft_wnp_blob(orig_blob, wnp_url, for_channels, for_locales, for_version)
    else:
        assert balrog.craft_wnp_blob(
            orig_blob, wnp_url, for_channels, for_locales, for_version
        ) == expected_blob


@pytest.mark.parametrize('blob_name, for_locales, returned_locales, raises, expected_locales', ((
    'firefox-61.0.2-build2', None, ['en-US', 'fr', 'de'], False, ['en-US', 'fr', 'de']
), (
    'irrelevant', 'en-US,fr,de', None, False, ['en-US', 'fr', 'de']
), (
    'irrelevant', 'en-US, fr, de', None, False, ['en-US', 'fr', 'de']
), (
    'firefox-61.0.2-build2', None, 'not a list', True, None
)))
def test_get_for_locales(
    monkeypatch, blob_name, for_locales, returned_locales, raises, expected_locales
):
    monkeypatch.setattr(
        balrog, 'get_releases', lambda _, name_prefix: ['firefox-61.0.2-build1']
    )
    monkeypatch.setattr(
        balrog, 'get_release_blob', lambda blob_name: {
            'updateLine': [{
                'for': {'locales': returned_locales},
            }],
        }
    )

    if raises:
        with pytest.raises(balrog.BalrogError):
            balrog.get_for_locales(blob_name, for_locales)
    else:
        assert balrog.get_for_locales(blob_name, for_locales) == expected_locales


@pytest.mark.parametrize('blob_name, all_releases_names_for_product, raises, expected_release', ((
    'firefox-61.0.2-build2',
    ['firefox-62.0b12-build1', 'firefox-61.0.1-build2', 'firefox-61.0.3-build1'],
    False,
    'firefox-61.0.1-build2'
), (
    'firefox-61.0.2-build2',
    [
        'firefox-62.0b12-build1',
        'firefox-61.0.1-build2',
        'firefox-61.0.3-build1',
        'firefox-61.0.2-build1',
    ],
    False,
    'firefox-61.0.2-build1'
), (
    'firefox-60.1.0esr-build1',
    [
        'firefox-62.0b12-build1',
        'firefox-61.0.1-build2',
        'firefox-61.0.3-build1',
        'firefox-60.0.2-build1',
        'firefox-60.0.2esr-build1',
        'firefox-60.0.2esr-build2',
    ],
    False,
    'firefox-60.0.2esr-build2',
), (
    'firefox-50.0-build1',
    [
        'firefox-62.0b12-build1',
        'firefox-61.0.1-build2',
        'firefox-61.0.3-build1',
        'firefox-61.0.2-build1',
    ],
    True,
    None
)))
def test_find_previous_release(
    blob_name, all_releases_names_for_product, raises, expected_release
):
    if raises:
        with pytest.raises(balrog.BalrogError):
            balrog.find_previous_release(blob_name, all_releases_names_for_product)
    else:
        assert balrog.find_previous_release(
            blob_name, all_releases_names_for_product
        ) == expected_release


@pytest.mark.parametrize('blob, raises, expected_locales', ((
    {
        'updateLine': [{
            'for': {'locales': ['en-US', 'fr', 'de']},
        }],
    },
    False,
    ['en-US', 'fr', 'de']
), (
    {
        'updateLine': [{
            'for': {'locales': ['en-US', 'fr', 'de']},
        }, {
            'for': {'locales': ['zh-CN', 'zh-TW', 'en-CA']},
        }],
    },
    True,
    None
), (
    {},
    True,
    None
)))
def test_get_locales_from_blob(blob, raises, expected_locales):
    if raises:
        with pytest.raises(balrog.BalrogError):
            balrog._get_locales_from_blob(blob, 'some blob name')
    else:
        assert balrog._get_locales_from_blob(blob, 'some blob name') == expected_locales


@pytest.mark.parametrize('blob_name, for_version, raises, expected_for_version', (
    ('firefox-61.0-build1', None, False, '<61.0'),
    ('firefox-61.0.1-build1', None, False, '<61.0'),
    ('irrelevant', '<61.0', False, '<61.0'),
    ('irrelevant', '<60.0', False, '<60.0'),
    ('irrelevant', '60.0', True, 'irrelevant'),
))
def test_get_for_version(blob_name, for_version, raises, expected_for_version):
    if raises:
        with pytest.raises(balrog.BalrogError):
            balrog.get_for_version(blob_name, for_version)
    else:
        assert balrog.get_for_version(blob_name, for_version) == expected_for_version
