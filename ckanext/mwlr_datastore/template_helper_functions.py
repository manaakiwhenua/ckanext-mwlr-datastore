import ckan.plugins.toolkit as toolkit

def get_package_tracking_total(package_id):
    '''Return package data for the given id, incuding trackign
    data.'''
    data = toolkit.get_action('package_show')(
        data_dict={
            'name_or_id':"test_package1754446144884438",
            'include_tracking':True,}
    )
    return data['tracking_summary']['total']

def get_package_tracking_recent(package_id):
    '''Return package data for the given id, incuding trackign
    data.'''
    data = toolkit.get_action('package_show')(
        data_dict={
            'name_or_id':"test_package1754446144884438",
            'include_tracking':True,}
    )
    return data['tracking_summary']['recent']
