$(document).ready(function(){

    // Google Maps setup
    var mapOptions = {
        center: new google.maps.LatLng(42.371751, -71.115489),
        zoom: 16,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    var map = new google.maps.Map(document.getElementById("map_canvas"),
                                  mapOptions);

    // variables for the DOM elements
    var video = $("#live").get()[0];
    var direction = $("#direction");
    var canvas = $("#canvas");
    var ctx = canvas.get()[0].getContext('2d');

    // mirror the canvas
    ctx.translate(MotionApp.WIDTH, 0);
    ctx.scale(-1, 1);

    // move map in the corresponding direction
    function get_direction(float_blob) {
        var reader = new FileReader();
        reader.onload = (function(blob) {
            return function(event) {
                var x = parseFloat(event.target.result.slice(0,5))
                    * MotionApp.WIDTH * MotionApp.SCALE_FACTOR;
                var y = parseFloat(event.target.result.slice(5,10))
                    * MotionApp.HEIGHT * MotionApp.SCALE_FACTOR;
                direction.html(x + "," + y);
                map.panBy(x, y);
            };
        })(float_blob);
        reader.readAsBinaryString(float_blob);
    }

    // interval variable to send a constant stream to the server
    var timer;

    // establish websocket
    var ws = new WebSocket("ws://" + MotionApp.HOST + ":" +
                           MotionApp.PORT + "/websocket");
    ws.onopen = function() {
        console.log("Opened connection to websocket");
    };
    ws.onmessage = function(msg) {
        // display the updated frame
        var target = document.getElementById("target");
        url = window.webkitURL.createObjectURL(msg.data.slice(10, msg.data.size));
        target.onload = function() {
            window.webkitURL.revokeObjectURL(url);
        };
        target.src = url;

        // handle the direction of the motion in the frame
        get_direction(msg.data.slice(0,10));
    };
    ws.onclose = function(msg) {
        window.clearInterval(timer);
        console.log("Closed connection to websocket");
    };

    // request access to webcam
    navigator.webkitGetUserMedia(
        {video: true, audio: false},
        function(stream) {
            video.src = webkitURL.createObjectURL(stream);
            // send a constant stream to the server
            timer = setInterval(
                function () {
                    ctx.drawImage(video, 0, 0, MotionApp.WIDTH, MotionApp.HEIGHT);
                    var data = canvas.get()[0].toDataURL('image/jpeg', 1.0);
                    ws.send(data.split(',')[1]);
                }, 250);
        },
        function(err) {
            ws.close();
            console.log("Unable to get video stream!, Error: " + err)
        }
    );

    // close socket when the document closes
    $(document).unload(function() {
        ws.close();
    });

});
