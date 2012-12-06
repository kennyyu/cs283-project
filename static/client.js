$(document).ready(function(){

    // variables for the DOM elements
    var video = $("#live").get()[0];
    var canvas = $("#canvas");
    var ctx = canvas.get()[0].getContext('2d');

    // mirror the canvas
    ctx.translate(canvasSource.width, 0);
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
        console.log("Openened connection to websocket");
    }
    ws.onmessage = function(msg) {
        var target = document.getElementById("target");
        url = window.webkitURL.createObjectURL(msg.data);
        target.onload = function() {
            window.webkitURL.revokeObjectURL(url);
        };
        target.src = url;
    }

    // send a constant stream to the server
    timer = setInterval(
        function () {
            ctx.drawImage(video, 0, 0, 320, 240);
            var data = canvas.get()[0].toDataURL('image/jpeg', 1.0);
            ws.send(data.split(',')[1]);
        }, 250);

});
