$(document).ready(function(){

    // Google Maps setup
    var mapOptions = {
        center: new google.maps.LatLng(-34.397, 150.644),
        zoom: 8,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    var map = new google.maps.Map(document.getElementById("map_canvas"),
                                  mapOptions);

    // variables for the DOM elements
    var WIDTH = 320;
    var HEIGHT = 240;
    var video = $("#live").get()[0];
    var canvas = $("#canvas");
    var ctx = canvas.get()[0].getContext('2d');

    // scale back the overall direction of the motion vector
    var SCALE_FACTOR = 0.2;

    // move map in the corresponding direction
    function get_direction(float_blob) {
        var reader = new FileReader();
        reader.onload = (function(blob) {
            return function(event) {
                var x = parseFloat(event.target.result.slice(0,5))
                    * WIDTH * SCALE_FACTOR;
                var y = parseFloat(event.target.result.slice(5,10))
                    * HEIGHT * SCALE_FACTOR;
                $("#direction").html(x + "," + y);
                map.panBy(x, y);
            };
        })(float_blob);
        reader.readAsBinaryString(float_blob);
    }

    // mirror the canvas
    ctx.translate(WIDTH, 0);
    ctx.scale(-1, 1);

    // request access to webcam
    navigator.webkitGetUserMedia(
        {video: true, audio: false},
        function(stream) {
            video.src = webkitURL.createObjectURL(stream);
        },
        function(err) {
            console.log("Unable to get video stream!")
        }
    );

    // establish websocket
    var ws = new WebSocket("ws://localhost:8888/websocket");
    ws.onopen = function () {
        console.log("Opened connection to websocket");
    }
    ws.onmessage = function(msg) {
        var target = document.getElementById("target");

        // display the updated frame
        url = window.webkitURL.createObjectURL(msg.data.slice(10, msg.data.size));
        target.onload = function() {
            window.webkitURL.revokeObjectURL(url);
        };
        target.src = url;

        // handle the direction of the motion in the frame
        get_direction(msg.data.slice(0,10));
    }

    // send a constant stream to the server
    timer = setInterval(
        function () {
            ctx.drawImage(video, 0, 0, WIDTH, HEIGHT);
            var data = canvas.get()[0].toDataURL('image/jpeg', 1.0);
            ws.send(data.split(',')[1]);
        }, 250);

});
