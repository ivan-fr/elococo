def get_dict_data_formset(formset):
    data = {}
    for field in formset.management_form:
        data["-".join((formset.management_form.prefix, field.name))
             ] = field.value()
    for form in formset:
        for field in form:
            data[field.html_name] = field.value()
    return data