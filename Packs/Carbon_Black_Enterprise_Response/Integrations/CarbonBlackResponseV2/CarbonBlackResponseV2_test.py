"""Base Integration for Cortex XSOAR - Unit Tests file

Pytest Unit Tests: all funcion names must start with "test_"

More details: https://xsoar.pan.dev/docs/integrations/unit-testing

MAKE SURE YOU REVIEW/REPLACE ALL THE COMMENTS MARKED AS "TODO"

You must add at least a Unit Test function for every XSOAR command
you are implementing with your integration
"""

import json
import io
import pytest
import demistomock as demisto


def util_load_json(path):
    with io.open(path, mode='r', encoding='utf-8') as f:
        return json.loads(f.read())


QUERY_STRING_CASES = [
    (
        {'hostname': 'ec2amaz-l4c2okc', 'query': 'chrome.exe'}, False,  # case both query and params
        'chrome.exe'  # expected
    ),
    (
        {'hostname': 'ec2amaz-l4c2okc'}, False,  # case only params
        'hostname:ec2amaz-l4c2okc'  # expected
    ),
    (
        {'query': 'chrome.exe'}, False,  # case only query
        'chrome.exe'  # expected
    ),
    (
        {}, True,  # case no params
        ''  # expected
    )
]


@pytest.mark.parametrize('params, empty, expected_results', QUERY_STRING_CASES)
def test_create_query_string(params, empty, expected_results):
    """
    Given:
        - A search task's parameters

    When:
        - running commands using filter arguments

    Then:
        - validating the query string containing the params

    """
    from CarbonBlackResponseV2 import _create_query_string

    query_string = _create_query_string(params, allow_empty=empty)

    assert query_string == expected_results


def test_fail_create_query_string():
    """
    Given:
        - En empty dictionary of params

    When:
        - running commands using filter arguments

    Then:
        - validating the function fails

    """
    from CarbonBlackResponseV2 import _create_query_string
    with pytest.raises(Exception) as e:
        _create_query_string({})
    assert str(e.value) == 'Carbon Black EDR - Search without any filter is not permitted.'


PARSE_FIELD_CASES = [
    ('x.x.x.x,06d3d4a5ba28|', ',', 1, '|', '06d3d4a5ba28'),
    ('06d3d4a5ba28|', ',', 0, '|', '06d3d4a5ba28'),
    ('06d3d4a5ba28^&*', ',', 0, '&^*', '06d3d4a5ba28'),
]


@pytest.mark.parametrize('field, sep, index_after_split, chars_to_remove, expected', PARSE_FIELD_CASES)
def test_parse_field(field, sep, index_after_split, chars_to_remove, expected):
    """
        Given:
            - A field with x.x.x.x,y| format

        When:
            - running Endpoints command

        Then:
            - validate only the ip returns
        """
    from CarbonBlackResponseV2 import _parse_field
    res = _parse_field(field, sep, index_after_split, chars_to_remove)
    assert res == expected


@pytest.mark.parametrize('isolation_activated, is_isolated, expected',
                         [(0, 1, 'Pending unisolation'), (0, 0, 'No'), (1, 0, 'Pending isolation'), (1, 1, 'Yes')])
def test_get_isolation_status_field(isolation_activated, is_isolated, expected):
    """
    Given:
        - A sensor isolation configuration

    When:
        - getting/ setting isolation status for a sensor

    Then:
        - validate status according to API.
    """
    from CarbonBlackResponseV2 import _get_isolation_status_field
    status = _get_isolation_status_field(isolation_activated, is_isolated)
    assert status == expected


''' ProcessEventDetail Tests'''

FILEMOD_CASES = [
    (
        "1|2013-09-16 07:11:58.000000|test_path.dll|||false",  # case only one valid string
        [{'event_time': '2013-09-16 07:11:58.000000',
          'file_path': 'test_path.dll',
          'file_type': '',
          'flagged_as_potential_tamper_attempt': 'false',
          'md5_after_last_write': '',
          'operation_type': 'Created the file'}]  # expected
    )
]
FILEMOD_BAD_CASES = [
    (
        "1|2013-09-16 07:11:58.000000|test_path.dll||false",  # case missing field
        'Carbon Black EDR - Missing details. Ignoring entry: 1|2013-09-16 07:11:58.000000|test_path.dll||false.'
        # error expected
    )
]


