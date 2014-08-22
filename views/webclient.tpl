<!DOCTYPE html>
<html>
<head>

<link rel="stylesheet" type="text/css" href="../static/css/quenb.css">

<!-- jQuery support library -->
<script src="../static/js/zepto.js"></script>

<!-- Main QuenB client library -->
<script src="../static/js/quenb.js"></script>

</head>
<body>

	<!-- Notification box -->
	<div id="notices"></div>

    <!-- Special item e.g. to display when things go wrong -->
    <img id="tvstatic" class="bg hidden special" src="../static/images/tvstatic.gif">

	<!-- As above, but we can use this to display an arbitrary image fullscreen -->
    <img id="imgfullscreen" class="bg hidden" src="../static/images/tvstatic.gif">

	<iframe id="contentpane"></iframe>
</body>
</html>
