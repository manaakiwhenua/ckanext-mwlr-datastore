# Additional plugins might expose endpoints that need testing for restricted resources

# This is a copy of what's in .env. If the env list changes, this test fails and alerts the dev team to check for any changes that need to be made for restricted resources
EXPECTED_LOADED_PLUGINS = "bsi_restricted_resources tracking mwlr_datastore activity datapusher_plus datastore geo_view geojson_view image_view pdf_view ldap scheming_datasets shp_view spatial_metadata spatial_query text_view datatables_view stats envvars"


def test_loaded_plugins():
    import os

    loaded_plugins = os.getenv("CKAN__PLUGINS", "")
    for plugin in loaded_plugins.split():
        assert plugin in EXPECTED_LOADED_PLUGINS, (
            f"Unexpected plugin loaded: {plugin}. Please check if this plugin adds any endpoints or actions that needs to be masked for restricted resources."
        )
