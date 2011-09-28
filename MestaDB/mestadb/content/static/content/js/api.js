function api_call(operation, data_obj, cb) {
  data_obj['operation'] = operation;
  $.ajax({
    type: 'POST',
    url: '/content/api/',
    dataType: 'json',
    data: data_obj,
    success: function(responseJson) {
      cb(responseJson);
    },
    error: function(response, x, y) {
      alert("Server error " + response.status);
    }
  });
  // return false;
}

/*
 * API functions
 * Use primitive variable, if there is only one parameter to pass
 * Otherwise use data_obj dictionary.
 */

function api_content_get(id, cb) {
  data_obj = { "id": id }
  api_call('content_get', data_obj, cb);
}

function api_content_search(data_obj, cb) {
  api_call('content_search', data_obj, cb);
}
