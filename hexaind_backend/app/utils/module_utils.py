from numpydoc.docscrape import NumpyDocString


def parse_numpy_doc_string(numpy_doc_string, parameter_names):
    param_descriptions = {param_name: '' for param_name in parameter_names}
    if numpy_doc_string:
        parsed_doc_string = NumpyDocString(numpy_doc_string)
        if parsed_doc_string.get('Parameters'):
            for param_details in parsed_doc_string.get('Parameters'):
                if param_details.desc:
                    help_text = '\n'.join(param_details.desc)
                    param_descriptions[param_details.name] = help_text

    return param_descriptions
