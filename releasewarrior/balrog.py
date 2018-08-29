import logging
import re
import requests

from copy import deepcopy
from mozilla_version.balrog import BalrogReleaseName

BALROG_API_ROOT = 'https://aus5.mozilla.org/api/v1'

log = logging.getLogger(name=__name__)


class BalrogError(Exception):
    pass


class TooManyBlobsFoundError(BalrogError):
    def __init__(self, blob_name, found_blobs):
        super().__init__('Multiple blobs found for "{}": {}'.format(blob_name, found_blobs))


class NoBlobFoundError(BalrogError):
    def __init__(self, blob_name):
        super().__init__('No blob found for "{}"'.format(blob_name))


def get_release_blob(blob_name):
    url = '{}/releases/{}'.format(BALROG_API_ROOT, blob_name)
    req = requests.get(url, verify=True, timeout=4)
    req.raise_for_status()
    return req.json()


def get_releases(blob_name, name_prefix=None):
    url = '{}/releases'.format(BALROG_API_ROOT)
    params = {
        'product': extract_product_from_blob_name(blob_name),
        'name_prefix': blob_name if name_prefix is None else name_prefix,
        'names_only': True
    }
    req = requests.get(url, verify=True, params=params, timeout=4)
    req.raise_for_status()
    return req.json()['names']


def extract_product_from_blob_name(blob_name):
    return blob_name.split('-')[0]


def ensure_blob_name_exists_on_balrog(blob_name):
    releases = get_releases(blob_name)
    if len(releases) > 1:
        raise TooManyBlobsFoundError(blob_name, releases)
    if len(releases) < 1:
        raise NoBlobFoundError(blob_name)


def craft_wnp_blob(orig_blob, wnp_url, for_channels, for_locales=None, for_version=None):
    blob_name = orig_blob['name']
    for_channels = [channel.strip() for channel in for_channels.split(',')]
    for_locales = get_for_locales(blob_name, for_locales)
    for_version = get_for_version(blob_name, for_version)

    new_blob = deepcopy(orig_blob)
    update_rules = new_blob.setdefault('updateLine', [])

    existing_wnp_rules = [
        rule for rule in update_rules if rule.get('fields', {}).get('actions', '') == "showURL"
    ]
    number_of_existing_rules = len(existing_wnp_rules)

    if number_of_existing_rules > 1:
        raise NotImplementedError('Cannot handle releases that have more than 1 WNP rule')
    elif number_of_existing_rules == 1:
        existing_wnp_rule = existing_wnp_rules[0]
        log.warn('replacing existing rule: {}'.format(existing_wnp_rule))
        update_rules.remove(existing_wnp_rule)

    wnp_rule = {
        'fields': {
            'actions': 'showURL',
            'openURL': wnp_url,
        },
        'for': {
            'channels': for_channels,
            'locales': for_locales,
            'versions': [for_version],
        },
    }

    update_rules.append(wnp_rule)

    log.info('New updateLine rules: {}'.format(update_rules))

    return new_blob


def get_for_locales(blob_name, for_locales=None):
    if for_locales is None:
        product = extract_product_from_blob_name(blob_name)
        all_releases_names_for_product = get_releases(blob_name, name_prefix=product)
        previous_release = find_previous_release(blob_name, all_releases_names_for_product)
        previous_release_blob = get_release_blob(blob_name=previous_release)
        for_locales = _get_locales_from_blob(previous_release_blob, previous_release)
        log.info('for_locales gotten from previous "{}": {}'.format(previous_release, for_locales))
    else:
        for_locales = [locale.strip() for locale in for_locales.split(',')]
        log.info('Using for_locales from command line: {}'.format(for_locales))

    if not isinstance(for_locales, list):
        raise BalrogError('{} is not a list'.format(for_locales))

    return for_locales


_ENDS_WITH_BUILD_REGEX = re.compile(r'build\d+$')


def find_previous_release(blob_name, all_releases_names_for_product):
    original_release = BalrogReleaseName.parse(blob_name)
    # ends_with_build strips out nightly blobs and the ones that were created manually
    ends_with_build = [
        release
        for release in all_releases_names_for_product
        if _ENDS_WITH_BUILD_REGEX.search(release)
    ]
    balrog_releases = [BalrogReleaseName.parse(release) for release in ends_with_build]

    same_type = [
        release
        for release in balrog_releases
        if release.version.version_type == original_release.version.version_type
    ]
    if original_release.version.is_release:
        same_type = [
            release for release in same_type if release.version.is_release
        ]    # strips ESR out
    elif original_release.version.is_esr:
        same_type = [
            release for release in same_type if release.version.is_esr
        ]    # strips release out

    sorted_releases = same_type
    sorted_releases.sort(reverse=True)

    for release in sorted_releases:
        if release < original_release:
            previous_release = str(release)
            log.info('Previous release was: {}'.format(previous_release))
            return previous_release

    raise BalrogError('Could not find a version smaller than {}'.format(original_release))


def _get_locales_from_blob(blob, blob_name):
    locales = []
    for rule in blob.get('updateLine', []):
        candidate_locales = rule.get('for', {}).get('locales', [])
        if candidate_locales:
            if locales:
                raise BalrogError(
                    'Too many locales defined in blob "{}". Found {} and {}'.format(
                        blob_name, candidate_locales, locales
                    )
                )
            locales = candidate_locales

    if not locales:
        raise BalrogError('No locales found in blob "{}"'.format(blob_name))

    return locales


_FOR_VERSION_PATTERN = re.compile(r'<\d+\.0')


def get_for_version(blob_name, for_version=None):
    if for_version is None:
        balrog_release = BalrogReleaseName.parse(blob_name)
        for_version = '<{}.0'.format(balrog_release.version.major_number)
        log.info('for_version build from original blob: {}'.format(for_version))
    else:
        log.info('Using for_version from command line: {}'.format(for_version))

    if _FOR_VERSION_PATTERN.match(for_version) is None:
        raise BalrogError('{} does not match a valid for_version pattern'.format(for_version))

    return for_version
