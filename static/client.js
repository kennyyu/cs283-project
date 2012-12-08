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

    // directions of overall motion
    var DIRECTIONS = {
        "NONE" : 0,
        "UP" : 1,
        "DOWN" : 2,
        "LEFT" : 3,
        "RIGHT" : 4,
    };

    function string_of_direction(direction) {
        switch(direction) {
        case DIRECTIONS["NONE"]:
            return "NONE";
        case DIRECTIONS["UP"]:
            return "UP";
        case DIRECTIONS["DOWN"]:
            return "DOWN";
        case DIRECTIONS["LEFT"]:
            return "LEFT";
        case DIRECTIONS["RIGHT"]:
            return "RIGHT";
        default:
            return "UNDEFINED";
        }
    }

    function move_in_direction(direction) {
        switch(direction) {
        case DIRECTIONS["NONE"]:
            return;
        case DIRECTIONS["UP"]:
            map.panBy(50, 0);
            break;
        case DIRECTIONS["DOWN"]:
            map.panBy(-50, 0);
            break;
        case DIRECTIONS["LEFT"]:
            map.panBy(0, -50);
            break;
        case DIRECTIONS["RIGHT"]:
            map.panBy(0, 50);
            break;
        default:
            return;
        }
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
        url = window.webkitURL.createObjectURL(msg.data.slice(1, msg.data.size));
        target.onload = function() {
            window.webkitURL.revokeObjectURL(url);
        };
        target.src = url;

        // handle the direction of the motion in the frame
        direction_blob = msg.data.slice(0,1);
        var reader = new FileReader();
        reader.onload = (function(blob) {
            return function(event) {
                var direction = parseInt(event.target.result);
                $("#direction").html(direction + "," + string_of_direction(direction));
                move_in_direction(direction);
            };
        })(direction_blob);
        reader.readAsBinaryString(direction_blob);
    }

    // send a constant stream to the server
    timer = setInterval(
        function () {
            ctx.drawImage(video, 0, 0, WIDTH, HEIGHT);
            var data = canvas.get()[0].toDataURL('image/jpeg', 1.0);
            ws.send(data.split(',')[1]);
        }, 250);

});
