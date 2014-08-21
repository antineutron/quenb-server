<!DOCTYPE html>
<html>
<head>

<link rel="stylesheet" type="text/css" href="../static/css/quenb.css">

<!-- jQuery support library -->
<script src="../static/js/jquery-1.9.1.min.js"></script>
<script src="../static/js/jquery-migrate-1.1.1.min.js"></script>

<!-- Include notification stuff (noty) -->
<script src="../static/js/noty/jquery.noty.js"></script>
<script src="../static/js/noty/layouts/all.js"></script>
<script src="../static/js/noty/themes/default.js"></script>

<!-- Main QuenB client library -->
<script src="../static/js/quenb.js"></script>

</head>
<body>
    <!-- Special item e.g. to display when things go wrong -->
    <img id="tvstatic" class="bg hidden special" src="../static/images/tvstatic.gif">

	<!-- As above, but we can use this to display an arbitrary image fullscreen -->
    <img id="imgfullscreen" class="bg hidden" src="../static/images/tvstatic.gif">

	<iframe id="contentpane"></iframe>
</body>
</html>
