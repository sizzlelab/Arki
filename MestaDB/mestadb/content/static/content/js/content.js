

// From http://www.thedotproduct.org/experiments/geo/

var wpid = false, op;

// Fake location for testing purposes
var userlocation = {
    lat: 60.17500,
    lon: 24.945,
    accuracy: 20000000
}


function message(msg) {
  $("#output").html(msg)
}

function initialize() {
  message("Haetaan paikkaa");
  get_pos();
  init_geo();

function trim_float(fl, digits) {
  var dec = Math.pow(10, digits);
  return Math.round(fl * dec) / dec;
}


// This is the function which is called each time the Geo location position is updated
function geo_success(position) {
  var lat = trim_float(position.coords.latitude, 7);
  var lon = trim_float(position.coords.longitude, 7);
  userlocation = {
    lat: lat,
    lon: lon,
    accuracy: Math.round(position.coords.accuracy, 1)
  }
  var center = lat + "," + lon;
  message(center + ", tarkkuus " + Math.round(position.coords.accuracy, 1)) + " m";
  // TODO: update map image only when map div loads, now it gets updated always when location changes.
  var url = "http://maps.google.com/maps/api/staticmap?center="+center+"&zoom=14&size=512x512&maptype=roadmap&markers=color:blue|label:X|"+center+"&markers=color:green|label:T|60.173,24.953&sensor=true"
  $("#mapimage").attr("src", url);
  /*
  tp = {
      'lat': lat,
      'lon': lon,
      'speed': trim_float(position.coords.speed, 2),
      'ele': trim_float(position.coords.altitude, 2),
      'hacc': position.coords.accuracy,
      'vacc': position.coords.altitudeAccuracy,
      'heading': trim_float(position.coords.heading, 2),
      'position_timestamp': position.timestamp,
      'localtime': current_datetime
  }
  */
}

// This function is called each time navigator.geolocation.watchPosition() generates an error (i.e. cannot get a Geo location reading)
function geo_error(error) {
  alert("Geolocation error: " + error.code);
  switch(error.code)
  {
    case error.TIMEOUT:
      message("Geolocation timeout!");
    break;
  };
}


function get_pos() {
  // Check that the Browser is capable
  if(!!navigator.geolocation) {
    // wpid=navigator.geolocation.watchPosition(geo_success, geo_error, {enableHighAccuracy:true, maximumAge:30000, timeout:27000});
    wpid = navigator.geolocation.getCurrentPosition(geo_success, geo_error, {maximumAge: 60000, timeout:10000, enableHighAccuracy: true});
  } else {
    message("ERROR: Your Browser doesnt support the Geo Location API");
  }
}



// Initialiser: This will find the output message div and set up the actions on the start/stop button
function init_geo() {
  // Close mainview when close button is pressed
  $('.closeviewbutton').click(function() {
    $(".mainview").hide('slow');
  });

  $('#get_location_button').click(function() {
    if (wpid) { // If we already have a wpid which is the ID returned by navigator.geolocation.watchPosition()
      navigator.geolocation.clearWatch(wpid);
    }
    message("Haetaan paikkaa")
    get_pos();
  });

  $('#chat_button').click(function() {
    //alert('Handler for ChatButton.click() called.');
    $("#chatview").show('slow');
    if (userlocation) {
      var data = {
        "useragent": navigator.userAgent,
        "lat": userlocation['lat'],
        "lon": userlocation['lon'],
        "accuracy": userlocation['accuracy'],
        "operation": "messages_get"
      }
      var jsoni = JSON.stringify(data);
      // var original_label = $(this).html();
      // $(this).html("Haetaan...");
      $.ajax({
        type: 'GET',
        url: '/hsl/api/',
        dataType: 'json',
        data: data,
        success: function(responseJson) {
          // $(this).html(original_label);
          // $(this).html("Omat&nbsp;lahdot");
          var m = responseJson['messages'];
          // alert("jee")
          render_messages(m);
        },
        error: function(responseJson) {
            message("Invalid response from server!");
            alert("Invalid response from server!");
        }
      }); // ajax
    }
  });

  $('#map_button').click(function() {
    $("#mapview").show('slow');
    // TODO: load map image now, not in get_pos()
  });



  $('#send_button').click(function() {
    $("#omatview").show('slow');
    if (userlocation) {
      var data = {
        "useragent": navigator.userAgent,
        "lat": userlocation['lat'],
        "lon": userlocation['lon'],
        "accuracy": userlocation['accuracy'],
        "operation": "stop_nearby_get"
      }
      var jsoni = JSON.stringify(data);
      // var original_label = $(this).html();
      // $(this).html("Haetaan...");
      $.ajax({
        type: 'GET',
        url: '/hsl/api/',
        dataType: 'json',
        data: data,
        success: function(responseJson) {
          // $(this).html(original_label);
          // $(this).html("Omat&nbsp;lahdot");
          var s = responseJson['stops'];
          render_stoplist(s);
        },
        error: function(responseJson) {
            message("Invalid response from server!");
            alert("Invalid response from server!");
        }
      }); // ajax
    }
  }); // click


  $('#favourites_button').click(function() {
    $("#favouritesview").show('slow');
    var s_div = $("#favouritescontent");
    s_div.html('<h1>Suosikit</h1>');
    var fav = $.cookie('favourites');
    if (fav) {
      fav = fav.split(",");
      for (i in fav) {
        var stop = $(document.createElement("div"))
          .attr({ title: 'Click me ', id: "s" + fav[i] })
          .addClass("favstopname")
          .appendTo(s_div)
          .html(fav[i] + "\n")
          .click(function() {
            var stopid = this.id.replace(/^\D+/, '');
            alert(stopid);
          });
      }
      // alert(fav.unshift(stopid));
    } else {;}
  });


}


// Initialise the whole system (above)
//window.onload=init_geo;
