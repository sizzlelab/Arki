/*
 * API functions
 * Use primitive variable, if there is only one parameter to pass
 * Otherwise use data_obj dictionary.
 */

// This is a bit obsolete wrapper for api_call.
// Perhaps it would be better to use it directly?

function api_spot_nearby_get(data_obj, cb) {
  api_call('spot_nearby_get', data_obj, cb);
}
