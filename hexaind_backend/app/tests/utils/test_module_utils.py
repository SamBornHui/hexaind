from app.utils.module_utils import parse_numpy_doc_string


def test_parse_numpy_doc_string_positive_case():
    numpy_doc_string = """
    Creates two identical pandas DataFrames for testing purposes.

    Parameters
    ----------
    start_date : str
        The start date for the widget. Must be in the format 'YYYY-MM-DD'.
        eg: '2023-12-12'

    end_date : str
        $The end date for the widget. Must be in the format 'YYYY-MM-DD'. x should be in [0-1]$

    Returns
    -------
    tuple
        A tuple containing two pandas DataFrames with the same data.
    """

    parameter_names = ['start_date', 'end_date']
    expected_output = {
        'start_date': "The start date for the widget. Must be in the format 'YYYY-MM-DD'.\neg: '2023-12-12'",
        'end_date': "$The end date for the widget. Must be in the format 'YYYY-MM-DD'. x should be in [0-1]$"}

    actual_outputs = parse_numpy_doc_string(numpy_doc_string, parameter_names)
    assert actual_outputs == expected_output