@pytest.mark.parametrize('data_str, expected', FILEMOD_CASES)
def test_filemod(data_str, expected):
    """
        Given:
            - A process event data containing filemod field

        When:
            - formatting the data to correct format

        Then:
            - validating the new filemod field contains json with correctly mapped data
        """
    from CarbonBlackResponseV2 import filemod_complete

    res = filemod_complete(data_str).format()
    assert res == expected


@pytest.mark.parametrize('data_str, expected', FILEMOD_BAD_CASES)
def test_fail_filemod(mocker, data_str, expected):
    """
        Given:
            - A process event data containing invalid filemod field

        When:
            - formatting the data to correct format

        Then:
            - validates when field in the response are missing, the error will show and the value be skipped.
    """
    from CarbonBlackResponseV2 import filemod_complete
    demisto_mocker = mocker.patch.object(demisto, 'debug')
    filemod_complete(data_str)
    assert demisto_mocker.call_args[0][0] == expected


MODLOAD_CASES = [
    (
        '2013-09-19 22:07:07.000000|f404e59db6a0f122ab26bf4f3e2fd0fa|test_path.dll',  # case valid response
        [{'event_time': '2013-09-19 22:07:07.000000',
          'loaded_module_full_path': 'test_path.dll',
          'loaded_module_md5': 'f404e59db6a0f122ab26bf4f3e2fd0fa'}]  # expected
    )
]


@pytest.mark.parametrize('data_str, expected', MODLOAD_CASES)
def test_modload(data_str, expected):
    """
        Given:
            - A process event data containing modload field

        When:
            - formatting the data to correct format

        Then:
            - validating the new modload field contains json with correctly mapped data
    """
    from CarbonBlackResponseV2 import modload_complete

    res = modload_complete(data_str).format()
    assert res == expected


REGMOD_CASES = [
    (
        "2|2013-09-19 22:07:07.000000|test_path",
        [{'event_time': '2013-09-19 22:07:07.000000',
          'operation_type': 'First wrote to the file',
          'registry_key_path': 'test_path'}]
    )
]


@pytest.mark.parametrize('data_str, expected', REGMOD_CASES)
def test_regmod(data_str, expected):
    """
        Given:
            - A process event data containing regmod field

        When:
            - formatting the data to correct format

        Then:
            - validating the new regmod field contains json with correctly mapped data
    """
    from CarbonBlackResponseV2 import regmod_complete

    res = regmod_complete(data_str).format()
    assert res == expected


CROSSPROC_CASES = [
    (
        "ProcessOpen|2014-01-23 09:19:08.331|00000177-0000-0258-01cf-c209d9f1c431|204f3f58212b3e422c90bd9691a2df28|"
        "test_path.exe|1|2097151|false",
        [{'ProcessOpen_sub-type': 'handle open to process',
          'cross-process_access_type': 'ProcessOpen',
          'event_time': '2014-01-23 09:19:08.331',
          'flagged_as_potential_tamper_attempt': 'false',
          'requested_access_priviledges': '2097151',
          'targeted_process_md5': '204f3f58212b3e422c90bd9691a2df28',
          'targeted_process_path': 'test_path.exe',
          'targeted_process_unique_id': '00000177-0000-0258-01cf-c209d9f1c431'}]
    )
]


@pytest.mark.parametrize('data_str, expected', CROSSPROC_CASES)
def test_crossproc(data_str, expected):
    """
        Given:
            - A process event data containing crossproc field

        When:
            - formatting the data to correct format

        Then:
            - validating the new crossproc field contains json with correctly mapped data
    """
    from CarbonBlackResponseV2 import crossproc_complete

    res = crossproc_complete(data_str).format()
    assert res == expected