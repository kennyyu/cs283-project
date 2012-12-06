$(document).ready(function(){

    function dataURItoBlob(dataURI) {
        /*
        var ab, bb, blob, byteString, i, ia, mimeString, _i, _len;
        if (dataURI.split(',')[0].indexOf('base64') >= 0) {
            byteString = atob(dataURI.split(',')[1]);
        } else {
            byteString = unescape(dataURI.split(',')[1]);
        }
        mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
        ab = new ArrayBuffer(byteString.length);
        ia = new Uint8Array(ab);
        for (_i = 0, _len = byteString.length; _i < _len; _i++) {
            i = byteString[_i];
            ia[_i] = byteString.charCodeAt(_i);
        }
        return new Blob([ia], {type: 'image/jpeg'}); */

        return dataURI.split(',')[1];
        /*
        var binary = atob(dataURI.split(',')[1]);
        var array = [];
        for(var i = 0; i < binary.length; i++) {
            array.push(binary.charCodeAt(i));
        }
        return new Blob([new Uint8Array(array)], {type: 'image/jpeg'}); */
        //return dataURI;
    }

    // variables for the DOM elements
    var video = $("#live").get()[0];
    var canvas = $("#canvas");
    var ctx = canvas.get()[0].getContext('2d');

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

    timer = setInterval(
        function () {
            ctx.drawImage(video, 0, 0, 320, 240);
            var data = canvas.get()[0].toDataURL('image/jpeg', 1.0);
            newblob = dataURItoBlob(data);
            ws.send(newblob);
        }, 250);

    /*
    var ws = new WebSocket("ws://localhost:8888/websocket");
    ws.onopen = function() {
        $("#test").append("<div>socket opened</div>");
    };
    ws.onmessage = function(event) {
        $("#test").append("<div>" + event.data + "</div>");
    };
    ws.onclose = function() {
        $("#test").append("<div>socket closed</div>");
    };

    $("#bar").click(function(eventObject) {
        ws.send("cheese");
    });
    */

    /*
    $("#bar").click(function(eventObject) {
        $.ajax({
            url: "/foo",
            success: function(data) {
                $("#test").append("<div>" + data + "</div>");
            },
            type: "GET",
        });
    });
    */
});