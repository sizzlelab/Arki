function api_call(operation, data_obj, cb) {
  data_obj['operation'] = operation;
  $.ajax({
    type: 'POST',
    url: '/api/',
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
